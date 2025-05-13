#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import bpy
from pathlib import Path
import json
import hashlib
import time
import contextlib
from typing import List

file_updated = False


@contextlib.contextmanager
def override_save_version():
    """Overrides the save version settings"""
    save_version = bpy.context.preferences.filepaths.save_version

    try:
        bpy.context.preferences.filepaths.save_version = 0
        yield

    finally:
        bpy.context.preferences.filepaths.save_version = save_version


def paths_for_vse_strip(strip: bpy.types.Sequence) -> List[str]:
    """Returns all paths related to Movie, Image and Sound strips
    in Blender's Video Sequence Editor

    Args:
        strip (bpy.types.Sequence): Movie, Image or Sounds Strip

    Returns:
        List[str]: List of all paths related to strip
    """
    if hasattr(strip, "filepath"):
        return [strip.filepath]
    if hasattr(strip, "directory"):
        return [strip.directory + elt.filename for elt in strip.elements]
    if hasattr(strip, "sound"):
        return [strip.sound.filepath]
    return []


def generate_checksum(filepath: str) -> str:
    """Generate a checksum for a zip file

    Args:
        archive_path: String of the archive's file path
    Returns:
        sha256 checksum for the provided archive as string
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as file:
        # Read the file in chunks to handle large files efficiently
        chunk = file.read(4096)
        while len(chunk) > 0:
            sha256.update(chunk)
            chunk = file.read(4096)
    return sha256.hexdigest()


def dict_find_new_from_old(old_path: str, file_map_dict: dict) -> str:
    """Returns the matching 'new' filepath stored in file_map_dict
    using the 'old' filepath.

    Args:
        old_path (str): 'old' filepath referencing a file from Blender
        file_map_dict (dict): Dictionary of 'old' and 'new' paths

    Returns:
        str: 'new' filepath to replace the 'old' filepath
    """
    for _, value in file_map_dict.items():
        for old_json_path in value['old']:
            # Match paths using the filepath stored in Blender
            if old_json_path.endswith(old_path.split("/..")[-1]):
                if value['new'] != old_json_path:
                    return value['new']
    for _, value in file_map_dict.items():
        for old_json_path in value['old']:
            # Match paths using filename only
            if old_json_path.endswith(old_path.split("/")[-1]):
                if value['new'] != old_json_path:
                    return value['new']


def update_vse_references(file_map_dict: dict) -> None:
    """Update file references for VSE strips

    Args:
        file_map_dict (dict): Dictionary of 'old' and 'new' paths
    """
    global file_updated
    for scn in bpy.data.scenes:
        if not scn.sequence_editor:
            continue
        for strip in scn.sequence_editor.sequences_all:
            for path in paths_for_vse_strip(strip):
                if path == "":
                    continue
                new_path = dict_find_new_from_old(path, file_map_dict)
                if not new_path:
                    print(f"No new path for '{strip.name}' at '{path}' ")
                    continue
                if strip.type == "IMAGE":
                    old_filename = Path(path).name.__str__()
                    for elm in strip.elements:
                        if elm.filename == old_filename:
                            elm.filename = Path(new_path).name.__str__()
                    print(f"Remapping Image Strip {strip.name} {path} to {new_path}")
                    strip.directory = Path(new_path).parent.__str__()
                    file_updated = True

                if strip.type == "MOVIE":
                    if Path(new_path).is_file():
                        print(
                            f"Remapping Movie Strip {strip.name} {path} to {new_path}"
                        )
                        strip.filepath = Path(new_path).__str__()  # new_path
                        file_updated = True
                if strip.type == "SOUND":
                    if Path(new_path).is_file():
                        print(
                            f"Remapping Sound Strip {strip.name} {path} to {new_path}"
                        )
                        strip.sound.filepath = Path(new_path).__str__()  # new_path
                        file_updated = True


def update_referenced_images(file_map_dict: dict) -> None:
    """Update file references for Image data-blocks

    Args:
        file_map_dict (dict): Dictionary of 'old' and 'new' paths
    """
    global file_updated
    for img in bpy.data.images:
        if img.filepath is not None and img.filepath != "":
            new_path = dict_find_new_from_old(img.filepath, file_map_dict)
            if new_path:
                print(f"Remapping Image Datablock {img.filepath }")
                img.filepath = new_path
                file_updated = True


def update_libs(file_map_dict: dict) -> None:
    """Update file references for libraries (linked/appended data)

    Args:
        file_map_dict (dict): Dictionary of 'old' and 'new' paths
    """
    global file_updated
    for lib in bpy.data.libraries:
        new_path = dict_find_new_from_old(lib.filepath, file_map_dict)
        if new_path:
            lib.filepath = new_path
            print(f"Remapping {lib.filepath}")
            file_updated = True


def remap_all_blender_paths():
    """Remap all references to files from blender via dictionary"""
    start = time.time()
    import sys

    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    json_file_path = argv[0]

    file_map_json = Path(json_file_path)
    file_map_data = open(file_map_json)
    file_map_dict = json.load(file_map_data)

    update_vse_references(file_map_dict)
    update_referenced_images(file_map_dict)
    update_libs(file_map_dict)
    bpy.ops.file.make_paths_relative()
    end = time.time()

    if file_updated == True:
        with override_save_version():
            bpy.ops.wm.save_mainfile()
            print(f"Saved file: '{bpy.data.filepath}'")

    print("File Path Updater time elapsed in minutes")
    print((end - start) / 60)


remap_all_blender_paths()
