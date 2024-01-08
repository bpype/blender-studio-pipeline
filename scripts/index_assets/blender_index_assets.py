# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from pathlib import Path
import bpy
import json
import sys


def load_json_file(json_file_path: str) -> dict:
    """Finds JSON file with asset index if any exist

    Args:
        json_file_path (str): Path to existing JSON File

    Returns:
        dict: Dictionary with the existing JSON File, else blank
    """
    asset_index_json = Path(json_file_path)
    if asset_index_json.exists():
        return json.load(open(asset_index_json))
    return {}


def dump_json_file(asset_dict: dict, json_file_path: str) -> None:
    """Save Asset Index to JSON File at provided path

    Args:
        asset_dict (dict): Dictionary of Asset Items
        json_file_path (str): Path to Save JSON File
    """
    with open(json_file_path, 'w') as json_file:
        json.dump(asset_dict, json_file, indent=4)


def get_realtive_path(json_file_path: str):
    """Store all Paths as relative to the parent directory
    of the JSON File, this will be the root of the asset
    directory which is being indexed."""
    asset_dir = Path(json_file_path).parent
    filepath = Path(bpy.data.filepath)
    return str(filepath.relative_to(asset_dir))


def find_save_assets():
    """Find all collections marked as asset in the current
    .blend file, and add them to a dictionary, saved as a JSON"""

    argv = sys.argv
    json_file_path = argv[argv.index("--") + 1 :][0]

    asset_dict = load_json_file(json_file_path)
    for col in bpy.data.collections:
        if col.asset_data:
            print(f"Found Asset {col.name}")
            asset_dict[col.name] = {
                'type': type(col).bl_rna.name,
                'filepath': get_realtive_path(json_file_path),
            }
    print('Asset Index Completed')
    dump_json_file(asset_dict, json_file_path)


find_save_assets()
