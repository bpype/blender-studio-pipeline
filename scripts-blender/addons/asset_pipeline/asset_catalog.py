# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import List

import bpy

asset_file_cache = None
cat_data_cache = None
asset_cat_dict = {}


def find_asset_cat_file(directory: str) -> str:
    """Find Asset Catalog file in directory or parent directories, recursively

    Args:
        directory (str): Directory to search for Asset Catalog file

    Returns:
        str: Path to Asset Catalog file or None if not found
    """
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


def get_asset_catalog_items(reload: bool = False) -> List[str]:
    """Generate List of Asset Catalog Items, and Dictionary of
    Asset Catalog UUIDs with their matching names. When this function
    is called the list and dict of asset catalog items will be updated.

    The List is used in the UI to populate the Asset Catalog List, and the
    Dictionary is used to look up the asset catalog UUID based on the name.

    Args:
        reload (bool, optional): Forces reload of list/dict if True. Defaults to False.

    Returns:
        List[str]: Returns list of strings representing Asset Catalog Names
    """
    global cat_data_cache
    global asset_cat_dict
    asset_cat_list = []

    # Return Empty List if File doesn't exist
    asset_cat_file = find_asset_cat_file(Path(bpy.data.filepath).parent.__str__())
    if asset_cat_file is None:
        return asset_cat_list

    # Return Cached List if exists and reload is False
    if cat_data_cache is not None and not reload:
        return cat_data_cache

    asset_cat_dict.clear()  # Reset dict so it is in sync with name list

    # Loop over items in file to find asset catalog
    with (Path(asset_cat_file)).open() as file:
        for line in file.readlines():
            if line.startswith(("#", "VERSION", "\n")):
                continue
            # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
            name = line.split(':', 1)[1].split(":")[-1].strip("\n")
            uuid = line.split(':', 1)[0]
            asset_cat_dict[uuid] = name  # Populate dict of uuid:name
            asset_cat_list.append(name)  # Populate list of asset catalogue names

    cat_data_cache = asset_cat_list  # Update Cache List
    return asset_cat_list


def get_asset_id(name: str) -> str:
    """Get Asset Catalog UUID based on Asset Catalog Name

    Args:
        name (str): Asset Catalog Name

    Returns:
        str: Asset Catalog UUID or None if not found
    """
    global asset_cat_dict
    for key, value in asset_cat_dict.items():
        if value == name:
            return key


def get_asset_name(id: str) -> str:
    """Get Asset Catalog UUID based on Asset Catalog Name

    Args:
        name (str): Asset Catalog Name

    Returns:
        str: Asset Catalog UUID or None if not found
    """
    global asset_cat_dict
    for key, value in asset_cat_dict.items():
        if key == id:
            return value
