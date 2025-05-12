# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from typing import Set, Union, Optional, List, Dict, Any

import bpy

from .ops import (
    RR_OT_sqe_create_review_session,
    RR_OT_setup_review_workspace,
    RR_OT_sqe_inspect_exr_sequence,
    RR_OT_sqe_clear_exr_inspect,
    RR_OT_sqe_approve_render,
    RR_OT_sqe_update_sequence_statuses,
    RR_OT_open_path,
    RR_OT_sqe_push_to_edit,
)
from . import opsdata
from .. import prefs


class RR_PT_render_review(bpy.types.Panel):
    """ """

    bl_category = "Render Review"
    bl_label = "Render Review"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:

        addon_prefs = prefs.addon_prefs_get(context)

        # Create box.
        layout = self.layout
        box = layout.box()

        # Label and setup workspace.
        row = box.row(align=True)
        row.label(text="Review", icon="CAMERA_DATA")
        row.operator(RR_OT_setup_review_workspace.bl_idname, text="", icon="WINDOW")

        # Render dir prop.
        row = box.row(align=True)
        row.prop(context.scene.rr, "render_dir")

        # Create session.
        render_dir = context.scene.rr.render_dir_path
        text = f"Invalid Render Directory"
        if render_dir:
            if opsdata.is_sequence_dir(render_dir):
                text = f"Review Sequence: {render_dir.name}"
            elif opsdata.is_shot_dir(render_dir):
                text = f"Review Shot: {render_dir.stem}"

        row = box.row(align=True)
        row.operator(RR_OT_sqe_create_review_session.bl_idname, text=text, icon="PLAY")
        row = box.row(align = True)
        row.prop(addon_prefs, 'match_latest_length')
        row = box.row(align=True)
        row.prop(addon_prefs, 'use_video')
        if addon_prefs.use_video:
            row.prop(addon_prefs, 'use_video_latest_only')
        row = box.row(align = False)
        row.prop(addon_prefs, 'shot_name_filter')

        # Warning if kitsu on but not logged in.
        if not prefs.session_auth(context):
            row = box.split(align=True, factor=0.7)
            row.label(text="Kitsu enabled but not logged in", icon="ERROR")
            row.operator("kitsu.session_start", text="Login")

        elif not opsdata.is_active_project():
            row = box.row(align=True)
            row.label(text="Kitsu enabled but no active project", icon="ERROR")

        sqe = context.scene.sequence_editor
        if not sqe:
            return
        active_strip = sqe.active_strip
        if active_strip and active_strip.rr.is_render:
            # Create box.
            layout = self.layout
            box = layout.box()
            box.label(text=f"Render: {active_strip.rr.shot_name}", icon="RESTRICT_RENDER_OFF")
            box.separator()

            # Render dir name label and open file op.
            row = box.row(align=True)
            directory = opsdata.get_strip_folder(active_strip)
            row.label(text=f"Folder: {directory.name}")
            row.operator(
                RR_OT_open_path.bl_idname, icon="FILEBROWSER", text="", emboss=False
            ).filepath = bpy.path.abspath(directory.as_posix())

            # Nr of frames.
            box.row(align=True).label(text=f"Frames: {active_strip.rr.frames_found_text}")

            # Inspect exr.
            text = "Inspect EXR"
            icon = "VIEWZOOM"
            if not opsdata.get_image_editor(context):
                text = "Inspect EXR: Needs Image Editor"
                icon = "ERROR"

            row = box.row(align=True)
            row.operator(RR_OT_sqe_inspect_exr_sequence.bl_idname, icon=icon, text=text)
            row.operator(RR_OT_sqe_clear_exr_inspect.bl_idname, text="", icon="X")

            # Approve render & udpate approved.
            row = box.row(align=True)

            text = "Push To Edit & Approve Render"
            if active_strip.rr.is_pushed_to_edit:
                text = "Approve Render"
            row.operator(RR_OT_sqe_approve_render.bl_idname, icon="CHECKMARK", text=text)
            row.operator(RR_OT_sqe_update_sequence_statuses.bl_idname, text="", icon="FILE_REFRESH")

            # Push to edit.
            if not addon_prefs.shot_playblast_root_dir:
                shot_previews_dir = ""  # ops handle invalid path
            else:
                shot_previews_dir = Path(opsdata.get_shot_previews_path(active_strip)).as_posix()

            row = box.row(align=True)
            row.operator(RR_OT_sqe_push_to_edit.bl_idname, icon="EXPORT")
            row.operator(RR_OT_open_path.bl_idname, icon="FILEBROWSER", text="").filepath = (
                shot_previews_dir
            )

            # Push strip to Kitsu.
            box.row().operator('kitsu.sqe_push_shot', icon='URL')


def RR_topbar_file_new_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    op = layout.operator(RR_OT_setup_review_workspace.bl_idname, text="Render Review")


# ----------------REGISTER--------------.

classes = [
    RR_PT_render_review,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Append to topbar file new.
    bpy.types.TOPBAR_MT_file_new.append(RR_topbar_file_new_draw_handler)


def unregister():

    # Remove to topbar file new.
    bpy.types.TOPBAR_MT_file_new.remove(RR_topbar_file_new_draw_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
