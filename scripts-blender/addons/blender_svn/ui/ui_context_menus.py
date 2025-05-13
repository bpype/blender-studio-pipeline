# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Context, UIList, Operator
from bpy.props import StringProperty, BoolProperty
from pathlib import Path


def check_context_match(context: Context, uilayout_type: str, bl_idname: str) -> bool:
    """For example, when right-clicking on a UIList, the uilayout_type will 
    be `ui_list` and the bl_idname is that of the UIList being right-clicked.
    """
    uilayout = getattr(context, uilayout_type, None)
    return uilayout and uilayout.bl_idname == bl_idname


def svn_file_list_context_menu(self: UIList, context: Context) -> None:
    if not check_context_match(context, 'ui_list', 'SVN_UL_file_list'):
        return

    layout = self.layout
    layout.separator()
    repo = context.scene.svn.get_repo(context)
    active_file = repo.active_file
    file_abs_path = repo.get_file_abspath(active_file)
    if active_file.name.endswith("blend"):
        op = layout.operator("wm.open_mainfile",
                        text=f"Open {active_file.name}")
        op.filepath = str(file_abs_path)
        op.display_file_selector = False
        op.load_ui = True
        op = layout.operator("wm.open_mainfile",
                        text=f"Open {active_file.name} (Keep UI)")
        op.filepath = str(file_abs_path)
        op.display_file_selector = False
        op.load_ui = False

    else:
        layout.operator("wm.path_open",
                        text=f"Open {active_file.name}").filepath = str(file_abs_path)
    layout.operator("wm.path_open",
                    text=f"Open Containing Folder").filepath = Path(file_abs_path).parent.as_posix()
    layout.separator()


def svn_log_list_context_menu(self: UIList, context: Context) -> None:
    if not check_context_match(context, 'ui_list', 'SVN_UL_log'):
        return

    layout = self.layout
    layout.separator()

    repo = context.scene.svn.get_repo(context)
    active_log = repo.active_log
    layout.operator("svn.update_all",
                    text=f"Revert Repository To r{active_log.revision_number}").revision = active_log.revision_number
    layout.separator()


def register():
    bpy.types.UI_MT_list_item_context_menu.append(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.append(svn_log_list_context_menu)


def unregister():
    bpy.types.UI_MT_list_item_context_menu.remove(svn_file_list_context_menu)
    bpy.types.UI_MT_list_item_context_menu.remove(svn_log_list_context_menu)

