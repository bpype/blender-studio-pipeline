import bpy
from .transfer_function_util.drivers import transfer_drivers
from .transfer_function_util.visibility import override_obj_visability
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    check_transfer_data_entry,
)
from ...naming import task_layer_prefix_name_get, task_layer_prefix_basename_get
from ...task_layer import get_transfer_data_owner
from .... import constants


def modifiers_clean(obj):
    transfer_data_clean(obj=obj, data_list=obj.modifiers, td_type_key=constants.MODIFIER_KEY)


def modifier_is_missing(transfer_data_item):
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.MODIFIER_KEY,
        data_list=transfer_data_item.id_data.modifiers,
    )


def init_modifiers(scene, obj):
    asset_pipe = scene.asset_pipeline
    td_type_key = constants.MODIFIER_KEY
    transfer_data = obj.transfer_data_ownership
    task_layer_owner, auto_surrender = get_transfer_data_owner(
        asset_pipe,
        td_type_key,
    )

    for mod in obj.modifiers:
        mod.name = task_layer_prefix_name_get(mod.name, task_layer_owner)
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        matches = check_transfer_data_entry(transfer_data, mod.name, td_type_key)
        if len(matches) == 0:
            asset_pipe.add_temp_transfer_data(
                name=mod.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj=obj,
                surrender=auto_surrender,
            )


def transfer_modifier(modifier_name, target_obj, source_obj):
    # remove old and sync existing modifiers
    context = bpy.context
    scene = context.scene
    old_mod = target_obj.modifiers.get(modifier_name)
    if old_mod:
        target_obj.modifiers.remove(old_mod)

    # get modifier index
    source_index = 0
    for i, source_mod in enumerate(source_obj.modifiers):
        if source_mod.name == modifier_name:
            source_index = i
            break

    # create target mod
    mod_new = target_obj.modifiers.new(source_mod.name, source_mod.type)

    # move new modifier at correct index (default to beginning of the stack)
    idx = 0
    if source_index > 0:
        name_prev = source_obj.modifiers[i - 1].name
        for target_mod_i, target_mod in enumerate(target_obj.modifiers):
            if task_layer_prefix_basename_get(target_mod.name) == task_layer_prefix_basename_get(
                name_prev
            ):
                idx = target_mod_i + 1

    with override_obj_visability(obj=target_obj, scene=scene):
        with context.temp_override(object=target_obj):
            bpy.ops.object.modifier_move_to_index(modifier=mod_new.name, index=idx)

    target_mod = target_obj.modifiers.get(source_mod.name)
    props = [p.identifier for p in source_mod.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(source_mod, prop)
        setattr(target_mod, prop, value)

    if source_mod.type == 'NODES':
        # Transfer geo node attributes
        for key, value in source_mod.items():
            target_mod[key] = value

        # Transfer geo node bake settings
        target_mod.bake_directory = source_mod.bake_directory
        for index, target_bake in enumerate(target_mod.bakes):
            source_bake = source_mod.bakes[index]
            props = [p.identifier for p in source_bake.bl_rna.properties if not p.is_readonly]
            for prop in props:
                value = getattr(source_bake, prop)
                setattr(target_bake, prop, value)
        
        # refresh node modifier UI
        if target_mod.node_group:
            target_mod.node_group.interface_update(context)

    # rebind modifiers (corr. smooth, surf. deform, mesh deform)
    for source_mod in target_obj.modifiers:
        if source_mod.type == 'SURFACE_DEFORM':
            if not source_mod.is_bound:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(object=target_obj, active_object=target_obj):
                        bpy.ops.object.surfacedeform_bind(modifier=source_mod.name)
        elif source_mod.type == 'MESH_DEFORM':
            if not source_mod.is_bound:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(object=target_obj, active_object=target_obj):
                        bpy.ops.object.meshdeform_bind(modifier=source_mod.name)
        elif source_mod.type == 'CORRECTIVE_SMOOTH':
            if not source_mod.is_bind:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(object=target_obj, active_object=target_obj):
                        bpy.ops.object.correctivesmooth_bind(modifier=source_mod.name)

        transfer_drivers(source_obj, target_obj, 'modifiers', modifier_name)
