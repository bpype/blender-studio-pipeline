# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from blender_kitsu.anim import opsdata
import bpy

from pathlib import Path

from blender_kitsu import prefs, cache, ui
from blender_kitsu.anim.ops import (
    KITSU_OT_anim_create_playblast,
    KITSU_OT_anim_set_playblast_version,
    KITSU_OT_anim_increment_playblast_version,
    KITSU_OT_anim_pull_frame_range,
    KITSU_OT_anim_quick_duplicate,
    KITSU_OT_anim_check_action_names,
    KITSU_OT_anim_update_output_coll,
)
from blender_kitsu.generic.ops import KITSU_OT_open_path


class KITSU_PT_vi3d_anim_tools(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for animation
    tasks, e.G playblast
    """

    bl_category = "Kitsu"
    bl_label = "Animation Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
            and cache.task_type_active_get().name == "Animation"
        )

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)

        return bool(
            context.scene.kitsu_error.frame_range
            or not addon_prefs.is_playblast_root_valid
            or not context.scene.camera
        )

    def draw_error(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout

        box = ui.draw_error_box(layout)
        if context.scene.kitsu_error.frame_range:
            ui.draw_error_frame_range_outdated(box)
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

        # Playblast box.
        box = layout.box()
        box.label(text="Playblast")

        # Playlast version op.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_set_playblast_version.bl_idname,
            text=context.scene.kitsu.playblast_version,
            icon="DOWNARROW_HLT",
        )
        # Playblast increment version op.
        row.operator(
            KITSU_OT_anim_increment_playblast_version.bl_idname,
            text="",
            icon="ADD",
        )

        # Playblast op.
        row = box.row(align=True)
        row.operator(KITSU_OT_anim_create_playblast.bl_idname, icon="RENDER_ANIMATION")

        # Playblast path label.
        if Path(context.scene.kitsu.playblast_file).exists():
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.playblast_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file
        else:
            row = box.row(align=True)
            row.label(text=context.scene.kitsu.playblast_file)
            row.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file

        # Scene operators.
        box = layout.box()
        box.label(text="Scene", icon="SCENE_DATA")

        # Pull frame range.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_pull_frame_range.bl_idname,
            icon="FILE_REFRESH",
        )

        # Update output collection.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_update_output_coll.bl_idname,
            icon="FILE_REFRESH",
        )

        # Quick duplicate.
        act_coll = context.view_layer.active_layer_collection.collection
        dupli_text = "Duplicate: Select Collection"

        if act_coll:
            dupli_text = f"Duplicate: {act_coll.name}"

        if act_coll and opsdata.is_item_local(act_coll):
            dupli_text = f"Duplicate: Select Overwritten Collection"

        split = box.split(factor=0.85, align=True)
        split.operator(
            KITSU_OT_anim_quick_duplicate.bl_idname, icon="DUPLICATE", text=dupli_text
        )
        split.prop(context.window_manager.kitsu, "quick_duplicate_amount", text="")

        # Check action names.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_anim_check_action_names.bl_idname,
            icon="ACTION",
            text="Check Action Names",
        )


# ---------REGISTER ----------.

classes = [
    KITSU_PT_vi3d_anim_tools,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
