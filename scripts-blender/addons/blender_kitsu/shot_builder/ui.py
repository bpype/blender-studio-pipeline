# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Header, Menu, Panel

from bpy.app.translations import (
    pgettext_iface as iface_,
    contexts as i18n_contexts,
)


from typing import Any


def topbar_file_new_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    layout.operator("kitsu.build_new_shot", text="Shot File")
    layout.operator("kitsu.build_new_asset", text="Asset File")
    layout.operator("kitsu.create_edit_file", text="Edit File")
    layout.separator()


def topbar_kitsu_menu_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    layout.menu("KITSU_MT_project_topbar_menu")


class KITSU_MT_project_topbar_menu(Menu):
    bl_label = "Project"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("kitsu.build_new_shot", text="New Shot")
        layout.operator("kitsu.build_new_asset", text="New Asset")
        layout.operator("kitsu.create_edit_file", text="New Edit")
        layout.separator()
        layout.operator("kitsu.open_shot_file", text="Open Shot")
        layout.operator("kitsu.open_asset_file", text="Open Asset")
        layout.operator("kitsu.open_edit_file", text="Open Edit")
        layout.separator()
        layout.operator("kitsu.con_detect_context")


classes = [
    KITSU_MT_project_topbar_menu,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_new.prepend(topbar_file_new_draw_handler)
    bpy.types.TOPBAR_MT_editor_menus.append(topbar_kitsu_menu_draw_handler)


def unregister():
    bpy.types.TOPBAR_MT_file_new.remove(topbar_file_new_draw_handler)
    bpy.types.TOPBAR_MT_editor_menus.append(topbar_kitsu_menu_draw_handler)

    for cls in classes:
        bpy.utils.unregister_class(cls)
