# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Panel
from bl_ui.space_filebrowser import FileBrowserPanel

from .ui_log import draw_svn_log, is_log_useful
from .ui_file_list import draw_file_list
from ..util import get_addon_prefs

class FILEBROWSER_PT_SVN_files(FileBrowserPanel, Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = "SVN Files"

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        prefs = get_addon_prefs(context)
        return prefs.active_repo and prefs.active_repo.authenticated

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        draw_file_list(context, layout)


class FILEBROWSER_PT_SVN_log(FileBrowserPanel, Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_parent_id = "FILEBROWSER_PT_SVN_files"
    bl_label = "Revision History"

    @classmethod
    def poll(cls, context):
        if not super().poll(context):
            return False

        return is_log_useful(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        draw_svn_log(context, layout)


registry = [
    FILEBROWSER_PT_SVN_files,
    FILEBROWSER_PT_SVN_log
]
