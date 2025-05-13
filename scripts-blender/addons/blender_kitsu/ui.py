# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import prefs


def draw_error_box(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    box = layout.box()
    box.label(text="Error", icon="ERROR")
    return box


def draw_error_active_project_unset(box: bpy.types.UILayout) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="No Active Project")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = __package__


def draw_error_invalid_playblast_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Playblast Root Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = __package__


def draw_error_invalid_edit_export_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Edit Export Directory")
    row.operator("preferences.addon_show", text="Open Addon Preferences").module = __package__


def draw_error_frame_range_outdated(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.alert = True
    row.label(text="Frame Range Outdated")
    row.operator("kitsu.pull_frame_range", icon="TRIA_DOWN")


def draw_error_invalid_render_preset_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Render Preset Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = __package__


def draw_error_invalid_project_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Project Root Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = __package__


def draw_error_config_dir_not_exists(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    row = box.row(align=True)
    row.label(text=f"Config Directory does not exist: {addon_prefs.config_dir}")


def draw_error_no_active_camera(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text=f"No active camera")
    row.prop(bpy.context.scene, "camera", text="")
