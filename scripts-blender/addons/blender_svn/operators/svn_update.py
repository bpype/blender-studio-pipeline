# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Set

import bpy
from bpy.types import Operator, Context
from bpy.props import IntProperty

from .simple_commands import May_Modifiy_Current_Blend
from ..threaded.background_process import Processes
from ..util import get_addon_prefs


class SVN_OT_update_all(May_Modifiy_Current_Blend, Operator):
    bl_idname = "svn.update_all"
    bl_label = "SVN Update All"
    bl_description = "Download all the latest updates from the remote repository"
    bl_options = {'INTERNAL'}

    revision: IntProperty(
        name="Revision",
        description="Which revision to revert the repository to. 0 means to update to the latest version instead",
        default=0
    )

    @classmethod
    def poll(cls, context):
        if get_addon_prefs(context).is_busy:
            # Don't allow attempting to Update/Commit while either is still running.
            return False

        repo = context.scene.svn.get_repo(context)
        if not repo:
            return False
        for f in repo.external_files:
            if f.repos_status != 'none':
                return True

        return True

    def invoke(self, context, event):
        repo = context.scene.svn.get_repo(context)
        current_blend = repo.current_blend_file
        if self.revision == 0:
            if current_blend and current_blend.repos_status != 'none':
                # If the current file will be modified, warn user.
                self.file_rel_path = current_blend.svn_path
                return context.window_manager.invoke_props_dialog(self, width=500)
        else:
            for f in repo.external_files:
                if f.status in ['modified', 'added', 'conflicted', 'deleted', 'missing', 'unversioned']:
                    # If user wants to check out an older version of the repo but 
                    # there are uncommitted local changes to any files, warn user.
                    return context.window_manager.invoke_props_dialog(self, width=500)

        return self.execute(context)

    def draw(self, context):
        if self.revision != 0:
            layout = self.layout
            col = layout.column()
            col.label(text="You have uncommitted local changes.")
            col.label(
                text="These won't be lost, but if you want to revert the state of the entire local repository to a ")
            col.label(
                text="past point in time, you would get a better result if you reverted or committed your changes first.")
            col.separator()
            col.label(
                text="Press OK to proceed anyways. Click out of this window to cancel.")
        super().draw(context)

    def execute(self, context: Context) -> Set[str]:
        Processes.stop('Status')
        if self.reload_file:
            current_file = context.scene.svn.get_repo(context).current_blend_file
            command = ["svn", "up", current_file.svn_path, "--accept", "postpone"]
            if self.revision > 0:
                command.insert(2, f"-r{self.revision}")
            self.execute_svn_command(
                context,
                command,
                use_cred=True
            )
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=False)
            Processes.start('Log')

        Processes.start('Update', revision=self.revision)

        return {"FINISHED"}


registry = [
    SVN_OT_update_all,
]
