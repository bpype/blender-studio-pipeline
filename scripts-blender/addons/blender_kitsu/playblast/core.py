# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from bpy.types import Context
import contextlib
from typing import Tuple
from .. import prefs, cache
from ..logger import LoggerFactory

logger = LoggerFactory.getLogger()


@contextlib.contextmanager
def override_render_format(self, context: Context, enable_sequencer: bool = False):
    """Overrides the render settings for playblast creation"""
    rd = context.scene.render

    if bpy.app.version >= (5, 0, 0):
        # For Blender 5.0 and later, use the new FFMPEG settings.
        media_type = rd.image_settings.media_type

    use_sequencer = rd.use_sequencer = enable_sequencer
    # Format render settings.
    # percentage = rd.resolution_percentage
    file_format = rd.image_settings.file_format
    ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
    ffmpeg_codec = rd.ffmpeg.codec
    ffmpeg_format = rd.ffmpeg.format
    ffmpeg_audio_codec = rd.ffmpeg.audio_codec

    try:
        if bpy.app.version >= (5, 0, 0):
            # For Blender 5.0 and later, use the new FFMPEG settings.
            rd.image_settings.media_type = "VIDEO"

        # rd.resolution_percentage = 100
        rd.use_sequencer = enable_sequencer
        rd.image_settings.file_format = "FFMPEG"
        rd.ffmpeg.constant_rate_factor = "HIGH"
        rd.ffmpeg.codec = "H264"
        rd.ffmpeg.format = "MPEG4"
        rd.ffmpeg.audio_codec = "AAC"

        yield

    finally:
        # rd.resolution_percentage = percentage
        if bpy.app.version >= (5, 0, 0):
            # For Blender 5.0 and later, use the new FFMPEG settings.
            rd.image_settings.media_type = media_type

        rd.use_sequencer = use_sequencer
        rd.image_settings.file_format = file_format
        rd.ffmpeg.codec = ffmpeg_codec
        rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
        rd.ffmpeg.format = ffmpeg_format
        rd.ffmpeg.audio_codec = ffmpeg_audio_codec


@contextlib.contextmanager
def override_render_path(self, context: Context, render_file_path: str):
    """Overrides the render settings for playblast creation"""
    rd = context.scene.render
    # Filepath.
    filepath = rd.filepath

    try:
        # Filepath.
        rd.filepath = render_file_path

        yield

    finally:
        # Filepath.
        rd.filepath = filepath


@contextlib.contextmanager
def override_hide_viewport_overlays(self, context: Context):
    sp = context.space_data
    show_gizmo = sp.show_gizmo
    show_overlays = sp.overlay.show_overlays

    try:
        sp.show_gizmo = False
        sp.overlay.show_overlays = False

        yield
    finally:
        sp.show_gizmo = show_gizmo
        sp.overlay.show_overlays = show_overlays


@contextlib.contextmanager
def override_metadata_stamp_settings(self, context: Context, username: str = "None"):
    addon_prefs = prefs.addon_prefs_get(context)
    if addon_prefs.pb_manual_burn_in:
        try:
            yield
        finally:
            return

    rd = context.scene.render

    # Get shot name for stamp note text.
    shot = cache.shot_active_get()

    # Remember current render settings in order to restore them later.

    # Stamp metadata settings.
    metadata_input = rd.metadata_input
    use_stamp_date = rd.use_stamp_date
    use_stamp_time = rd.use_stamp_time
    use_stamp_render_time = rd.use_stamp_render_time
    use_stamp_frame = rd.use_stamp_frame
    use_stamp_frame_range = rd.use_stamp_frame_range
    use_stamp_memory = rd.use_stamp_memory
    use_stamp_hostname = rd.use_stamp_hostname
    use_stamp_camera = rd.use_stamp_camera
    use_stamp_lens = rd.use_stamp_lens
    use_stamp_scene = rd.use_stamp_scene
    use_stamp_marker = rd.use_stamp_marker
    use_stamp_marker = rd.use_stamp_marker
    use_stamp_note = rd.use_stamp_note
    stamp_note_text = rd.stamp_note_text
    use_stamp = rd.use_stamp
    # stamp_font_size = rd.stamp_font_size
    stamp_foreground = rd.stamp_foreground
    stamp_background = rd.stamp_background
    use_stamp_labels = rd.use_stamp_labels
    try:
        # Stamp metadata settings.
        rd.metadata_input = "SCENE"
        rd.use_stamp_date = False
        rd.use_stamp_time = False
        rd.use_stamp_render_time = False
        rd.use_stamp_frame = True
        rd.use_stamp_frame_range = False
        rd.use_stamp_memory = False
        rd.use_stamp_hostname = False
        rd.use_stamp_camera = False
        rd.use_stamp_lens = True
        rd.use_stamp_scene = False
        rd.use_stamp_marker = False
        rd.use_stamp_marker = False
        rd.use_stamp_note = True
        rd.stamp_note_text = f"Shot: {shot.name} | Animator: {username}"
        rd.use_stamp = True
        rd.stamp_font_size = 24
        rd.stamp_foreground = (0.8, 0.8, 0.8, 1)
        rd.stamp_background = (0, 0, 0, 0.25)
        rd.use_stamp_labels = True

        yield

    finally:
        # Stamp metadata settings.
        rd.metadata_input = metadata_input
        rd.use_stamp_date = use_stamp_date
        rd.use_stamp_time = use_stamp_time
        rd.use_stamp_render_time = use_stamp_render_time
        rd.use_stamp_frame = use_stamp_frame
        rd.use_stamp_frame_range = use_stamp_frame_range
        rd.use_stamp_memory = use_stamp_memory
        rd.use_stamp_hostname = use_stamp_hostname
        rd.use_stamp_camera = use_stamp_camera
        rd.use_stamp_lens = use_stamp_lens
        rd.use_stamp_scene = use_stamp_scene
        rd.use_stamp_marker = use_stamp_marker
        rd.use_stamp_marker = use_stamp_marker
        rd.use_stamp_note = use_stamp_note
        rd.stamp_note_text = stamp_note_text
        rd.use_stamp = use_stamp
        # rd.stamp_font_size = stamp_font_size
        rd.stamp_foreground = stamp_foreground
        rd.stamp_background = stamp_background
        rd.use_stamp_labels = use_stamp_labels


