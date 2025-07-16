# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ..naming import merge_get_basename
from ..task_layer import get_transfer_data_owner
import contextlib

def check_transfer_data_entry(
    transfer_data: bpy.types.CollectionProperty, key: str, td_type_key: str
) -> set:
    """Verifies if Transferable Data entry exists

    Args:
        ownership (bpy.types.CollectionProperty): Transferable Data of an object
        key (str): Name of item that is being verified
        td_type_key (str): Type of Transferable Data

    Returns:
        set: Returns set of matches where name is found in ownership
    """
    existing_items = [
        transfer_data_item.name
        for transfer_data_item in transfer_data
        if transfer_data_item.type == td_type_key
    ]
    return set([key]).intersection(set(existing_items))


def transfer_data_add_entry(
    transfer_data: bpy.types.CollectionProperty,
    name: str,
    td_type_key: str,
    task_layer_name: str,
    surrender: bool,
):
    """Add entry to Transferable Data ownership

    Args:
        ownership (bpy.types.CollectionProperty): Transferable Data of an object
        name (str): Name of new Transferable Data item
        td_type_key (str): Type of Transferable Data
        task_layer_name (str): Name of current task layer
        surrender (bool): Whether this data's ownership should be surrendered to begin with
    """
    transfer_data_item = transfer_data.add()
    transfer_data_item.name = name
    transfer_data_item.owner = task_layer_name
    transfer_data_item.type = td_type_key
    transfer_data_item.surrender = surrender
    return transfer_data_item


def transfer_data_clean(
    obj: bpy.types.Object, data_list: bpy.types.CollectionProperty, td_type_key: str
):
    """Removes data if a transfer_data_item doesn't exist but the data does exist
    Args:
        obj (bpy.types.Object): Object containing Transferable Data
        data_list (bpy.types.CollectionProperty): Collection Property containing a type of possible Transferable Data e.g. obj.modifiers
        td_type_key (str): Key for the Transferable Data type
    """
    cleaned_item_names = set()

    for item in data_list:
        matches = check_transfer_data_entry(
            obj.transfer_data_ownership,
            merge_get_basename(item.name),
            td_type_key,
        )
        if len(matches) == 0:
            cleaned_item_names.add(item.name)
            data_list.remove(item)

    return cleaned_item_names

def transfer_data_item_is_missing(
    transfer_data_item, data_list: bpy.types.CollectionProperty, td_type_key: str
) -> bool:
    """Returns true if a transfer_data_item exists the data doesn't exist

    Args:
        transfer_data_item (_type_): Item of Transferable Data
        data_list (bpy.types.CollectionProperty): Collection Property containing a type of possible Transferable Data e.g. obj.modifiers
        td_type_key (str): Key for the Transferable Data type
    Returns:
        bool: Returns True if transfer_data_item is missing
    """
    if transfer_data_item.type == td_type_key and not data_list.get(
        transfer_data_item["name"]
    ):
        return True


"""Intilize Transferable Data to a temporary collection property, used
    to draw a display of new Transferable Data to the user before merge process. 
"""


def transfer_data_item_init(
    scene: bpy.types.Scene,
    obj: bpy.types.Object,
    data_list: bpy.types.CollectionProperty,
    td_type_key: str,
):
    """_summary_

    Args:
        scene (bpy.types.Scene): Scene that contains a the file's asset
        obj (bpy.types.Object): Object containing possible Transferable Data
        data_list (bpy.types.CollectionProperty): Collection Property containing a type of possible Transferable Data e.g. obj.modifiers
        td_type_key (str): Key for the Transferable Data type
    """
    asset_pipe = scene.asset_pipeline
    transfer_data = obj.transfer_data_ownership

    for item in data_list:
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        matches = check_transfer_data_entry(transfer_data, item.name, td_type_key)
        if len(matches) == 0:
            task_layer_owner, auto_surrender = get_transfer_data_owner(
                asset_pipe,
                td_type_key,
            )
            asset_pipe.add_temp_transfer_data(
                name=item.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


@contextlib.contextmanager
def isolate_collection(context, iso_col: bpy.types.Collection):
    col_exclude = {}
    view_layer_col = context.view_layer.layer_collection
    view_layer_col.collection.children.link(iso_col)
    for col in view_layer_col.children:
        col_exclude[col.name] = col.exclude

    try:
        # Exclude all collections that are not iso collection
        for col in view_layer_col.children:
            col.exclude = col.name != iso_col.name
        yield

    finally:
        for col in view_layer_col.children:
            col.exclude = col_exclude[col.name]
        view_layer_col.collection.children.unlink(iso_col)


@contextlib.contextmanager
def link_objs_to_collection(objs: set, col: bpy.types.Collection):
    try:
        for obj in objs:
            col.objects.link(obj)
        yield

    finally:
        for obj in objs:
            col.objects.unlink(obj)


@contextlib.contextmanager
def activate_shapekey(objs: set, sk_name: str):
    old_values = {}
    try:
        for obj in objs:
            if not obj.data.shape_keys:
                continue
            sk = obj.data.shape_keys.key_blocks.get(sk_name)
            if not sk:
                continue
            old_values[obj] = sk.value
            sk.value = 1
        yield

    finally:
        for obj, val in old_values.items():
            obj.data.shape_keys.key_blocks[sk_name].value = val

@contextlib.contextmanager
def disable_modifiers(objs: set, mod_types: set[str]):
    mods_to_enable = {obj: [] for obj in objs}
    try:
        for obj in objs:
            for mod in obj.modifiers:
                if mod.type in mod_types and mod.show_viewport:
                    mods_to_enable[obj].append(mod.name)
                    mod.show_viewport = False
        yield

    finally:
        for obj, mod_names in mods_to_enable.items():
            for mod_name in mod_names:
                obj.modifiers[mod_name].show_viewport = True

@contextlib.contextmanager
def simplify(scene):
    """Disable subdivision surface modifiers globally using the scene's Simplify setting.
    Important for binding modifiers, but also probably doesn't hurt for general performance.
    """
    orig_simplify = scene.render.use_simplify
    levels = scene.render.simplify_subdivision
    
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 0

    yield

    scene.render.use_simplify = orig_simplify
    scene.render.simplify_subdivision = levels
