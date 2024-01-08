#!/usr/bin/env python3

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
import argparse
import os
import platform
import subprocess
import sys
import json


def cancel_program(message: str) -> None:
    """Cancel Execution of this file"""
    print(message)
    sys.exit(0)


parser = argparse.ArgumentParser()
parser.add_argument(
    "path",
    help="Path to a file(s) or folder(s) on which to perform crawl. In format of '{my_project}/'",
)


def get_bbatch_script_path() -> str:
    """Returns path to script that runs with bbatch"""
    dir = Path(__file__).parent.absolute()
    return dir.joinpath("blender_index_assets.py").__str__()


def get_blender_path(project_path: Path) -> str:
    """Get the path to a project's blender executable

    Args:
        project_path (Path): Path Object, containing project's root path

    Returns:
        str: Path to blender executable as a string
    """
    # TODO get this from the run_blender.py script instead (new logic needs tobe added to run_blender.py first)
    local_blender_path = project_path.joinpath('local').joinpath('blender')
    system_name = platform.system().lower()
    blender_path_base = local_blender_path / system_name
    if system_name == 'linux':
        blender_path = blender_path_base / 'blender'
    elif system_name == 'darwin':
        blender_path = blender_path_base / 'Blender.app' / 'Contents' / 'MacOS' / 'Blender'
    elif system_name == 'windows':
        blender_path = blender_path_base / 'blender.exe'
    return blender_path.absolute().__str__()


def index_assets():
    """Crawl the Asset Library of a provided Blender Studio Pipeline Project and
    index all assets into a dictionary using a script executed by bbatch"""
    args = parser.parse_args()
    project_path = Path(args.path)
    if not project_path.exists():
        cancel_program("Provided Path does not exist")
    asset_dir = project_path.joinpath("svn").joinpath("pro").joinpath("assets").absolute()
    if not asset_dir.exists():
        cancel_program("Asset Library does not exist at provided path")
    asset_dir_path = asset_dir.__str__()
    json_file_path = asset_dir.joinpath("asset_index.json").__str__()
    script_path = get_bbatch_script_path()
    project_blender = get_blender_path(project_path)
    # Reset Index File
    with open(json_file_path, 'w') as json_file:
        json.dump({}, json_file, indent=4)
    print(project_blender)
    os.chdir("../bbatch")
    cmd_list = (
        'python',
        '-m',
        'bbatch',
        asset_dir_path,
        '--ask',
        '--exec',
        project_blender,
        "--nosave",
        "--recursive",
        '--script',
        script_path,
        "--args",
        f'{json_file_path}',
    )
    process = subprocess.Popen(cmd_list, shell=False)
    if process.wait() != 0:
        cancel_program(f"Asset Index Failed!")
    print("Asset Index Completed Successfully")
    print(f"Index File: '{json_file_path}'")
    return 0


if __name__ == "__main__":
    index_assets()