@contextlib.contextmanager
def override_viewport_shading(self, context: Context):
    """Overrides the render settings for playblast creation"""
    rd = context.scene.render
    sps = context.space_data.shading
    sp = context.space_data

    # Space data settings.
    shading_type = sps.type
    shading_light = sps.light
    studio_light = sps.studio_light
    color_type = sps.color_type
    background_type = sps.background_type

    show_backface_culling = sps.show_backface_culling
    show_xray = sps.show_xray
    show_shadows = sps.show_shadows
    show_cavity = sps.show_cavity
    show_object_outline = sps.show_object_outline
    show_specular_highlight = sps.show_specular_highlight

    try:
        # Space data settings.
        sps.type = "SOLID"
        sps.light = "STUDIO"
        sps.studio_light = "paint.sl"
        sps.color_type = "MATERIAL"
        sps.background_type = "THEME"

        sps.show_backface_culling = False
        sps.show_xray = False
        sps.show_shadows = False
        sps.show_cavity = False
        sps.show_object_outline = False
        sps.show_specular_highlight = True

        yield

    finally:
        # Space data settings.
        sps.type = shading_type
        sps.light = shading_light
        sps.studio_light = studio_light
        sps.color_type = color_type
        sps.background_type = background_type

        sps.show_backface_culling = show_backface_culling
        sps.show_xray = show_xray
        sps.show_shadows = show_shadows
        sps.show_cavity = show_cavity
        sps.show_object_outline = show_object_outline
        sps.show_specular_highlight = show_specular_highlight


def ensure_render_path(file_path: str) -> Path:
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def playblast_with_scene_settings(self, context: Context, file_path: str, username: str) -> Path:
    with override_render_path(self, context, file_path):
        with override_render_format(self, context):
            with override_metadata_stamp_settings(self, context, username):
                output_path = ensure_render_path(file_path)
                bpy.ops.render.render(animation=True, use_viewport=False)
                return output_path


def playblast_with_viewport_settings(self, context: Context, file_path: str, username: str) -> Path:
    with override_render_path(self, context, file_path):
        with override_render_format(self, context):
            with override_metadata_stamp_settings(self, context, username):
                output_path = ensure_render_path(file_path)
                bpy.ops.render.opengl(animation=True)
                return output_path


def playblast_with_viewport_preset_settings(
    self, context: Context, file_path: str, username: str
) -> Path:
    with override_render_path(self, context, file_path):
        with override_render_format(self, context):
            with override_metadata_stamp_settings(self, context, username):
                with override_viewport_shading(self, context):
                    with override_hide_viewport_overlays(self, context):
                        output_path = ensure_render_path(file_path)
                        bpy.ops.render.opengl(animation=True)
                        return output_path


def playblast_vse(self, context: Context, file_path: str) -> Path:
    with override_render_path(self, context, file_path):
        with override_render_format(self, context, enable_sequencer=True):
            output_path = ensure_render_path(file_path)
            bpy.ops.render.opengl(animation=True, sequencer=True)
            return output_path


def set_frame_range_in(frame_in: int) -> dict:
    shot = cache.shot_active_pull_update()
    shot.data["3d_start"] = frame_in
    shot.update()
    return shot


def get_frame_range() -> Tuple[int, int]:
    active_shot = cache.shot_active_get()
    if not active_shot:
        return

    # Pull update for shot.
    cache.shot_active_pull_update()
    kitsu_3d_start = active_shot.get_3d_start()
    frame_in = kitsu_3d_start
    frame_out = kitsu_3d_start + int(active_shot.nb_frames) - 1
    return frame_in, frame_out


def check_frame_range(context: Context) -> bool:
    """
    Compare the current scene's frame range with that of the active shot on kitsu.
    If there's a mismatch, set kitsu_error.frame_range -> True. This will enable
    a warning in the Animation Tools Tab UI.
    """
    try:
        frame_in, frame_out = get_frame_range()
    except TypeError:
        return
    scene = context.scene

    if frame_in == scene.frame_start and frame_out == scene.frame_end:
        scene.kitsu_error.frame_range = False
        return True

    scene.kitsu_error.frame_range = True
    logger.warning("Current frame range is outdated!")
    return False
