import os
from pathlib import Path
import bpy

asset_file_cache = None
cat_data_cache = None


# TODO add refresh operator


def find_asset_cat_file(directory):
    global asset_file_cache
    if asset_file_cache is not None:
        return asset_file_cache
    asset_file = os.path.join(directory, "blender_assets.cats.txt")
    if os.path.exists(asset_file):
        return asset_file

    parent_dir = os.path.dirname(directory)
    if parent_dir == directory:
        return None

    return find_asset_cat_file(parent_dir)


def get_asset_cat_enum_items(reload: bool = False):
    global cat_data_cache
    if cat_data_cache is not None and not reload:
        return cat_data_cache
    items = []
    items.append(('NONE', 'None', ''))
    asset_cat_file = find_asset_cat_file(Path(bpy.data.filepath).parent.__str__())
    if asset_cat_file is None:
        return items

    with (Path(asset_cat_file)).open() as file:
        for line in file.readlines():
            if line.startswith(("#", "VERSION", "\n")):
                continue
            # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
            name = line.split(':', 1)[1].split(":")[-1].strip("\n")
            uuid = line.split(':', 1)[0]

            items.append((uuid, name, ''))
    return items
