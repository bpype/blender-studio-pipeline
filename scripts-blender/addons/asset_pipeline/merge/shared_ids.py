# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy_extras.id_map_utils import get_id_reference_map, get_all_referenced_ids
from .util import get_fundamental_id_type
from .. import constants


def get_shared_ids(collection: bpy.types.Collection) -> list[bpy.types.ID]:
    """Returns a list of any ID that is not covered by the merge process

    Args:
        collection (bpy.types.Collection): Collection that contains data that references 'shared_ids'

    Returns:
        list[bpy.types.ID]: List of 'shared_ids'
    """
    ref_map = get_id_reference_map()
    all_ids_of_coll = get_all_referenced_ids(collection, ref_map)
    return [
        id
        for id in all_ids_of_coll
        if (isinstance(id, bpy.types.NodeTree) or isinstance(id, bpy.types.Image))
        and id.library is None
    ]


def init_shared_ids(scene: bpy.types.Scene) -> list[bpy.types.ID]:
    """Intilizes any ID not covered by the transfer process as an 'shared_id'
    and marks all 'shared_ids' without an owner to the current task layer

    Args:
        scene (bpy.types.Scene): Scene that contains a the file's asset

    Returns:
        list[bpy.types.ID]: A list of new 'shared_ids' owned by the file's task layer
    """
    asset_pipe = scene.asset_pipeline
    task_layer_key = asset_pipe.get_local_task_layers()[0]
    shared_ids = []
    local_col = asset_pipe.asset_collection
    for id in get_shared_ids(local_col):
        if id.asset_id_owner == 'NONE':
            id.asset_id_owner = task_layer_key
            shared_ids.append(id)
    return shared_ids


def get_shared_id_icon(id: bpy.types.ID) -> str:
    if bpy.types.NodeTree == get_fundamental_id_type(id):
        return constants.GEO_NODE
    if bpy.types.Image == get_fundamental_id_type(id):
        return constants.IMAGE
    return constants.BLANK
