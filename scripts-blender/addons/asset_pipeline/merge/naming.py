# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2021, Blender Foundation - Paul Golter

import bpy
from bpy_extras.id_map_utils import get_id_reference_map, get_all_referenced_ids
from .util import get_storage_of_id
from .. import constants, config
from .util import data_type_from_transfer_data_key


def merge_get_target_suffix(suffix: str) -> str:
    """Get the corresponding suffix for a given suffix

    Args:
        suffix (str): Suffix for External or Local Datablock

    Returns:
        str: Returns External Suffix if given Local suffix for vice-versa
    """
    if suffix.endswith(constants.EXTERNAL_SUFFIX):
        return constants.LOCAL_SUFFIX
    if suffix.endswith(constants.LOCAL_SUFFIX):
        return constants.EXTERNAL_SUFFIX


def merge_get_target_name(name: str) -> str:
    """Get the corresponding target name for a given datablock's suffix.
    Suffixes are set by the add_suffix_to_hierarchy() function prior to
    calling this function.

    Args:
        name (str): Name of a given datablock including its suffix

    Returns:
        str: Returns datablock name with the opposite suffix
    """
    old = name.split(constants.MERGE_DELIMITER)[-1]
    new = merge_get_target_suffix(old)
    assert new, "Failed to flip the LOC/EXT suffix of this name, this should never happen : " + name
    li = name.rsplit(old, 1)
    return new.join(li)


def merge_get_basename(name: str) -> str:
    """Returns the name of an asset without its suffix"""
    if name.endswith(constants.LOCAL_SUFFIX) or name.endswith(
        constants.EXTERNAL_SUFFIX
    ):
        return constants.MERGE_DELIMITER.join(
            name.split(constants.MERGE_DELIMITER)[:-1]
        )
    return name


def merge_remove_suffix_from_hierarchy(collection: bpy.types.Collection) -> None:
    """Removes the suffix after a set delimiter from all datablocks
    referenced by a collection, itself included

    Args:
        collection (bpy.types.Collection): Collection that as been suffixed
    """

    ref_map = get_id_reference_map()
    datablocks = get_all_referenced_ids(collection, ref_map)
    datablocks.add(collection)
    for action in bpy.data.actions:
        datablocks.add(action)
    for db in datablocks:
        if db.library:
            # Don't rename linked datablocks.
            continue
        try:
            db.name = merge_get_basename(db.name)
        except:
            pass


def merge_add_suffix_to_hierarchy(
    collection: bpy.types.Collection, suffix_base: str
) -> None:
    """Add a suffix to the names of all datablocks referenced by a collection,
    itself included.

    Args:
        collection (bpy.types.Collection): Collection that needs to be suffixed
        suffix_base (str): Suffix to append to collection and items linked to collection
    """

    suffix = f"{constants.MERGE_DELIMITER}{suffix_base}"

    ref_map = get_id_reference_map()
    datablocks = get_all_referenced_ids(collection, ref_map)
    datablocks.add(collection)
    for db in datablocks:
        if len(db.name) > 59:
            raise Exception(
                f"Datablock name too long, must be max 59 characters: {db.name}"
            )

        if db.library:
            # Don't rename linked datablocks.
            continue
        collision_db = get_storage_of_id(db).get(db.name + suffix)
        if collision_db:
            collision_db.name += f'{constants.MERGE_DELIMITER}OLD'
        try:
            new_name = db.name + suffix
            db.name = new_name
            assert (
                db.name == new_name
            ), "This should never happen here, unless some add-on suffix is >3 characters. Avoid!"
        except:
            pass


def asset_prefix_name_get(name: str) -> str:
    """Returns a string with the asset prefix if it is not already set.
    Users can specify a prefix to live on all objects during the
    asset creation process. This prefix is stored in the scene.

    Args:
        name (str): Name to add prefix to

    Returns:
        str: Returns name with prefix
    """
    asset_pipe = bpy.context.scene.asset_pipeline
    if name.startswith(asset_pipe.prefix + constants.NAME_DELIMITER):
        return name
    prefix = (
        asset_pipe.prefix + constants.NAME_DELIMITER if asset_pipe.prefix != "" else ""
    )
    return prefix + name


