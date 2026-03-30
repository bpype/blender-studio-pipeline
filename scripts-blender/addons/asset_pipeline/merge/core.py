# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from pathlib import Path

import bpy
from bpy.types import ID, Collection, Context, Object, Scene

from .. import config, constants, logging
from ..merge.naming import task_layer_prefix_transfer_data_update
from ..props import AssetPipeline, AssetTransferDataTemp
from .asset_mapping import AssetTransferMapping, merge_get_target_name
from .naming import (
    get_id_type_name,
    merge_add_suffix_to_hierarchy,
    merge_remove_suffix_from_hierarchy,
)
from .transfer_data.transfer_core import (
    apply_transfer_data,
    init_transfer_data,
    transfer_data_clean_all,
    transfer_data_is_missing,
)
from .transfer_data.transfer_functions.transfer_function_util.active_indexes import (
    transfer_active_color_attribute_index,
    transfer_active_uv_layer_index,
)
from .transfer_data.transfer_functions.transfer_function_util.armature import (
    reset_armature,
)
from .transfer_data.transfer_util import (
    simplify,
    transfer_data_add_entry,
)


def ownership_transfer_data_cleanup(
    asset_pipe: AssetPipeline,
    obj: Object,
) -> None:
    """Remove Transferable Data ownership items if the corresponding data is missing

    Args:
        obj (Object): Object that contains the Transferable Data
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
    local_col: Collection,
    scene: Scene,
) -> None:
    """Find new Transferable Data owned by the local task layer.
    Marks items as owned by the local task layer if they are in the
    corresponding task layer collection and have no owner.

    Args:
        local_col: The top level asset collection that is local to the file
        scene: Active scene (which holds add-on data.)

    Returns:
        list[Object]: Returns a list of objects that have no owner and will not be included
        in the merge process
    """
    asset_pipe = scene.asset_pipeline
    asset_pipe.temp_transfer_data.clear()

    default_task_layer = asset_pipe.get_local_task_layers()[0]

    for col in asset_pipe.asset_collection.children:
        if col.asset_id_owner == "NONE":
            col.asset_id_owner = default_task_layer

    task_layer_objs = get_local_tasklayer_collection_objects(asset_pipe)

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


def ownership_set(temp_transfer_data: list[AssetTransferDataTemp]) -> None:
    """Add new Transferable Data items on each object found in the
    temp Transferable Data collection property

    Args:
        temp_transfer_data: Collection property containing newly found
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
    asset_pipe: AssetPipeline,
    local_col: Collection,
) -> set[Object]:
    """Returns a list of objects not used in the merge processing,
    which are considered invalid. The objects will be excluded from
    the merge process.

    Args:
        asset_pipe: Asset pipeline data.
        local_col: Asset root collection.

    Returns:
        Set of Invalid Objects
    """
    invalid_objs = set()
    for obj in local_col.all_objects:
        if obj.library:
            # Linked objects don't have or need ownership data, so they don't count
            # as invalid.
            continue
        if obj.asset_id_owner == "NONE":
            invalid_objs.add(obj)
        if not any([obj in set(coll.all_objects) for coll in asset_pipe.asset_collection.children if coll.asset_id_owner == obj.asset_id_owner]):
            # Object is not assigned to its owning task layer's collection.
            invalid_objs.add(obj)
    return invalid_objs


def remap_user(source_datablock: ID, target_datablock: ID) -> None:
    """Remap datablock and append name to datablock that has been remapped

    Args:
        source_datablock (ID): datablock that will be replaced by the target
        target_datablock (ID): datablock that will replace the source
    """
    logger = logging.get_logger()
    logger.debug(f"Remapping {source_datablock.rna_type.name}: {source_datablock.name} to {target_datablock.name}")
    source_datablock.user_remap(target_datablock)
    source_datablock.name += "_Users_Remapped"


