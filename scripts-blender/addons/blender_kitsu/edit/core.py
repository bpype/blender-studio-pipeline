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
    """Loads latest export from editorial department.

    There are two items to consider when calculating
    the strip frame start:

    1. The `shot.get_3d_start()` a.k.a `data["3d_start"]` set on kitsu 
       (the first frame of an animation file). 
       See:
        - `shot_builder_frame_offset`
        - `KITSU_OT_push_frame_range`
        - `bpy.types.Strip.kitsu_3d_start`
       
    2. The first frame where this shot appears in the edit
       (set on kitsu as frame_in). This is the frame in the
       editorial movie the shot starts at.
       
    NOTE: We need to -1 from the shot frame_in because the first frame of a movie is 1, not 0.

    Example 1: The first shot has frame_in=1 on Kitsu and
    every shot file starts on frame 101. Subtracting gives
    100, so we subtract 1 more to get the correct movie
    start frame of 101.

    Example 2: The second shot has frame_in=51. It appears
    at frame 51 in the editorial movie. The movie is offset
    by -50 frames so the shot starts on frame 101 as
    expected.
    """
    strip_channel = 1
    latest_file = edit_export_get_latest(context)
    if not latest_file:
        return None
    # Check if Kitsu server returned empty shot
    if shot.id == '':
        return None
    strip_filepath = bpy.path.relpath(latest_file.as_posix())
    strip_frame_start = shot.get_3d_start() - (shot.data.get("frame_in") - 1)

    scene = context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    seq_editor = scene.sequence_editor
    movie_strip = seq_editor.strips.new_movie(
        latest_file.name,
        strip_filepath,
        strip_channel + 1,
        strip_frame_start,
        fit_method="ORIGINAL",
    )
    sound_strip = seq_editor.strips.new_sound(
        latest_file.name,
        strip_filepath,
        strip_channel,
        strip_frame_start,
    )
    return [movie_strip, sound_strip]