# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .transfer_function_util.drivers import transfer_drivers, cleanup_drivers
from .transfer_function_util.visibility import override_obj_visibility
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    find_ownership_data,
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
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        ownership_data = find_ownership_data(transfer_data, mod.name, td_type_key)
        if not ownership_data:
            ownership_data = asset_pipe.add_temp_transfer_data(
                name=mod.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )

        mod.name = task_layer_prefix_name_get(mod.name, ownership_data.owner)


def transfer_modifier(context, modifier_name, target_obj, source_obj):
    """Transfer a single modifier from source_obj to target_obj.
    For example, when pulling into rigging and transferring a rigging modifier,
    then source_obj will be the local object, and target_obj will be the external object.
    """
    logger = logging.get_logger()

    source_mod = source_obj.modifiers.get(modifier_name)
    target_mod = target_obj.modifiers.get(modifier_name)

    if not source_mod:
        logger.debug(
            f"Modifer Transfer cancelled, '{modifier_name}' not found on '{source_obj.name}'"
        )
        target_obj.modifiers.remove(target_mod)
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        return

    # remove old and sync existing modifiers
    if not target_mod:
        target_mod = target_obj.modifiers.new(source_mod.name, source_mod.type)

    place_modifier_in_stack(source_obj, target_obj, modifier_name)
    transfer_modifier_props(context, source_mod, target_mod)
    transfer_drivers(source_obj, target_obj, 'modifiers', modifier_name)
    if is_modifier_bound(source_mod):
        bind_modifier(context, target_obj, modifier_name)

def place_modifier_in_stack(source_obj, target_obj, modifier_name):
    """Modifiers will try to be placed below the modifier they were below on the source object.
    This is not very foolproof, since re-ordering multiple modifiers or renaming plus re-ordering, 
    or removing plus re-ordering, all in one step, could make it hard to determine the ideal order.
    In such cases, user may need to fix the order and sync a 2nd time.
    """

    logger = logging.get_logger()
    idx_tgt = target_obj.modifiers.find(modifier_name)
    idx_src = source_obj.modifiers.find(modifier_name)

    idx_new = 0
    name_anchor = ""
    # Order modifier based on previous modifier in source obj.
    if idx_src > 0:
        mod_anchor = source_obj.modifiers[idx_src - 1]
        name_anchor = task_layer_prefix_basename_get(mod_anchor.name)

        for idx, mod_of_tgt in enumerate(target_obj.modifiers):
            if name_anchor == task_layer_prefix_basename_get(mod_of_tgt.name):
                idx_new = min(len(target_obj.modifiers)-1, idx+1)
                break

    if idx_tgt != idx_new:
        target_obj.modifiers.move(idx_tgt, idx_new)
        msg = f"  Moved {modifier_name} to index {idx_new}"
        if name_anchor:
            msg +=  f"(after {name_anchor})"
        logger.debug(msg)


def transfer_modifier_props(context, source_mod, target_mod):
    props = [p.identifier for p in source_mod.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(source_mod, prop)
        setattr(target_mod, prop, value)

    if source_mod.type == 'NODES':
        # NOTE: This matches inputs by their internal name, not their display name.
        # That means you can rename sockets, but removing and adding new ones might cause trouble.

        # Transfer geo node attributes
        for key, value in source_mod.items():
            typ = type(getattr(target_mod, f'["{key}"]'))
            if typ in (int, float, bool, str):
                value = typ(value)
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


def bind_modifier(context, obj, modifier_name):
    """Binding data cannot be transferred. Instead, modifiers that require binding will have the bind operator executed.

    Sometimes binding is meant to be done in a bind pose other than the default. For this, shape keys can be added
    to the deforming and/or the deformed mesh, named "BIND-<name_of_modifier_with_prefix>". Such shape keys will be enabled
    during binding. Other deforming modifiers will be disabled during binding.
    """

    # NOTE: This could be optimized by not re-binding unnecessarily, but Blender doesn't allow checking
    # if the binding is broken or not. https://projects.blender.org/blender/blender/issues/140550
    # Another way to get around this is to let the rigging task layer own the object base.

    logger = logging.get_logger()
    modifier = obj.modifiers.get(modifier_name)
    assert modifier
    bind_op = BIND_OPS.get(modifier.type)
    if (
        not bind_op or 
        (hasattr(modifier, 'target') and not modifier.target) or 
        not modifier.show_viewport or 
        (modifier.type=='CORRECTIVE_SMOOTH' and modifier.rest_source=='ORCO')
    ):
        return

    objs = [obj]
    if hasattr(modifier, 'target') and modifier.target:
        objs.append(modifier.target)
    with activate_shapekey(objs, "BIND-"+modifier_name):
        modifiers_to_disable = ['LATTICE', 'ARMATURE', 'SHRINKWRAP', 'SMOOTH']
        if modifier.type != 'CORRECTIVE_SMOOTH':
            modifiers_to_disable.append('CORRECTIVE_SMOOTH')
        with disable_modifiers(objs, modifiers_to_disable):
            for i in range(2):
                context.view_layer.update()
                with override_obj_visibility(obj=obj, scene=context.scene):
                    with context.temp_override(object=obj, active_object=obj):
                        bind_op(modifier=modifier.name)
                        word = "Bound" if is_modifier_bound(modifier) else "Un-bound"
                        logger.debug(f"{word} {modifier_name} on {obj.name}")
                        if is_modifier_bound(modifier):
                            return


def is_modifier_bound(modifier) -> bool | None:
    if modifier.type == 'CORRECTIVE_SMOOTH':
        return modifier.is_bind
    elif hasattr(modifier, 'is_bound'):
        return modifier.is_bound