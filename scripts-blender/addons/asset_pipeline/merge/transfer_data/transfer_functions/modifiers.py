# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

import bpy
from bpy.types import Context, Modifier, Object, Scene

from .... import config, constants, logging
from ....props import AssetTransferData, AssetTransferDataTemp
from ...naming import task_layer_prefix_name_get
from ...task_layer import get_transfer_data_owner
from ..transfer_util import (
    activate_shapekey,
    disable_modifiers,
    enable_modifiers,
    find_ownership_data,
    transfer_data_clean,
    transfer_data_item_is_missing,
)
from .transfer_function_util.drivers import cleanup_drivers, transfer_drivers
from .transfer_function_util.fractional_indexing import order_midpoint
from .transfer_function_util.visibility import override_obj_visibility

BIND_OPS = {
    'SURFACE_DEFORM': bpy.ops.object.surfacedeform_bind,
    'MESH_DEFORM': bpy.ops.object.meshdeform_bind,
    'CORRECTIVE_SMOOTH': bpy.ops.object.correctivesmooth_bind,
}


@dataclass
class ModifierOrderState:
    name: str
    transfer_data: AssetTransferData | AssetTransferDataTemp
    order_key: str | None
    is_local: bool


def modifiers_clean(obj: Object):
    cleaned_names = transfer_data_clean(obj=obj, data_list=obj.modifiers, td_type_key=constants.MODIFIER_KEY)

    # Remove Drivers that match the cleaned item's name
    for name in cleaned_names:
        cleanup_drivers(obj, 'modifiers', name)


def modifier_is_missing(transfer_data_item: AssetTransferData):
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.MODIFIER_KEY,
        data_list=transfer_data_item.id_data.modifiers,
    )


def init_modifiers(scene: Scene, obj: Object):
    _ensure_modifier_ownership(scene, obj)
    _fix_modifier_order_keys(scene, obj)


def _ensure_modifier_ownership(scene: Scene, obj: Object) -> None:
    """Register new (unowned) modifiers in temp transfer data, and rename all modifiers to include their task layer prefix."""
    asset_pipe = scene.asset_pipeline
    task_layer_owner, auto_surrender = get_transfer_data_owner(asset_pipe, constants.MODIFIER_KEY)
    for mod in obj.modifiers:
        ownership_data = find_ownership_data(obj.transfer_data_ownership, mod.name, constants.MODIFIER_KEY)
        if not ownership_data:
            ownership_data = asset_pipe.add_temp_transfer_data(
                name=mod.name,
                owner=task_layer_owner,
                type=constants.MODIFIER_KEY,
                obj_name=obj.name,
                surrender=auto_surrender,
            )
        mod.name = task_layer_prefix_name_get(mod.name, ownership_data.owner)
        ownership_data.name = mod.name


def _fix_modifier_order_keys(scene: Scene, obj: Object) -> None:
    """Reassign order_keys for any local modifiers that are out of position."""
    asset_pipe = scene.asset_pipeline
    local_task_layers = set(asset_pipe.get_local_task_layers())
    mods = list(obj.modifiers)

    temp_mod_data = {
        item.name: item
        for item in asset_pipe.temp_transfer_data
        if item.obj_name == obj.name and item.type == constants.MODIFIER_KEY
    }

    states: list[ModifierOrderState] = []
    for mod in mods:
        ownership = find_ownership_data(obj.transfer_data_ownership, mod.name, constants.MODIFIER_KEY)
        transfer_data = ownership or temp_mod_data.get(mod.name)
        order_key = transfer_data.order_key or None
        is_local = transfer_data.owner in local_task_layers
        states.append(ModifierOrderState(
            name=mod.name,
            transfer_data=transfer_data,
            order_key=order_key,
            is_local=is_local,
        ))

    def _needs_key(s: ModifierOrderState) -> bool:
        return s.is_local or s.order_key is None

    buckets = []
    i = 0
    while i < len(states):
        if not _needs_key(states[i]):
            i += 1
            continue
        start = i
        owner = _get_state_owner(states[i])
        while i < len(states) and _needs_key(states[i]) and _get_state_owner(states[i]) == owner:
            i += 1
        buckets.append((start, i))

    for bucket_start, bucket_end in buckets:
        _make_bucket_contiguous(states, bucket_start, bucket_end)


def _get_state_owner(state: ModifierOrderState) -> str:
    return state.transfer_data.owner


def _make_bucket_contiguous(
    states: list[ModifierOrderState],
    bucket_start: int,
    bucket_end: int,
) -> None:
    """Redistribute order_keys for a contiguous block of same-owner modifiers within their anchor bounds."""
    n = len(states)
    bucket_owner = _get_state_owner(states[bucket_start])

    def is_anchor(i: int) -> bool:
        return states[i].order_key is not None and _get_state_owner(states[i]) != bucket_owner

    anchor_prev = next(
        (states[i].order_key for i in range(bucket_start - 1, -1, -1) if is_anchor(i)),
        None,
    )
    anchor_nxt = next(
        (states[i].order_key for i in range(bucket_end, n) if is_anchor(i)),
        None,
    )

    if _bucket_is_contiguous([s.order_key for s in states[bucket_start:bucket_end]], anchor_prev, anchor_nxt):
        return

    lower = anchor_prev or ""
    for j in range(bucket_start, bucket_end):
        new_key = order_midpoint(lower, anchor_nxt)
        if j == bucket_start and anchor_prev is None and anchor_nxt is None:
            new_key += config.TASK_LAYER_TYPES.get(bucket_owner, bucket_owner).lower()
        states[j].order_key = new_key
        states[j].transfer_data.order_key = new_key
        lower = new_key


