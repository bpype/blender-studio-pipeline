# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import bpy

from .. import prefs, lookdev, ui, cache
from .ops import (
    KITSU_OT_lookdev_set_preset,
    KITSU_OT_lookdev_apply_preset,
)
from . import opsdata


class KITSU_PT_vi3d_lookdev_tools(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for general tasks
    """

    bl_category = "Kitsu"
    bl_label = "Lookdev Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 60

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            cache.task_type_active_get().name
            in ["Lighting", "Rendering", "Compositing"]
        )

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(not addon_prefs.lookdev.is_presets_dir_valid)

    def draw_error(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        box = ui.draw_error_box(layout)

        if not addon_prefs.lookdev.is_presets_dir_valid:
            ui.draw_error_invalid_render_preset_dir(box)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        if self.poll_error(context):
            self.draw_error(context)

        box = layout.box()
        box.label(text="Render Settings", icon="RESTRICT_RENDER_OFF")

        # Render settings.
        row = box.row(align=True)
        rdpreset_text = "Select Render Preset"
        if context.scene.lookdev.preset_file:
            try:
                rdpreset_text = opsdata._rd_preset_data_dict[
                    Path(context.scene.lookdev.preset_file).name
                ]
            except KeyError:
                pass

        row.operator(
            KITSU_OT_lookdev_set_preset.bl_idname,
            text=rdpreset_text,
            icon="DOWNARROW_HLT",
        )
        row.operator(
            KITSU_OT_lookdev_apply_preset.bl_idname,
            text="",
            icon="PLAY",
        )


class KITSU_PT_comp_lookdev_tools(KITSU_PT_vi3d_lookdev_tools):
    bl_space_type = "NODE_EDITOR"


# ---------REGISTER ----------
# Classes that inherit from another need to be registered first for some reason.
classes = [KITSU_PT_comp_lookdev_tools, KITSU_PT_vi3d_lookdev_tools]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
