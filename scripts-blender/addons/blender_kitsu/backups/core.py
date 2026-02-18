# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from ..context import core as context_core


def get_disk_version_folder() -> Path:
    return Path(bpy.data.filepath).parent.joinpath("version_backups")

def save_disk_version_backup_file(version_name:str) -> bool:
    """Saves a versioned backup of the current .blend file to disk.
    Args:
        version_name (str): The version name to append to the backup file.
    Returns:
        bool: True if the backup file was successfully created, False otherwise.
    
    """    
    basename = context_core.get_versioned_file_basename(Path(bpy.data.filepath).stem)

    version_filepath = basename + "-" + version_name + ".blend1"
    version_directory = get_disk_version_folder()
    version_directory.mkdir(exist_ok=True)
    version_filepath = version_directory.joinpath(version_filepath)
    
    # Check if the base version file exists and handle increments
    if version_filepath.exists():
        version_filepath = get_next_increment_filepath(version_name)
    
    bpy.ops.wm.save_as_mainfile(filepath=version_filepath.as_posix(), copy=True)
    
    if version_filepath.exists():
        return version_filepath
    
    return None
 

def get_next_increment_filepath(version_name: str) -> str:
    version_directory = get_disk_version_folder()
    basename = context_core.get_versioned_file_basename(Path(bpy.data.filepath).stem)
    pattern = f"{basename}-{version_name}_*.blend1"
    matching_files = list(version_directory.glob(pattern))
    increment = len(matching_files) + 1
    return version_directory.joinpath(
        f"{basename}-{version_name}_{increment:03d}.blend1"
    )