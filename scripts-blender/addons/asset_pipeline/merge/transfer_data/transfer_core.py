# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time
from .transfer_functions import (
    attributes,
    constraints,
    custom_props,
    modifers,
    parent,
    shape_keys,
    vertex_groups,
    materials,
)
from typing import List
from ... import constants, logging
from .transfer_util import (
    transfer_data_add_entry,
    check_transfer_data_entry,
    link_objs_to_collection,
    isolate_collection,
)


# TODO use logging module here
def copy_transfer_data_ownership(
    td_type_key: str, target_obj: bpy.types.Object, transfer_data_dict: dict
) -> None:
    """Copy Transferable Data item to object if non entry exists

    Args:
        transfer_data_item: Item of bpy.types.CollectionProperty from source object
        target_obj (bpy.types.Object): Object to add Transferable Data item to
    """
    transfer_data = target_obj.transfer_data_ownership
    matches = check_transfer_data_entry(
        transfer_data,
        transfer_data_dict["name"],
        td_type_key,
    )
    if len(matches) == 0:
        transfer_data_add_entry(
            transfer_data,
            transfer_data_dict["name"],
            td_type_key,
            transfer_data_dict["owner"],
            transfer_data_dict["surrender"],
        )


def transfer_data_clean(obj):
    vertex_groups.vertex_groups_clean(obj)
    modifers.modifiers_clean(obj)
    constraints.constraints_clean(obj)
    custom_props.custom_prop_clean(obj)
    shape_keys.shape_keys_clean(obj)
    attributes.attribute_clean(obj)
    parent.parent_clean(obj)


def transfer_data_is_missing(transfer_data_item) -> bool:
    """Check if Transferable Data item is missing

    Args:
        transfer_data_item: Item of class ASSET_TRANSFER_DATA

    Returns:
        bool: bool if item is missing
    """
    return bool(
        vertex_groups.vertex_group_is_missing(transfer_data_item)
        or modifers.modifier_is_missing(transfer_data_item)
        or constraints.constraint_is_missing(transfer_data_item)
        or custom_props.custom_prop_is_missing(transfer_data_item)
        or shape_keys.shape_key_is_missing(transfer_data_item)
        or attributes.attribute_is_missing(transfer_data_item)
    )


def init_transfer_data(
    scene: bpy.types.Scene,
    obj: bpy.types.Object,
):
    """Collect Transferable Data Items on a given object

    Args:
        obj (bpy.types.Object): Target object for Transferable Data
        task_layer_name (str): Name of task layer
        temp_transfer_data: Item of class ASSET_TRANSFER_DATA_TEMP
    """
    if obj.library:
        # Don't create ownership data for object data if the object is linked.
        return

    constraints.init_constraints(scene, obj)
    custom_props.init_custom_prop(scene, obj)
    parent.init_parent(scene, obj)
    modifers.init_modifiers(scene, obj)

    if not obj.data or obj.data.library:
        # Don't create ownership data for mesh data if the mesh is linked, or Empties.
        return

    vertex_groups.init_vertex_groups(scene, obj)
    materials.init_materials(scene, obj)
    shape_keys.init_shape_keys(scene, obj)
    attributes.init_attributes(scene, obj)


