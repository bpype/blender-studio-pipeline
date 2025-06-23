# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .transfer_function_util.drivers import transfer_drivers, cleanup_drivers
from .transfer_function_util.visibility import override_obj_visability
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    check_transfer_data_entry,
    activate_shapekey,
    disable_modifiers,
)
from ...naming import task_layer_prefix_name_get, task_layer_prefix_basename_get
from ...task_layer import get_transfer_data_owner
from .... import constants, logging

BIND_OPS = {
    'SURFACE_DEFORM': bpy.ops.object.surfacedeform_bind,
    'MESH_DEFORM': bpy.ops.object.meshdeform_bind,
    'CORRECTIVE_SMOOTH': bpy.ops.object.correctivesmooth_bind,
}


def modifiers_clean(obj):
    cleaned_names = transfer_data_clean(
        obj=obj, data_list=obj.modifiers, td_type_key=constants.MODIFIER_KEY
    )

    # Remove Drivers that match the cleaned item's name
    for name in cleaned_names:
        cleanup_drivers(obj, 'modifiers', name)


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
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def transfer_modifier(context, modifier_name, target_obj, source_obj):
    logger = logging.get_logger()

    # get modifier & index
    source_index = source_obj.modifiers.find(modifier_name)
    source_mod = source_obj.modifiers.get(modifier_name)

    # remove old and sync existing modifiers
    target_mod = target_obj.modifiers.get(modifier_name)
    if not target_mod:
        target_mod = target_obj.modifiers.new(source_mod.name, source_mod.type)
        target_obj.modifiers.move(len(target_obj.modifiers)-1, 0)

    if not source_mod:
        logger.debug(
            f"Modifer Transfer cancelled, '{modifier_name}' not found on '{source_obj.name}'"
        )
        target_obj.modifiers.remove(target_mod)
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        return

    # Order modifier based on previous modifier in source obj.
    if source_index > 0:
        name_anchor = task_layer_prefix_basename_get(source_obj.modifiers[source_index - 1].name)

        for target_mod_i, targ_mod in enumerate(target_obj.modifiers):
            if name_anchor == task_layer_prefix_basename_get(targ_mod.name):
                target_obj.modifiers.move(source_index, target_mod_i+1)
                break

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
        transfer_drivers(source_obj, target_obj, 'modifiers', modifier_name)

        bind_op = BIND_OPS.get(source_mod.type)
        if not bind_op or not target_mod.target:
            continue

        with activate_shapekey((target_obj, target_mod.target), "BIND-"+modifier_name):
            with disable_modifiers((target_obj, ), ('CORRECTIVE_SMOOTH', 'LATTICE', 'ARMATURE', 'SHRINKWRAP', 'SMOOTH')):
                for i in range(2):
                    context.view_layer.update()
                    with override_obj_visability(obj=target_obj, scene=context.scene):
                        with context.temp_override(object=target_obj, active_object=target_obj):
                            bind_op(modifier=target_mod.name)
