import bpy
from ..merge.naming import task_layer_prefix_transfer_data_update
from .asset_mapping import AssetTransferMapping
from .transfer_data.transfer_core import (
    init_transfer_data,
    transfer_data_is_missing,
    apply_transfer_data,
    transfer_data_clean,
)
from .transfer_data.transfer_util import transfer_data_add_entry

from .naming import (
    merge_add_suffix_to_hierarchy,
    merge_remove_suffix_from_hierarchy,
    get_id_type_name,
)
from .transfer_data.transfer_functions.transfer_function_util.active_indexes import (
    transfer_active_uv_layer_index,
    transfer_active_color_attribute_index,
)
from pathlib import Path
from typing import Dict
from .. import constants, logging
import time


def ownership_transfer_data_cleanup(
    asset_pipe: 'bpy.types.AssetPipeline',
    obj: bpy.types.Object,
) -> None:
    """Remove Transferable Data ownership items if the corresponding data is missing

    Args:
        obj (bpy.types.Object): Object that contains the Transferable Data
    """
    local_task_layer_keys = asset_pipe.get_local_task_layers()
    transfer_data = obj.transfer_data_ownership
    to_remove = []
    for transfer_data_item in transfer_data:
        if transfer_data_item.owner in local_task_layer_keys:
            if transfer_data_is_missing(transfer_data_item):
                to_remove.append(transfer_data_item.name)

    for name in to_remove:
        transfer_data.remove(transfer_data.keys().index(name))


def ownership_get(
    local_col: bpy.types.Collection,
    scene: bpy.types.Scene,
) -> None:
    """Find new Transferable Data owned by the local task layer.
    Marks items as owned by the local task layer if they are in the
    corresponding task layer collection and have no owner.

    Args:
        local_col (bpy.types.Collection): The top level asset collection that is local to the file
        task_layer_name (str): Name of the current task layer that will be the owner of the data
        temp_transfer_data (bpy.types.CollectionProperty): Collection property containing newly found
        data and the object that contains this data.

    Returns:
        list[bpy.types.Object]: Returns a list of objects that have no owner and will not be included
        in the merge process
    """
    asset_pipe = scene.asset_pipeline
    asset_pipe.temp_transfer_data.clear()

    default_task_layer = asset_pipe.get_local_task_layers()[0]

    for col in asset_pipe.asset_collection.children:
        if col.asset_id_owner == "NONE":
            col.asset_id_owner = default_task_layer

    task_layer_objs = get_task_layer_objects(asset_pipe)

    for obj in local_col.all_objects:
        # TODO REPLACE This is expensive to loop over everything again
        for transfer_data_item in obj.transfer_data_ownership:
            task_layer_prefix_transfer_data_update(transfer_data_item)

        # Mark Asset ID Owner for objects in the current task layers collection
        if obj.asset_id_owner == "NONE" and obj in task_layer_objs:
            obj.asset_id_owner = default_task_layer
            # obj.name = asset_prefix_name_get(obj.name)
        # Skip items that have no owner
        if obj.asset_id_owner == "NONE":
            continue
        ownership_transfer_data_cleanup(asset_pipe, obj)
        init_transfer_data(scene, obj)


def ownership_set(temp_transfer_data: bpy.types.CollectionProperty) -> None:
    """Add new Transferable Data items on each object found in the
    temp Transferable Data collection property

    Args:
        temp_transfer_data (bpy.types.CollectionProperty): Collection property containing newly found
        data and the object that contains this data.
    """
    for transfer_data_item in temp_transfer_data:
        obj = bpy.data.objects.get(transfer_data_item.obj_name)
        transfer_data = obj.transfer_data_ownership
        transfer_data_add_entry(
            transfer_data,
            transfer_data_item.name,
            transfer_data_item.type,
            transfer_data_item.owner,
            transfer_data_item.surrender,
        )


def get_invalid_objects(
    asset_pipe: 'bpy.types.AssetPipeline',
    local_col: bpy.types.Collection,
) -> list[bpy.types.Object]:
    """Returns a list of objects not used in the merge processing,
    which are considered invalid. The objects will be excluded from
    the merge process.

    Args:
        local_col (bpy.types.Collection): The top level asset collection that is local to the file
        scene (bpy.types.Scene): Scene that contains a the file's asset

    Returns:
        list[bpy.types.Object]: List of Invalid Objects
    """
    local_task_layer_keys = asset_pipe.get_local_task_layers()
    task_layer_objs = get_task_layer_objects(asset_pipe)

    invalid_obj = []
    for obj in local_col.all_objects:
        if obj.library:
            # Linked objects don't have or need ownership data, so they don't count
            # as invalid.
            continue
        if obj.asset_id_owner == "NONE":
            invalid_obj.append(obj)
        if obj not in task_layer_objs and obj.asset_id_owner in local_task_layer_keys:
            invalid_obj.append(obj)
    return invalid_obj


def remap_user(source_datablock: bpy.types.ID, target_datablock: bpy.types.ID) -> None:
    """Remap datablock and append name to datablock that has been remapped

    Args:
        source_datablock (bpy.types.ID): datablock that will be replaced by the target
        target_datablock (bpy.types.ID): datablock that will replace the source
    """
    logger = logging.get_logger()
    logger.debug(
        f"Remapping {source_datablock.rna_type.name}: {source_datablock.name} to {target_datablock.name}"
    )
    source_datablock.user_remap(target_datablock)
    source_datablock.name += "_Users_Remapped"


