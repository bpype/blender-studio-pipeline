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
    """Transfer a single modifier from source_obj to target_obj.
    For example, when pulling into rigging and transferring a rigging modifier,
    then source_obj will be the local object, and target_obj will be the external object.

    ~Order
    Modifiers are ordered based on the name of the preceeding modifier on the local object.
    This is not very foolproof, since re-ordering multiple modifiers or renaming plus re-ordering, 
    or removing plus re-ordering, could all result in situations where determining the ideal order is difficult.
    In such cases, just fixing the order and needing to sync a second time is expected.

    ~Binding
    Binding data cannot be transferred. Instead, modifiers that require binding will have the bind operator executed.
    Sometimes binding is meant to be done in a bind pose other than the default. For this, shape keys can be added
    to either the deforming or the deformed mesh, named "BIND-<name_of_modifier_with_prefix>". Such shape keys will be enabled
    during binding. Deforming modifiers will be disabled during binding, except for the modifier being bound.
    """
    logger = logging.get_logger()

    # get modifier & index
    mod_idx_on_src = source_obj.modifiers.find(modifier_name)
    source_mod = source_obj.modifiers.get(modifier_name)

    # remove old and sync existing modifiers
    target_mod = target_obj.modifiers.get(modifier_name)
    if not target_mod:
        target_mod = target_obj.modifiers.new(source_mod.name, source_mod.type)
        target_obj.modifiers.move(len(target_obj.modifiers)-1, 0)
    mod_idx_on_tgt = target_obj.modifiers.find(modifier_name)

    if not source_mod:
        logger.debug(
            f"Modifer Transfer cancelled, '{modifier_name}' not found on '{source_obj.name}'"
        )
        target_obj.modifiers.remove(target_mod)
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        return

    tgt_idx = 0
    # Order modifier based on previous modifier in source obj.
    if mod_idx_on_src > 0:
        mod_anchor = source_obj.modifiers[mod_idx_on_src - 1]
        name_anchor = task_layer_prefix_basename_get(mod_anchor.name)
        logger.debug(f"  Anchor modifier: {name_anchor}")

        for idx, mod_of_tgt in enumerate(target_obj.modifiers):
            if name_anchor == task_layer_prefix_basename_get(mod_of_tgt.name):
                tgt_idx = min(len(target_obj.modifiers)-1, idx+1)
                break

    if mod_idx_on_tgt != tgt_idx:
        target_obj.modifiers.move(mod_idx_on_tgt, tgt_idx)
        logger.debug(f"  Moved {target_mod.name} to index {tgt_idx}.")

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
    for target_mod in target_obj.modifiers:
        transfer_drivers(source_obj, target_obj, 'modifiers', modifier_name)

        bind_op = BIND_OPS.get(target_mod.type)
        if (
            not bind_op or 
            (hasattr(target_mod, 'target') and not target_mod.target) or 
            (target_mod.type=='CORRECTIVE_SMOOTH' and target_mod.rest_source=='ORCO')
        ):
            continue

        objs = [target_obj]
        if hasattr(target_mod, 'target') and target_mod.target:
            objs.append(target_mod.target)
        with activate_shapekey(objs, "BIND-"+modifier_name):
            modifiers_to_disable = ['LATTICE', 'ARMATURE', 'SHRINKWRAP', 'SMOOTH']
            if target_mod.type != 'CORRECTIVE_SMOOTH':
                modifiers_to_disable.append('CORRECTIVE_SMOOTH')
            with disable_modifiers((target_obj, ), modifiers_to_disable):
                for i in range(2):
                    context.view_layer.update()
                    with override_obj_visability(obj=target_obj, scene=context.scene):
                        with context.temp_override(object=target_obj, active_object=target_obj):
                            bind_op(modifier=target_mod.name)