def apply_transfer_data_items(
    context,
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    td_type_key: str,
    transfer_data_dicts: List[dict],
):
    logger = logging.get_logger()
    # Get source/target from first item in list, because all items in list are same object/type
    if target_obj is None:
        logger.warning(f"Failed to Transfer {td_type_key.title()} from {source_obj.name}")
        return

    for transfer_data_dict in transfer_data_dicts:
        copy_transfer_data_ownership(td_type_key, target_obj, transfer_data_dict)

    # if TD Source is Target, restore the ownership data but don't transfer anything
    if source_obj == target_obj:
        return

    if td_type_key == constants.VERTEX_GROUP_KEY:
        # Transfer All Vertex Groups in one go
        logger.debug(f"Transferring All Vertex Groups from {source_obj.name} to {target_obj.name}.")
        vertex_groups.transfer_vertex_groups(
            vertex_group_names=[item["name"] for item in transfer_data_dicts],
            target_obj=target_obj,
            source_obj=source_obj,
        )
    if td_type_key == constants.MODIFIER_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(
                f"Transferring Modifier {transfer_data_dict['name']} from {source_obj.name} to {target_obj.name}."
            )
            modifers.transfer_modifier(
                context,
                modifier_name=transfer_data_dict["name"],
                target_obj=target_obj,
                source_obj=source_obj,
            )
    if td_type_key == constants.CONSTRAINT_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(
                f"Transferring Constraint {transfer_data_dict['name']} from {source_obj.name} to {target_obj.name}."
            )
            constraints.transfer_constraint(
                constraint_name=transfer_data_dict["name"],
                target_obj=target_obj,
                source_obj=source_obj,
            )
    if td_type_key == constants.CUSTOM_PROP_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(
                f"Transferring Custom Property {transfer_data_dict['name']} from {source_obj.name} to {target_obj.name}."
            )
            custom_props.transfer_custom_prop(
                prop_name=transfer_data_dict["name"],
                target_obj=target_obj,
                source_obj=source_obj,
            )
    if td_type_key == constants.MATERIAL_SLOT_KEY:
        logger.debug(f"Transferring Materials from {source_obj.name} to {target_obj.name}.")
        for transfer_data_dict in transfer_data_dicts:
            materials.transfer_materials(
                target_obj=target_obj,
                source_obj=source_obj,
            )
    if td_type_key == constants.SHAPE_KEY_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(
                f"Transferring Shape Key {transfer_data_dict['name']} from {source_obj.name} to {target_obj.name}."
            )
            shape_keys.transfer_shape_key(
                context=context,
                target_obj=target_obj,
                source_obj=source_obj,
                shape_key_name=transfer_data_dict["name"],
            )
    if td_type_key == constants.ATTRIBUTE_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(
                f"Transferring Attribute {transfer_data_dict['name']} from {source_obj.name} to {target_obj.name}."
            )
            attributes.transfer_attribute(
                target_obj=target_obj,
                source_obj=source_obj,
                attribute_name=transfer_data_dict["name"],
            )
    if td_type_key == constants.PARENT_KEY:
        for transfer_data_dict in transfer_data_dicts:
            logger.debug(		
                    f"Transferring Parent Relationship from {source_obj.name} to {target_obj.name}."		
                )
            parent.transfer_parent(
                target_obj=target_obj,
                source_obj=source_obj,
            )


def apply_transfer_data(context: bpy.types.Context, transfer_data_map) -> None:
    """Apply all Transferable Data from Transferable Data map onto objects.
    Copies any Transferable Data owned by local layer onto objects owned by external layers.
    Applies Transferable Data from external layers onto objects owned by local layers

    Transfer_data_map is generated by class 'AssetTransferMapping'

    Args:
        context (bpy.types.Context): context of .blend file
        transfer_data_map: Map generated by class AssetTransferMapping
    """
    # Create/isolate tmp collection to reduce depsgraph update time
    profiler = logging.get_profiler()
    td_col = bpy.data.collections.new("ISO_COL_TEMP")
    with isolate_collection(context, td_col):
        # Loop over objects in Transfer data map
        for source_obj in transfer_data_map:
            target_obj = transfer_data_map[source_obj]["target_obj"]
            td_types = transfer_data_map[source_obj]["td_types"]
            with link_objs_to_collection(set([target_obj, source_obj]), td_col):
                for td_type_key, td_dicts in td_types.items():
                    start_time = time.time()
                    apply_transfer_data_items(
                        context, source_obj, target_obj, td_type_key, td_dicts
                    )
                    profiler.add(time.time() - start_time, td_type_key)
    bpy.data.collections.remove(td_col)
