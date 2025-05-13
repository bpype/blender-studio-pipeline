# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import prefs, ui
from ..context import core as context_core
from pathlib import Path
from .ops import (
    KITSU_OT_edit_export_set_version,
    KITSU_OT_edit_export_increment_version,
    KITSU_OT_edit_export_publish,
    KITSU_OT_edit_export_import_latest,
)
from ..generic.ops import KITSU_OT_open_path


class KITSU_PT_edit_export_publish(bpy.types.Panel):
    """
    Panel in sequence editor that exposes a set of tools that are used to export latest edit
    """

    bl_category = "Kitsu"
    bl_label = "Export & Publish"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context_core.is_edit_context())

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        split_factor_small = 0.95

        # # ERROR.
        if not addon_prefs.is_edit_export_root_valid:
            box = ui.draw_error_box(layout)
            ui.draw_error_invalid_edit_export_root_dir(box)

        # Edit Export version op.
        row = layout.row(align=True)
        row.operator(
            KITSU_OT_edit_export_set_version.bl_idname,
            text=context.scene.kitsu.edit_export_version,
            icon="DOWNARROW_HLT",
        )
        # Edit Export increment version op.
        row.operator(
            KITSU_OT_edit_export_increment_version.bl_idname,
            text="",
            icon="ADD",
        )

        # Edit Export op.
        row = layout.row(align=True)
        row.operator(KITSU_OT_edit_export_publish.bl_idname, icon="RENDER_ANIMATION")

        # Edit Export path label.
        if Path(context.scene.kitsu.edit_export_file).exists():
            split = layout.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.edit_export_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.edit_export_file
        else:
            row = layout.row(align=True)
            row.label(text=context.scene.kitsu.edit_export_file)
            row.operator(KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text="").filepath = (
                context.scene.kitsu.edit_export_file
            )


class KITSU_PT_edit_export_tools(bpy.types.Panel):
    """
    Panel in sequence editor that exposes a set of tools that are used to load the latest edit
    """

    bl_category = "Kitsu"
    bl_label = "General Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            return False

        if not (context_core.is_sequence_context() or context_core.is_shot_context()):
            return False
        return True

    def draw(self, context: bpy.types.Context) -> None:
        box = self.layout.box()
        box.label(text="General", icon="MODIFIER")
        box.operator(KITSU_OT_edit_export_import_latest.bl_idname)


classes = [KITSU_PT_edit_export_publish, KITSU_PT_edit_export_tools]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
