# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import cache, bkglobals


# Category values are defined in enum props.py KITSU_property_group_scene under category
def is_edit_context():
    return bpy.context.scene.kitsu.category == "EDIT"


def is_sequence_context():
    return bpy.context.scene.kitsu.category == "SEQ"


def is_asset_context():
    return bpy.context.scene.kitsu.category == "ASSET"


def is_shot_context():
    return bpy.context.scene.kitsu.category == "SHOT"


def active_project_row(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    project_active = cache.project_active_get()
    row = layout.row(align=True)

    if not project_active:
        row.enabled = False
    return row


def active_episode_row(layout: bpy.types.UILayout) -> None:
    episode_active = cache.episode_active_get()
    project_active = cache.project_active_get()
    row = active_project_row(layout)
    if project_active.production_type == bkglobals.KITSU_TV_PROJECT and not episode_active:
        row.enabled = False
    return row


def draw_episode_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_project_row(layout)
    row.prop(context.scene.kitsu, "episode_active_name")


def draw_sequence_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_episode_row(layout)
    row.prop(context.scene.kitsu, "sequence_active_name")


def draw_asset_type_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_project_row(layout)
    row.prop(context.scene.kitsu, "asset_type_active_name")


def draw_shot_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_episode_row(layout)
    row.prop(context.scene.kitsu, "shot_active_name")


def draw_asset_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_project_row(layout)
    row.prop(context.scene.kitsu, "asset_active_name")


def draw_edit_selector(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    row = active_project_row(layout)
    row.prop(context.scene.kitsu, "edit_active_name")


def draw_task_type_selector(context: bpy.types.Context, layout: bpy.types.UILayout):
    layout.prop(context.scene.kitsu, "task_type_active_name")
