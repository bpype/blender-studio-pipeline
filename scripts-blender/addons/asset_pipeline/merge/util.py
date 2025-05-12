# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2021, Blender Foundation - Paul Golter

from typing import Any, Tuple, Generator, List
from .. import constants
import bpy


####################################
############# ID Stuff #############
####################################


def get_id_info() -> List[Tuple[type, str, str]]:
    """Return a list of tuples with the python class, type identifier string, and bpy.data container name
    of each ID type present in the blend file.
    Eg. when called in a file containing meshes and objects, it will return at least:
    [
        (bpy.types.Object, 'OBJECT', "objects"),
        (bpy.types.Mesh, 'MESH', "meshes"),
    ]
    """
    bpy_prop_collection = type(bpy.data.objects)
    id_info = []
    for prop_name in dir(bpy.data):
        coll_prop = getattr(bpy.data, prop_name)
        if type(coll_prop) == bpy_prop_collection:
            if len(coll_prop) == 0:
                # We can't get full info about the ID type if there isn't at least one entry of it.
                # But we shouldn't need it, since we don't have any entries of it!
                continue

            id_info.append((get_fundamental_id_type(coll_prop[0]), coll_prop[0].id_type, prop_name))
    return id_info


def get_id_identifier_from_class(id_type: type):
    """Return the string name of an ID type class.
    eg. bpy.types.Object -> 'OBJECT'
    """
    id_info = get_id_info()
    for typ, typ_str, container_str in id_info:
        if id_type == typ:
            return typ_str


def get_fundamental_id_type(datablock: bpy.types.ID) -> Any:
    """Certain datablocks have very specific types, such as
    bpy.types.GeometryNodeTree instead of bpy.types.NodeTree.

    This function should return their fundamental type, ie. parent class,
    by reaching into the python Method Resolution Order (MRO) to find its
    python class inheritance chain and then step back 4 steps:
    object->bpy_struct->bpy.types.ID->bpy.types.WhatWeNeed"""

    return type(datablock).mro()[-4]


def get_storage_of_id(datablock: bpy.types.ID) -> 'bpy_prop_collection':
    """Return the storage collection property of the datablock.
    Eg. for an object, returns bpy.data.objects.
    """

    fundamental_type = get_fundamental_id_type(datablock)

    id_info = get_id_info()
    for typ, _typ_str, container_str in id_info:
        if fundamental_type == typ:
            return getattr(bpy.data, container_str)
    assert False, "Failed to find the type of this ID: " + str(datablock) + "with fundamental type: " + str(fundamental_type)


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def data_type_from_transfer_data_key(obj: bpy.types.Object, td_type: str):
    """Returns the data on an object that is referred to by the Transferable Data type"""
    if td_type == constants.VERTEX_GROUP_KEY:
        return obj.vertex_groups
    if td_type == constants.MODIFIER_KEY:
        return obj.modifiers
    if td_type == constants.CONSTRAINT_KEY:
        return obj.constraints
    if td_type == constants.MATERIAL_SLOT_KEY:
        return obj.material_slots
    if td_type == constants.SHAPE_KEY_KEY:
        return obj.data.shape_keys.key_blocks
    if td_type == constants.ATTRIBUTE_KEY:
        return obj.data.attributes
    if td_type == constants.PARENT_KEY:
        return obj.parent
