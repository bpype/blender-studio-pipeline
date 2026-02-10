# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import bpy
import subprocess
import os
import platform
from .core import save_disk_version_backup_file, get_disk_version_folder


class KITSU_OT_save_backup_version(bpy.types.Operator):
    """Save a new backup version"""
    bl_idname = "kitsu.save_backup_version"
    bl_label = "Save Incremental Backup"
    bl_description = "Saves an incremental version backup of the current .blend file to the `version_backups` folder. To save a major version number use Playblast"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        kitsu_props = context.scene.kitsu    
        version_filename = save_disk_version_backup_file(kitsu_props.playblast_version)
        if version_filename:
            self.report({"INFO"}, f"Backup version {version_filename.stem} saved successfully")
        else:
            self.report({"ERROR"}, "Failed to save backup version")
            return {"CANCELLED"}
        return {"FINISHED"}
    
class KITSU_OT_open_backups_folder(bpy.types.Operator):
    """Open the backups folder"""
    bl_idname = "kitsu.open_backups_folder"
    bl_label = "Open Backups Folder"
    bl_description = "Opens the folder where backup versions are saved in the system file browser"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        folder = get_disk_version_folder()
        
        # Ensure the folder exists
        if not folder.exists():
            self.report({"ERROR"}, f"Backups folder does not exist: {folder}")
            return {"CANCELLED"}
        
        # Open folder in system file browser
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", str(folder)])
            else:  # Linux and others
                # Use Popen to avoid blocking/freezing
                subprocess.Popen(["xdg-open", str(folder)], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            self.report({"INFO"}, f"Opened backups folder: {folder}")
            
        except Exception as e:
            self.report({"ERROR"}, f"Failed to open folder: {str(e)}")
            return {"CANCELLED"}
        
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
    KITSU_OT_save_backup_version,
    KITSU_OT_open_backups_folder,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
