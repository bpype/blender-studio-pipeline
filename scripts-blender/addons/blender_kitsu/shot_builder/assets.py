# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import prefs, bkglobals
from ..types import Shot
from . import core, config
from typing import Tuple, List


def get_shot_assets(
    scene: bpy.types.Scene,
    output_collection: bpy.types.Collection,
    shot: Shot,
) -> Tuple[List[str], List[str]]:
    """Link Assets into file by fetching metadata from Kitsu Server

    Args:
        scene (bpy.types.Scene): Scene to link Asset into
        output_collection (bpy.types.Collection): Collection to link Asset into
        shot (Shot): Shot context entity

    Returns:
        Tuple[List[str], List[str]]: Success Links, Failed Links (rturns list of status messages for each)
    """
    kitsu_assets = shot.get_all_assets()
    success_links = []
    fail_links = []

    for kitsu_asset in kitsu_assets:
        success, msg = get_shot_asset(kitsu_asset, scene, output_collection, shot)
        if success:
            success_links.append(msg)
        else:
            fail_links.append(msg)

    for msg in success_links:
        print(msg)

    for msg in fail_links:
        print(msg)
    return success_links, fail_links


def get_shot_asset(
    kitsu_asset: dict,
    scene: bpy.types.Scene,
    output_collection: bpy.types.Collection,
    shot: Shot,
) -> Tuple[bool, str]:
    asset_path = kitsu_asset.data.get(bkglobals.KITSU_FILEPATH_KEY)
    collection_name = kitsu_asset.data.get(bkglobals.KITSU_COLLECTION_KEY)
    if not asset_path:
        return False, f"Asset '{kitsu_asset.name}' is missing filepath on Kitsu Server"

    if not collection_name:
        return False, f"Asset '{kitsu_asset.name}' is missing collection name on Kitsu Sever"

    filepath = prefs.project_root_dir_get(bpy.context).joinpath(asset_path).absolute()
    if not filepath.exists():
        return (
            False,
            f"Asset '{kitsu_asset.name}' filepath '{str(filepath)}' does not exist. Skipping",
        )

    if config.ASSET_TYPE_TO_OVERRIDE.get(collection_name.split('-')[0]):
        linked_collection = core.link_and_override_collection(
            collection_name=collection_name, file_path=str(filepath), scene=scene
        )
        if not linked_collection:
            return (
                False,
                f"Asset '{kitsu_asset.name}' collection '{collection_name}' does not exist. Skipping",
            )

        core.add_action_to_armature(linked_collection, shot)
        msg = f"'{collection_name}': Successfully Linked & Overridden"
    else:
        linked_collection = core.link_data_block(
            file_path=str(filepath),
            data_block_name=collection_name,
            data_block_type="Collection",
        )
        msg = f"'{collection_name}': Successfully Linked"

    output_collection.children.link(linked_collection)
    return True, msg
