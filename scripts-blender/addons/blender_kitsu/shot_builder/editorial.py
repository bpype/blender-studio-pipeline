import bpy
from .. import prefs
from pathlib import Path
import re
from ..edit import core as edit_core


def edit_export_import_latest(
    context: bpy.types.Context, shot
) -> list[bpy.types.Sequence]:  # TODO add info to shot
    """Loads latest export from editorial department"""
    addon_prefs = prefs.addon_prefs_get(context)
    strip_channel = 1
    latest_file = edit_core.edit_export_get_latest(context)
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
