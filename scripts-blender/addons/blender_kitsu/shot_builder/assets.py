# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from .. import prefs, bkglobals
from pathlib import Path
import json
from ..types import Shot
from . import core, config


def get_asset_dir() -> str:
    svn_project_root_dir = prefs.project_root_dir_get(bpy.context)
    asset_dir = Path(svn_project_root_dir).joinpath("pro").joinpath("assets")
    return asset_dir.__str__()


def get_asset_index_file() -> str:
    asset_index_file = Path(get_asset_dir()).joinpath("asset_index.json")
    if asset_index_file.exists():
        return asset_index_file.__str__()


def get_assset_index() -> dict:
    asset_index_file = get_asset_index_file()
    if asset_index_file is None:
        return
    return json.load(open(asset_index_file))


def get_shot_assets(
    scene: bpy.types.Scene,
    output_collection: bpy.types.Collection,
    shot: Shot,
):
    asset_index = get_assset_index()
    if asset_index is None:
        return
    kitsu_assets = shot.get_all_assets()

    for kitsu_asset in kitsu_assets:
        asset_path = kitsu_asset.data.get(bkglobals.KITSU_FILEPATH_KEY)
        collection_name = kitsu_asset.data.get(bkglobals.KITSU_COLLECTION_KEY)
        if not asset_path or not collection_name:
            print(
                f"Asset '{kitsu_asset.name}' is missing filepath or collection metadata. Skipping"
            )
            continue

        filepath = prefs.project_root_dir_get(bpy.context).joinpath(asset_path).absolute()
        if not filepath.exists():
            print(f"Asset '{kitsu_asset.name}' filepath '{str(filepath)}' does not exist. Skipping")

        if config.ASSET_TYPE_TO_OVERRIDE.get(collection_name.split('-')[0]):
            linked_collection = core.link_and_override_collection(
                collection_name=collection_name, file_path=str(filepath), scene=scene
            )
            core.add_action_to_armature(linked_collection, shot)
            print(f"'{collection_name}': Successfully Linked & Overridden")
        else:
            linked_collection = core.link_data_block(
                file_path=str(filepath),
                data_block_name=collection_name,
                data_block_type="Collection",
            )
            print(f"'{collection_name}': Successfully Linked")
        output_collection.children.link(linked_collection)
