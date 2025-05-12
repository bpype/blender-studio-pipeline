# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import opsdata
import bpy

from pathlib import Path

from .. import prefs, cache, ui
from .ops import (
    KITSU_OT_anim_quick_duplicate,
    KITSU_OT_anim_check_action_names,
    KITSU_OT_anim_update_output_coll,
)
from ..generic.ops import KITSU_OT_open_path


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
            # HACK to accomodate custom task types @ blender studio (Anim3D, Anim2D)
            and cache.task_type_active_get().name in ['Animation', 'Layout', 'Anim3D', 'Anim2D']
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # Scene operators.
        box = layout.box()
        box.label(text="Scene", icon="SCENE_DATA")

        col = box.column(align=True)
        col.operator("kitsu.push_frame_range", icon="TRIA_UP")
        col.operator(
            "kitsu.pull_frame_range",
            icon="TRIA_DOWN",
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

        row = box.row(align=True)
        row.operator("kitsu.anim_enforce_naming_convention", icon="SORTALPHA")


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
