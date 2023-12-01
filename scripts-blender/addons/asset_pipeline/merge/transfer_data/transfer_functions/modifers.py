import bpy
from .transfer_function_util.drivers import find_drivers, copy_driver
from .transfer_function_util.visibility import override_obj_visability
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    check_transfer_data_entry,
)
from ...naming import task_layer_prefix_name_get
from ...task_layer import get_transfer_data_owner
from .... import constants


def modifiers_clean(obj):
    transfer_data_clean(
        obj=obj, data_list=obj.modifiers, td_type_key=constants.MODIFIER_KEY
    )


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

    # transfer new modifiers
    for i, mod in enumerate(source_obj.modifiers):
        if mod.name == modifier_name:
            mod_new = target_obj.modifiers.new(mod.name, mod.type)
            # sort new modifier at correct index (default to beginning of the stack)
            idx = 0
            if i > 0:
                name_prev = source_obj.modifiers[i - 1].name
                for target_mod_i, target_mod in enumerate(target_obj.modifiers):
                    if target_mod.name == name_prev:
                        idx = target_mod_i + 1
            with override_obj_visability(obj=target_obj, scene=scene):
                with context.temp_override(object=target_obj):
                    bpy.ops.object.modifier_move_to_index(
                        modifier=mod_new.name, index=idx
                    )
            mod_target = target_obj.modifiers.get(mod.name)
            props = [p.identifier for p in mod.bl_rna.properties if not p.is_readonly]
            for prop in props:
                value = getattr(mod, prop)
                setattr(mod_target, prop, value)

            if mod.type != 'NODES':
                return

            # Transfer geo node attributes
            for key, value in mod.items():
                mod_target[key] = value

    # rebind modifiers (corr. smooth, surf. deform, mesh deform)
    for mod in target_obj.modifiers:
        if mod.type == 'SURFACE_DEFORM':
            if not mod.is_bound:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(
                        object=target_obj, active_object=target_obj
                    ):
                        bpy.ops.object.surfacedeform_bind(modifier=mod.name)
        elif mod.type == 'MESH_DEFORM':
            if not mod.is_bound:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(
                        object=target_obj, active_object=target_obj
                    ):
                        bpy.ops.object.meshdeform_bind(modifier=mod.name)
        elif mod.type == 'CORRECTIVE_SMOOTH':
            if not mod.is_bind:
                continue
            for i in range(2):
                with override_obj_visability(obj=target_obj, scene=scene):
                    with context.temp_override(
                        object=target_obj, active_object=target_obj
                    ):
                        bpy.ops.object.correctivesmooth_bind(modifier=mod.name)
        fcurves = find_drivers(source_obj, 'modifiers', modifier_name)
        for fcurve in fcurves:
            copy_driver(from_fcurve=fcurve, target=target_obj)