def merge_task_layer(
    context: Context,
    local_tls: list[str],
    external_file: Path,
) -> tuple[Collection, str]:
    """Combines data from an external .blend file's asset collection, with
    the copy of the same asset collection in the local .blend file.

    During a Push step, this function should be called after opening the
    sync target .blend.

    The process goes something like this:
        1. Add .LOC name suffix to the local datablocks.
        2. Append the asset from the external .blend.
        3. Add .EXT name suffix to the appended datablocks.
           The name suffixing serves two purposes: 1) Avoid name conflicts. 2) Help pairing objects.
        4. Based on ownership data stored on both copies and the passed "local_tls" list of
           task layer names, we generate a source->target mapping between the two sets of objects.
           4.1 We also detect any ownership conflicts during this step, and raise errors.
           4.2 We also keep track of objects which have been removed or added.
        5. Whichever object is owner by one of the local task layers, becomes the target for data
           transfers, and the other object becomes the source. Then, any data owned by other task
           layers on the other object, gets transferred.
        6. Transfer all transferable data from sources to targets.
            6.1 Link new objects to the local collection
            6.2 Remove objects from the local collection whose external pair was not found in their
                corresponding task layer collection.

    Args:
        context: (Context): context of current .blend
        local_tls: (list[str]): list of task layers that are local to the current file
        external_file (Path): external file to pull data into the current file from
    """

    profiles = logging.get_profiler()
    assetpipe = context.scene.asset_pipeline

    start_time = time.time()
    local_col = assetpipe.asset_collection
    if not local_col:
        return "Unable to find Asset Collection"
    col_base_name = local_col.name
    local_suffix = constants.LOCAL_SUFFIX
    external_suffix = constants.EXTERNAL_SUFFIX
    merge_add_suffix_to_hierarchy(local_col, local_suffix)

    external_col = import_data_from_lib(external_file, "collections", col_base_name)
    assert external_col, f"Failed to append collection {col_base_name} from {external_file}"
    merge_add_suffix_to_hierarchy(external_col, external_suffix)
    imported_time = time.time()
    profiles.add((imported_time - start_time), "IMPORT")

    local_col = bpy.data.collections[f"{col_base_name}.{local_suffix}"]
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            reset_armature(obj)

    # External col may come from publish, ensure it is not marked as asset so it purges correctly
    external_col.asset_clear()

    task_layer_dict = config.get_task_layer_dict()
    json_push_count = task_layer_dict.get("FORCE_PUSH_COUNTER", 0)
    local_push_count = assetpipe.force_push_counter
    if assetpipe.is_published and local_push_count > json_push_count:
        # This is an error case that can happen if user force pushes, then
        # reverts the .json file using version control, but does not revert the publish.
        return external_col, f".json's push counter ({json_push_count}) less than publish ({local_push_count})!"
    if local_push_count < json_push_count:
        assetpipe.force_push_counter = json_push_count
        # In the case of a force push, we simply fully replace the asset, without transferring any data.
        replace_asset(local_col, external_col)
        return external_col, ""

    map = AssetTransferMapping(local_col, external_col, local_tls)
    error_msg = ''
    if len(map.conflict_transfer_data) != 0:
        for conflict in map.conflict_transfer_data:
            error_msg += f"Transferable Data conflict found for '{conflict.name}' on obj '{conflict.id_data.name}'\n"
        return local_col, error_msg

    if len(map.conflict_ids) != 0:
        for conflict_obj in map.conflict_ids:
            type_name = get_id_type_name(conflict_obj)
            error_msg += f"Ownership conflict found for {type_name}: '{conflict_obj.name}'\n"
        return local_col, error_msg
    mapped_time = time.time()
    profiles.add((mapped_time - imported_time), "MAPPING")

    # Remove all Transferable Data from target objects
    for source_obj in map.object_map:
        target_obj = map.object_map[source_obj]
        target_obj.transfer_data_ownership.clear()

    with simplify(context.scene):
        apply_transfer_data(context, map.transfer_data_map)
    apply_td_time = time.time()
    profiles.add((apply_td_time - mapped_time), "TRANSFER_DATA")

    for source_obj, target_obj in map.object_map.items():
        remap_user(source_obj, target_obj)
        transfer_data_clean_all(target_obj)
    obj_remap_time = time.time()
    profiles.add((obj_remap_time - apply_td_time), "OBJECTS")

    # Restore Active UV Layer and Active Color Attributes
    for _, index_map_item in map.index_map.items():
        target_obj = index_map_item.get('target_obj')
        transfer_active_uv_layer_index(target_obj, index_map_item.get('active_uv_name'))
        transfer_active_color_attribute_index(target_obj, index_map_item.get('active_color_attribute_name'))
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

    return local_col, ""


def replace_asset(to_replace: Collection, replaced_by: Collection):
    for child_coll in to_replace.children_recursive:
        other_coll_name = merge_get_target_name(child_coll.name)
        other_coll = bpy.data.collections.get(other_coll_name)
        if other_coll:
            child_coll.user_remap(other_coll)
        for obj in child_coll.objects:
            other_obj_name = merge_get_target_name(obj.name)
            other_obj = bpy.data.objects.get(other_obj_name)
            if other_obj:
                obj.user_remap(other_obj)
    to_replace.user_remap(replaced_by)

    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    merge_remove_suffix_from_hierarchy(replaced_by)


def import_data_from_lib(
    libpath: Path,
    data_category: str,
    data_name: str,
    link: bool = False,
) -> ID:
    """Appends/Links data from an external file into the current file.

    Args:
        libpath (Path): path to .blend file that contains library
        data_category (str): bpy.types, like object or collection
        data_name (str): name of datablock to link/append
        link (bool, optional): Set to link library otherwise append. Defaults to False.

    Returns:
        ID: returns datablock that was linked/appended
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


def get_local_tasklayer_collection_objects(asset_pipe: AssetPipeline) -> list[Object]:
    """Return all objects in collections of local task layers."""
    local_task_layer_keys = asset_pipe.get_local_task_layers()
    root_coll = asset_pipe.asset_collection
    objs = set()
    for col in root_coll.children:
        if col.asset_id_owner in local_task_layer_keys:
            objs |= set(col.all_objects)
    return list(objs)


def get_local_tasklayer_objects(asset_pipe: AssetPipeline) -> list[Object]:
    """Return all objects in collections of local task layers
    WHICH ARE OWNED BY a local task layer."""
    local_task_layer_keys = asset_pipe.get_local_task_layers()
    coll_objects = get_local_tasklayer_collection_objects(asset_pipe)
    return [o for o in coll_objects if o.asset_id_owner in local_task_layer_keys]
