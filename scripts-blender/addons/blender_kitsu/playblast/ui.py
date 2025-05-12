# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..anim import opsdata
from ..context import core as context_core
import bpy

from pathlib import Path

from .. import prefs, cache, ui
from ..playblast.ops import (
    KITSU_OT_playblast_create,
    KITSU_OT_playblast_set_version,
    KITSU_OT_playblast_increment_playblast_version,
)
from ..generic.ops import KITSU_OT_open_path


class KITSU_PT_vi3d_playblast(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for animation
    tasks, e.G playblast
    """

    bl_category = "Kitsu"
    bl_label = "Playblast"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context_core.is_edit_context():
            return False
        return bool(prefs.session_auth(context))

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)

        return bool(not addon_prefs.is_playblast_root_valid or not context.scene.camera)

    def draw_error(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout

        box = ui.draw_error_box(layout)
        if not addon_prefs.is_playblast_root_valid:
            ui.draw_error_invalid_playblast_root_dir(box)
        if not context.scene.camera:
            ui.draw_error_no_active_camera(box)

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        split_factor_small = 0.95

        # ERROR.
        if self.poll_error(context):
            self.draw_error(context)

        # Playblast version op.
        row = layout.row(align=True)
        row.operator(
            KITSU_OT_playblast_set_version.bl_idname,
            text=context.scene.kitsu.playblast_version,
            icon="DOWNARROW_HLT",
        )
        # Playblast increment version op.
        row.operator(
            KITSU_OT_playblast_increment_playblast_version.bl_idname,
            text="",
            icon="ADD",
        )

        # Playblast op.
        row = layout.row(align=True)
        row.operator(KITSU_OT_playblast_create.bl_idname, icon="RENDER_ANIMATION")

        # Playblast path label.
        if Path(context.scene.kitsu.playblast_file).exists():
            split = layout.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.playblast_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file
        else:
            row = layout.row(align=True)
            row.label(text=context.scene.kitsu.playblast_file)
            row.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file


class KITSU_PT_seq_playblast(KITSU_PT_vi3d_playblast):
    bl_space_type = "SEQUENCE_EDITOR"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context_core.is_sequence_context():
            return False
        return bool(prefs.session_auth(context))


classes = (KITSU_PT_seq_playblast, KITSU_PT_vi3d_playblast)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
