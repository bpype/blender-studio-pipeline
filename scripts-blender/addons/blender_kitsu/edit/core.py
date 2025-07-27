# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import prefs, propsdata
import re
from pathlib import Path


def edit_export_get_latest(context: bpy.types.Context):
    """Find latest render in editorial export directory"""

    files_list = edit_export_get_all(context)
    if len(files_list) >= 1:
        files_list = sorted(files_list, reverse=True)
        return files_list[0]
    return None


def edit_export_get_all(context: bpy.types.Context):
    """Find all renders in editorial export directory"""
    addon_prefs = prefs.addon_prefs_get(context)

    edit_export_path = propsdata.get_edit_export_dir()

    if not edit_export_path.exists():
        print(f"Editorial export directory '{edit_export_path}' does not exist.")
        return []

    files_list = [
        f
        for f in edit_export_path.iterdir()
        if f.is_file() and edit_export_is_valid_name(addon_prefs.edit_export_file_pattern, f.name)
    ]
    return files_list


def edit_export_is_valid_name(file_pattern: str, filename: str) -> bool:
    """Verify file name matches file pattern set in preferences"""
    # Prevents un-expected matches
    file_pattern = re.escape(file_pattern)
    # Replace `#` with `\d` to represent digits
    match = re.search(file_pattern.replace('\#', '\d'), filename)
    if match:
        return True
    return False


def edit_export_import_latest(
    context: bpy.types.Context, shot
) -> list[bpy.types.Strip]:  # TODO add info to shot
    """Loads latest export from editorial department"""
    addon_prefs = prefs.addon_prefs_get(context)
    strip_channel = 1
    latest_file = edit_export_get_latest(context)
    if not latest_file:
        return None
    # Check if Kitsu server returned empty shot
    if shot.id == '':
        return None
    strip_filepath = latest_file.as_posix()
    strip_frame_start = addon_prefs.shot_builder_frame_offset

    scene = context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    seq_editor = scene.sequence_editor
    movie_strip = seq_editor.sequences.new_movie(
        latest_file.name,
        strip_filepath,
        strip_channel + 1,
        strip_frame_start,
        fit_method="ORIGINAL",
    )
    sound_strip = seq_editor.sequences.new_sound(
        latest_file.name,
        strip_filepath,
        strip_channel,
        strip_frame_start,
    )
    new_strips = [movie_strip, sound_strip]

    # Update shift frame range prop.
    frame_in = shot.data.get("frame_in")
    frame_3d_start = shot.get_3d_start()
    frame_3d_offset = frame_3d_start - addon_prefs.shot_builder_frame_offset
    edit_export_offset = addon_prefs.edit_export_frame_offset

    # Set sequence strip start kitsu data.
    for strip in new_strips:
        strip.frame_start = (
            -frame_in + (strip_frame_start * 2) + frame_3d_offset + edit_export_offset
        )
    return new_strips