def merge_task_layer(
    context: bpy.types.Context,
    local_tls: list[str],
    external_file: Path,
) -> None:
    """Combines data from an external task layer collection in the local
    task layer collection. By finding the owner of each collection,
    object and Transferable Data item and keeping each layer of data via a copy
    from its respective owners.

    This ensures that objects owned by an external task layer will always be kept
    linked into the scene, and any local Transferable Data like a modifier will be applied
    ontop of that external object of vice versa. Ownership is stored in an objects properties,
    and map is created to match each object to its respective owner.

    Args:
        context: (bpy.types.Context): context of current .blend
        local_tls: (list[str]): list of task layers that are local to the current file
        external_file (Path): external file to pull data into the current file from
    """

    logger = logging.get_logger()
    profiles = logging.get_profiler()

    start_time = time.time()
    local_col = context.scene.asset_pipeline.asset_collection
    if not local_col:
        return "Unable to find Asset Collection"
    col_base_name = local_col.name
    local_suffix = constants.LOCAL_SUFFIX
    external_suffix = constants.EXTERNAL_SUFFIX
    merge_add_suffix_to_hierarchy(local_col, local_suffix)

    appended_col = import_data_from_lib(external_file, "collections", col_base_name)
    merge_add_suffix_to_hierarchy(appended_col, external_suffix)
    imported_time = time.time()
    profiles.add((imported_time - start_time), "IMPORT")

    local_col = bpy.data.collections[f"{col_base_name}.{local_suffix}"]
    external_col = bpy.data.collections[f"{col_base_name}.{external_suffix}"]

    # External col may come from publish, ensure it is not marked as asset so it purges correctly
    external_col.asset_clear()

    map = AssetTransferMapping(local_col, external_col, local_tls)
    error_msg = ''
    if len(map.conflict_transfer_data) != 0:
        for conflict in map.conflict_transfer_data:
            error_msg += f"Transferable Data conflict found for '{conflict.name}' on obj '{conflict.id_data.name}'\n"
        return error_msg

    if len(map.conflict_ids) != 0:
        for conflict_obj in map.conflict_ids:
            type_name = get_id_type_name(type(conflict_obj))
            error_msg += f"Ownership conflict found for {type_name}: '{conflict_obj.name}'\n"
        return error_msg
    mapped_time = time.time()
    profiles.add((mapped_time - imported_time), "MAPPING")

    # Remove all Transferable Data from target objects
    for source_obj in map.object_map:
        target_obj = map.object_map[source_obj]
        target_obj.transfer_data_ownership.clear()

    apply_transfer_data(context, map.transfer_data_map)
    apply_td_time = time.time()
    profiles.add((apply_td_time - mapped_time), "TRANSFER_DATA")

    for source_obj, target_obj in map.object_map.items():
        remap_user(source_obj, target_obj)
        transfer_data_clean(target_obj)
    obj_remap_time = time.time()
    profiles.add((obj_remap_time - apply_td_time), "OBJECTS")

    # Restore Active UV Layer and Active Color Attributes
    for _, index_map_item in map.index_map.items():
        target_obj = index_map_item.get('target_obj')
        transfer_active_uv_layer_index(target_obj, index_map_item.get('active_uv_name'))
        transfer_active_color_attribute_index(
            target_obj, index_map_item.get('active_color_attribute_name')
        )
    index_time = time.time()
    profiles.add((index_time - obj_remap_time), "INDEXES")

    for source_col, target_col in map.collection_map.items():
        remap_user(source_col, target_col)

    for col in map.external_col_to_add:
        local_col.children.link(col)

    for col in map.external_col_to_remove:
        local_col.children.unlink(col)
    col_remap_time = time.time()
    profiles.add((col_remap_time - index_time), "COLLECTIONS")

    for source_id, target_id in map.shared_id_map.items():
        remap_user(source_id, target_id)
    shared_id_remap_time = time.time()
    profiles.add((shared_id_remap_time - col_remap_time), "SHARED_IDS")

    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    merge_remove_suffix_from_hierarchy(local_col)
    profiles.add((time.time() - start_time), "MERGE")

def import_data_from_lib(
    libpath: Path,
    data_category: str,
    data_name: str,
    link: bool = False,
) -> bpy.types.ID:
    """Appends/Links data from an external file into the current file.

    Args:
        libpath (Path): path to .blend file that contains library
        data_category (str): bpy.types, like object or collection
        data_name (str): name of datablock to link/append
        link (bool, optional): Set to link library otherwise append. Defaults to False.

    Returns:
        bpy.types.ID: returns datablock that was linked/appended
    """

    noun = "Appended"
    if link:
        noun = "Linked"
    logger = logging.get_logger()
    data_local_collprop = getattr(bpy.data, data_category)
    with bpy.data.libraries.load(libpath.as_posix(), relative=True, link=link) as (
        data_from,
        data_to,
    ):
        data_from_collprop = getattr(data_from, data_category)
        data_to_collprop = getattr(data_to, data_category)
        if data_name not in data_from_collprop:
            logger.critical(
                f"Failed to import {data_category} {data_name} from {libpath.as_posix()}. Doesn't exist in file.",
            )

        # Check if datablock with same name already exists in blend file.
        existing_datablock = data_local_collprop.get(data_name)
        if existing_datablock:
            logger.critical(
                f"{data_name} already in bpy.data.{data_category} of this blendfile.",
            )

        # Append data block.
        data_to_collprop.append(data_name)
        logger.info(f"{noun}:{data_name} from library: {libpath.as_posix()}")

    if link:
        return data_local_collprop.get((data_name, bpy.path.relpath(libpath.as_posix())))

    return data_local_collprop.get(data_name)


def get_task_layer_objects(asset_pipe):
    local_task_layer_keys = asset_pipe.get_local_task_layers()
    local_col = asset_pipe.asset_collection
    task_layer_objs = []
    for col in local_col.children:
        if col.asset_id_owner in local_task_layer_keys:
            task_layer_objs = task_layer_objs + list(col.all_objects)
    return task_layer_objs
