import bpy
from .. import prefs
from pathlib import Path
import json
from ..types import Shot
from .core import link_and_override_collection, link_data_block
from .. import bkglobals


def get_asset_index_file() -> str:
    svn_project_root_dir = prefs.project_root_dir_get(bpy.context)
    asset_index_file = (
        Path(svn_project_root_dir)
        .joinpath("pro")
        .joinpath("assets")
        .joinpath("asset_index.json")
    )
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
    assets = shot.get_all_assets()
    asset_slugs = [
        asset.data.get("slug") for asset in assets if asset.data.get("slug") is not None
    ]
    if asset_slugs == []:
        print("No asset slugs found on Kitsu Server. Assets will not be loaded")
    for key, value in asset_index.items():
        if key in asset_slugs:
            filepath = value.get('filepath')
            data_type = value.get('type')
            if bkglobals.ASSET_TYPE_TO_OVERRIDE.get(key.split('-')[0]):
                if data_type != "Collection":
                    print(f"Cannot load {key} because it is not a collection")
                    continue
                linked_collection = link_and_override_collection(
                    collection_name=key, file_path=filepath, scene=scene
                )
                print(f"'{key}': Succesfully Linked & Overriden")
            else:
                linked_collection = link_data_block(
                    file_path=filepath, data_block_name=key, data_block_type=data_type
                )
                print(f"'{key}': Succesfully Linked")
            output_collection.children.link(linked_collection)
