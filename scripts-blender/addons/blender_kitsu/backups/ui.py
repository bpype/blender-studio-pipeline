# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .ops import KITSU_OT_save_backup_version, KITSU_OT_open_backups_folder
from ..util import addon_prefs_get

class KITSU_PT_version_backups(bpy.types.Panel):
    
    bl_category = "Kitsu"
    bl_label = "Backups"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50
    bl_parent_id = "KITSU_PT_vi3d_playblast"

    @classmethod
    def poll(self, context):
        addon_prefs = addon_prefs_get(bpy.context)
        if addon_prefs.version_control:
            return False
        return True
    
    def draw(self, context):
        self.layout.operator(KITSU_OT_save_backup_version.bl_idname, icon="ADD", text="Save Backup Version")
        self.layout.operator(KITSU_OT_open_backups_folder.bl_idname, icon="FILE_FOLDER", text="Open Backups Folder")

# ---------REGISTER ----------.

# Classes that inherit from another need to be registered first for some reason.
classes = [
    KITSU_PT_version_backups,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
