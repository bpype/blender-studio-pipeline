# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .ops import (
    CS_OT_make_contactsheet,
    CS_OT_exit_contactsheet,
)
from . import opsdata


class CS_PT_contactsheet(bpy.types.Panel):
    """ """

    bl_category = "Contactsheet"
    bl_label = "Contactsheet"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Return opsdata.poll_make_contactsheet(context).
        return True

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # Handle case if scene is contactsheet.
        if context.scene.contactsheet.is_contactsheet:
            # Exit contact sheet.
            row = layout.row(align=True)
            row.operator(CS_OT_exit_contactsheet.bl_idname, icon="X")
            return

        # Make contact sheet.
        row = layout.row(align=True)

        strips = context.selected_strips
        if not strips:
            valid_strips = opsdata.get_top_level_valid_strips_continuous(context)
        else:
            valid_strips = opsdata.get_valid_cs_strips(strips)

        text = f"Make Contactsheet with {len(valid_strips)} strips"

        row.operator(CS_OT_make_contactsheet.bl_idname, icon="MESH_GRID", text=text)
        icon = "UNLOCKED" if context.scene.contactsheet.use_custom_rows else "LOCKED"
        row.prop(context.scene.contactsheet, "use_custom_rows", text="", icon=icon)

        if context.scene.contactsheet.use_custom_rows:
            layout.row(align=True).prop(context.scene.contactsheet, "rows")

        # Contact sheet resolution.
        row = layout.row(align=True)
        row.prop(context.scene.contactsheet, "contactsheet_x", text="X")
        row.prop(context.scene.contactsheet, "contactsheet_y", text="Y")


# ----------------REGISTER--------------.

classes = [
    CS_PT_contactsheet,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