def task_layer_prefix_name_get(name: str, task_layer_owner: str) -> str:
    """Returns a string with the task layer prefix if one is not already set.
    Prefix for assets is defined task_layer.json file within TASK_LAYER_TYPES
    Will return early if any prefix is found, cannot replace existing prefixes.

    Args:
        name (str): Name to add prefix to
        task_layer_owner (str):

    Returns:
        str: Returns name with prefix
    """
    for task_layer_key in config.TASK_LAYER_TYPES:
        if name.startswith(
            config.TASK_LAYER_TYPES[task_layer_key] + constants.NAME_DELIMITER
        ):
            return name
    prefix = config.TASK_LAYER_TYPES[task_layer_owner]
    return prefix + constants.NAME_DELIMITER + name


def task_layer_prefix_basename_get(name: str) -> str:
    """Get the base of a name if it contains a task layer prefix.
    This prefix is set on some Transferable Data items, this functions
    removes the prefixes and returns the basename

    Args:
        name (str): Original name including prefix

    Returns:
        str: Returns name without task layer prefix
    """
    for task_layer_key in config.TASK_LAYER_TYPES:
        if name.startswith(
            config.TASK_LAYER_TYPES[task_layer_key] + constants.NAME_DELIMITER
        ):
            return name.replace(name.split(constants.NAME_DELIMITER)[0], "")[1:]
    return name


def task_layer_prefix_legacy_basename(name) -> str:
    # TODO Remove this is legacy code (coordinate with team)
    if "." in name:
        legacy_name = name.replace(".", "")
        for task_layer_key in config.TASK_LAYER_TYPES:
            if legacy_name.startswith(config.TASK_LAYER_TYPES[task_layer_key]):
                return legacy_name.replace(config.TASK_LAYER_TYPES[task_layer_key], "")


def task_layer_prefix_transfer_data_update(
    transfer_data_item: bpy.types.CollectionProperty,
) -> bool:
    """Task Layer Prefix can become out of date with the actual owner of the task layer.
    This will update the existing prefixes on transfer_data_item so it can match the
    owner of that transfer_data_item. Will update both the transfer_data_item.name and the
    name of the actual data the transfer_data_item is referring to.

    Args:
        transfer_data_item (bpy.types.CollectionProperty): Transferable Data Item that is named with prefix

    Returns:
        bool: Returns True if a change to the name was completed
    """
    prefix_types = [constants.MODIFIER_KEY, constants.CONSTRAINT_KEY]
    if transfer_data_item.type not in prefix_types:
        return
    obj = transfer_data_item.id_data
    td_data = data_type_from_transfer_data_key(obj, transfer_data_item.type)

    # TODO Remove this
    # Legacy Prefix Name was used during add-on testing stage but not production
    legacy_name = task_layer_prefix_legacy_basename(transfer_data_item.name)

    if legacy_name:
        base_name = legacy_name
    else:
        base_name = task_layer_prefix_basename_get(transfer_data_item.name)

    prefix = config.TASK_LAYER_TYPES[transfer_data_item.owner]
    new_name = prefix + constants.NAME_DELIMITER + base_name
    if new_name == transfer_data_item.name or not td_data.get(transfer_data_item.name):
        return

    # Ensure no period in name
    # TODO Remove this is legacy code (coordinate with team)
    new_name = new_name.replace(".", "")

    td_data[transfer_data_item.name].name = new_name
    transfer_data_item.name = new_name
    return True


def get_id_type_name(id_type: bpy.types) -> str:
    """Return the cosmetic name of a given ID type

    Args:
        id_type (bpy.types): An ID type e.g. bpy.types.Object

    Returns:
        str: Name of an ID type e.g. bpy.types.Object will return 'Object'
    """
    return str(id_type).split("'bpy_types.")[1].replace("'>", "")