def _bucket_is_contiguous(keys: list[str | None], anchor_prev: str | None, anchor_nxt: str | None) -> bool:
    """Return True if all keys are non-None, strictly increasing, and within the anchor bounds."""
    prev = anchor_prev
    for key in keys:
        if key is None:
            return False
        if prev is not None and key <= prev:
            return False
        if anchor_nxt is not None and key >= anchor_nxt:
            return False
        prev = key
    return True



def transfer_modifier(
        context: Context,
        modifier_name: str,
        target_obj: Object,
        source_obj: Object,
    ):
    """Transfer a single modifier from source_obj to target_obj.
    For example, when pulling into rigging and transferring a rigging modifier,
    then source_obj will be the local object, and target_obj will be the external object.
    """
    logger = logging.get_logger()

    source_mod = source_obj.modifiers.get(modifier_name)
    target_mod = target_obj.modifiers.get(modifier_name)

    if not source_mod:
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        logger.debug(f"Modifier Transfer cancelled, '{modifier_name}' not found on '{source_obj.name}'")
        if target_mod:
            target_obj.modifiers.remove(target_mod)
        return

    if not target_mod:
        target_mod = target_obj.modifiers.new(source_mod.name, source_mod.type)

    transfer_modifier_props(context, source_mod, target_mod)
    transfer_drivers(source_obj, target_obj, 'modifiers', modifier_name)
    if is_modifier_bound(source_mod):
        bind_modifier(context, target_obj, modifier_name)


def sort_modifiers_by_order(obj: Object):
    """Sort all modifiers on obj by their stored order_key values.
    Must be called after all transfer_data_ownership entries are populated,
    so that orders from all task layers are available simultaneously.
    """
    td_type_key = constants.MODIFIER_KEY

    def get_order_key(mod_name: str) -> str:
        td = find_ownership_data(obj.transfer_data_ownership, mod_name, td_type_key)
        # "~" sorts after all lowercase letters, so modifiers without an order_key end up last.
        return td.order_key if (td and td.order_key) else "~"

    def is_out_of_order(pos: int) -> bool:
        return get_order_key(obj.modifiers[pos - 1].name) > get_order_key(obj.modifiers[pos].name)

    # Sort modifiers by order_key: step through each modifier and shift it left
    # until it is no longer out of order with its predecessor.
    for i in range(1, len(obj.modifiers)):
        pos = i
        while pos > 0 and is_out_of_order(pos):
            obj.modifiers.move(pos, pos - 1)
            pos -= 1


def transfer_modifier_props(context: Context, source_mod: Modifier, target_mod: Modifier):
    props = [p.identifier for p in source_mod.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(source_mod, prop)
        setattr(target_mod, prop, value)

    if source_mod.type == 'NODES':
        # NOTE: This matches inputs by their internal name, not their display name.
        # That means you can rename sockets, but removing and adding new ones might cause trouble.

        # Transfer geo node attributes
        if bpy.app.version >= (5,2,0):
            props = source_mod.properties
            if not props:
                # This happens when GeoNode modifier has no node group at all.
                # Could arguably raise an error, since such a modifier is useless.
                return
            target_props = target_mod.properties
            for socket_name in props.inputs.keys():
                source_socket = getattr(props.inputs, socket_name, None)
                target_socket = getattr(target_props.inputs, socket_name, None)
                if source_socket and target_socket and hasattr(source_socket, "value"):
                    target_socket.value = source_socket.value
        else:
            for key, value in source_mod.items():
                typ = type(getattr(target_mod, f'["{key}"]'))
                if typ in (int, float, bool, str):
                    if not (typ is str and type(target_mod[key]) is int):  # skip conversion for enum props
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


def bind_modifier(context: Context, obj: Object, modifier_name: str):
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

    def is_target_missing(modifier) -> bool:
        if modifier.type == 'CORRECTIVE_SMOOTH':
            return False
        if hasattr(modifier, 'object'):
            return not bool(modifier.object)
        elif hasattr(modifier, 'target'):
            return not bool(modifier.target)
        else:
            return False

    if (
        not bind_op
        or is_target_missing(modifier)
        or (modifier.type == 'CORRECTIVE_SMOOTH' and modifier.rest_source == 'ORCO')
    ):
        return

    objs = [obj]
    if hasattr(modifier, 'target') and modifier.target:
        objs.append(modifier.target)
    with activate_shapekey(objs, "BIND-" + modifier_name):
        modifiers_to_disable = ['LATTICE', 'ARMATURE', 'SHRINKWRAP', 'SMOOTH']
        if modifier.type != 'CORRECTIVE_SMOOTH':
            modifiers_to_disable.append('CORRECTIVE_SMOOTH')
        with disable_modifiers(objs, modifiers_to_disable):
            with override_obj_visibility(obj=obj, scene=context.scene):
                with enable_modifiers(obj, [modifier]):
                    with context.temp_override(object=obj, active_object=obj):
                        for _ in range(2):
                            context.view_layer.update()
                            bind_op(modifier=modifier.name)
                            word = "Bound" if is_modifier_bound(modifier) else "Un-bound"
                            logger.debug(f"{word} {modifier_name} on {obj.name}")
                            if is_modifier_bound(modifier):
                                return


def is_modifier_bound(modifier: Modifier) -> bool | None:
    if modifier.type == 'CORRECTIVE_SMOOTH':
        return modifier.rest_source == 'BIND' and modifier.is_bind
    elif hasattr(modifier, 'is_bound'):
        return modifier.is_bound
