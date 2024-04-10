import bpy
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    check_transfer_data_entry,
)
from ...naming import task_layer_prefix_name_get, task_layer_prefix_basename_get
from .transfer_function_util.drivers import transfer_drivers, cleanup_drivers
from .transfer_function_util.visibility import override_obj_visability
from ...task_layer import get_transfer_data_owner
from .... import constants, logging


def constraints_clean(obj):
    cleaned_names = transfer_data_clean(
        obj=obj, data_list=obj.constraints, td_type_key=constants.CONSTRAINT_KEY
    )

    # Remove Drivers that match the cleaned item's name
    for name in cleaned_names:
        cleanup_drivers(obj, 'constraints', name)

def constraint_is_missing(transfer_data_item):
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.CONSTRAINT_KEY,
        data_list=transfer_data_item.id_data.constraints,
    )


def init_constraints(scene, obj):
    td_type_key = constants.CONSTRAINT_KEY
    transfer_data = obj.transfer_data_ownership
    asset_pipe = scene.asset_pipeline
    task_layer_owner, auto_surrender = get_transfer_data_owner(
        asset_pipe,
        td_type_key,
    )
    for const in obj.constraints:
        const.name = task_layer_prefix_name_get(const.name, task_layer_owner)
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        matches = check_transfer_data_entry(transfer_data, const.name, td_type_key)
        if len(matches) == 0:
            asset_pipe.add_temp_transfer_data(
                name=const.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def transfer_constraint(constraint_name, target_obj, source_obj):
    logger = logging.get_logger()
    context = bpy.context
    # remove old and sync existing modifiers
    old_mod = target_obj.constraints.get(constraint_name)
    if old_mod:
        target_obj.constraints.remove(old_mod)

    source_index = 0
    source_constraint = None
    # transfer new modifiers
    for source_index, source_constraint in enumerate(source_obj.constraints):
        if source_constraint.name == constraint_name:
            source_index = source_index
            break

    if not source_constraint:
        logger.debug(
            f"Constraint Transfer cancelled, '{constraint_name}' not found on '{source_obj.name}'"
        )
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        return

    constraint_new = target_obj.constraints.new(source_constraint.type)
    constraint_new.name = source_constraint.name
    # sort new modifier at correct index (default to beginning of the stack)
    idx = 0
    if source_index > 0:
        name_prev = source_obj.constraints[source_index - 1].name
        for target_mod_i, target_constraint in enumerate(target_obj.constraints):
            if task_layer_prefix_basename_get(
                target_constraint.name
            ) == task_layer_prefix_basename_get(name_prev):
                idx = target_mod_i + 1

    with override_obj_visability(obj=target_obj, scene=context.scene):
        with context.temp_override(object=target_obj):
            bpy.ops.constraint.move_to_index(constraint=constraint_new.name, index=idx)

    constraint_target = target_obj.constraints.get(source_constraint.name)
    props = [p.identifier for p in source_constraint.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(source_constraint, prop)
        setattr(constraint_target, prop, value)

    # HACK to cover edge case of armature constraints
    if source_constraint.type == "ARMATURE":
        for target_item in source_constraint.targets:
            new_target = constraint_new.targets.new()
            new_target.target = target_item.target
            new_target.subtarget = target_item.subtarget

    transfer_drivers(source_obj, target_obj, 'constraints', constraint_name)
