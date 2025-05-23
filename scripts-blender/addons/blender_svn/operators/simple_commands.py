# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, BoolProperty
from bpy.types import Context, Operator

from send2trash import send2trash

from ..threaded.execute_subprocess import execute_svn_command
from ..threaded.background_process import Processes
from ..util import get_addon_prefs, redraw_viewport


class SVN_Operator:
    @staticmethod
    def update_file_list(context):
        repo = context.scene.svn.get_repo(context)
        repo.refresh_ui_lists(context)

    def execute_svn_command(self, context, command: List[str], use_cred=False) -> str:
        # Since a status update might already be being requested when an SVN operator is run,
        # we want to ignore the first update after any SVN operator.
        # Otherwise it can result in a predicted state being overwritten by an outdated state.
        # For example, the Commit operator sets a file to "Normal" state, then the old svn status
        # arrives and sets it back to "Modified" state, which it isn't anymore.
        return execute_svn_command(context, command, use_cred=use_cred)


class SVN_Operator_Single_File(SVN_Operator):
    """Base class for SVN operators operating on a single file."""

    file_rel_path: StringProperty()

    # Flag to differentiate operators that require that the file exists pre-execute.
    missing_file_allowed = False

    def execute(self, context: Context) -> Set[str]:
        if not self.file_exists(context) and not type(self).missing_file_allowed:
            # If the operator requires the file to exist and it doesn't, cancel.
            self.report(
                {'ERROR'},
                f'File is no longer on the file system: "{self.file_rel_path}"',
            )
            return {'CANCELLED'}

        status = Processes.get('Status')
        if status:
            Processes.kill('Status')
        ret = self._execute(context)

        file = self.get_file(context)
        Processes.start('Status')
        redraw_viewport()

        self.update_file_list(context)
        return ret

    def _execute(self, context: Context) -> Set[str]:
        raise NotImplementedError

    def get_file_full_path(self, context) -> Path:
        repo = context.scene.svn.get_repo(context)
        return Path.joinpath(Path(repo.directory), Path(self.file_rel_path))

    def get_file(self, context) -> "SVN_file":
        repo = context.scene.svn.get_repo(context)
        return repo.external_files.get(self.file_rel_path)

    def file_exists(self, context) -> bool:
        exists = self.get_file_full_path(context).exists()
        if not exists and not type(self).missing_file_allowed:
            self.report({'INFO'}, "File was not found, cancelling.")
        return exists

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        return


class Popup_Operator:
    popup_width = 400

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(
            self, width=type(self).popup_width
        )


class Warning_Operator(Popup_Operator):
    def draw(self, context):
        layout = self.layout.column(align=True)

        warning = self.get_warning_text(context)
        for line in warning.split("\n"):
            row = layout.row()
            row.alert = True
            row.label(text=line)

    def get_warning_text(self, context):
        raise NotImplemented


class May_Modifiy_Current_Blend(SVN_Operator_Single_File, Warning_Operator):
    def file_is_current_blend(self, context) -> bool:
        current_blend = context.scene.svn.get_repo(context).current_blend_file
        return current_blend and current_blend.svn_path == self.file_rel_path

    set_outdated_flag = True

    reload_file: BoolProperty(
        name="Reload File (Keep UI)",
        description="Reload the file after the operation is completed. The UI layout will be preserved",
        default=False,
    )

    def invoke(self, context, event):
        self.reload_file = False
        if self.file_is_current_blend(context) or self.get_warning_text(context):
            return context.window_manager.invoke_props_dialog(self, width=500)

        return self.execute(context)

    def get_warning_text(self, context):
        if self.file_is_current_blend(context):
            return "This will modify the currently opened .blend file."
        return ""

    def draw(self, context):
        super().draw(context)
        if self.file_is_current_blend(context):
            self.layout.prop(self, 'reload_file')

    def execute(self, context):
        super().execute(context)
        if self.reload_file:
            bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath, load_ui=False)
        elif self.file_is_current_blend(context) and self.set_outdated_flag:
            context.scene.svn.file_is_outdated = True
        return {'FINISHED'}


class SVN_OT_update_single(May_Modifiy_Current_Blend, Operator):
    bl_idname = "svn.update_single"
    bl_label = "Update File"
    bl_description = (
        "Download the latest available version of this file from the remote repository"
    )
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def _execute(self, context: Context) -> Set[str]:
        self.will_conflict = False
        repo = context.scene.svn.get_repo(context)
        file_entry = repo.external_files.get(self.file_rel_path)
        if file_entry.status not in ['normal', 'none']:
            self.will_conflict = True

        self.execute_svn_command(
            context,
            ["svn", "up", f"{self.file_rel_path}", "--accept", "postpone"],
            use_cred=True,
        )

        self.report({'INFO'}, f'Updated "{self.file_rel_path}" to the latest version.')

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        if self.will_conflict:
            file_entry.status = 'conflicted'
        else:
            file_entry.status = 'normal'
            file_entry.repos_status = 'none'

        return {"FINISHED"}


class SVN_OT_download_file_revision(May_Modifiy_Current_Blend, Operator):
    bl_idname = "svn.download_file_revision"
    bl_label = "Download Revision"
    bl_description = "Download this revision of this file"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    revision: IntProperty(default=0)

    def invoke(self, context, event):
        repo = context.scene.svn.get_repo(context)
        file_entry = repo.external_files.get(self.file_rel_path)
        if self.file_is_current_blend(context) and file_entry.status != 'normal':
            self.report(
                {'ERROR'}, 'You must first revert or commit the changes to this file.'
            )
            return {'CANCELLED'}
        return super().invoke(context, event)

    def _execute(self, context: Context) -> Set[str]:
        repo = context.scene.svn.get_repo(context)
        file_entry = repo.external_files.get(self.file_rel_path)
        if file_entry.status == 'modified':
            # If file has local modifications, let's avoid a conflict by cancelling
            # and telling the user to resolve it in advance.
            self.report(
                {'ERROR'},
                "Cancelled: You have local modifications to this file. You must revert or commit it first!",
            )
            return {'CANCELLED'}

        self.svn_download_file_revision(context, self.file_rel_path, self.revision)

        self.report(
            {'INFO'}, f"Checked out revision {self.revision} of {self.file_rel_path}"
        )

        return {"FINISHED"}

    def svn_download_file_revision(self, context, svn_file_path: str, revision=0):
        commands = ["svn", "up", f"{self.file_rel_path}", "--accept", "postpone"]
        if self.revision > 0:
            commands.insert(2, f"-r{self.revision}")

        self.execute_svn_command(context, commands, use_cred=True)

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        file_entry['revision'] = self.revision
        latest_rev = repo.get_latest_revision_of_file(self.file_rel_path)
        if latest_rev == self.revision:
            file_entry.status = 'normal'
            file_entry.repos_status = 'none'
        else:
            file_entry.status = 'normal'
            file_entry.repos_status = 'modified'


class SVN_OT_restore_file(May_Modifiy_Current_Blend, Operator):
    bl_idname = "svn.restore_file"
    bl_label = "Restore File"
    bl_description = "Restore this deleted file to its previously checked out revision"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def svn_revert(self, context, svn_file_path):
        self.execute_svn_command(context, ["svn", "revert", f"{svn_file_path}"])

    def _execute(self, context: Context) -> Set[str]:
        self.svn_revert(context, self.file_rel_path)
        return {"FINISHED"}

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        file_entry.status = 'normal'


class SVN_OT_revert_file(SVN_OT_restore_file):
    bl_idname = "svn.revert_file"
    bl_label = "Revert File"
    bl_description = "PERMANENTLY DISCARD local changes to this file and return it to the state of the last local revision. Cannot be undone"
    bl_options = {'INTERNAL'}

    missing_file_allowed = False

    def get_warning_text(self, context) -> str:
        return (
            "You will irreversibly and permanently lose the changes you've made to this file:\n    "
            + self.file_rel_path
        )


class SVN_OT_revert_and_update(SVN_OT_download_file_revision, SVN_OT_revert_file):
    """Convenience operator for the "This file is outdated" warning message. Normally, these two operations should be done separately!"""

    bl_idname = "svn.revert_and_update_file"
    bl_label = "Revert And Update File"
    bl_description = "A different version of this file was downloaded while it was open. This warning will persist until the file is updated and reloaded, or committed. Click to PERMANENTLY DISCARD local changes to this file and update it to the latest revision. Cannot be undone"
    bl_options = {'INTERNAL'}

    missing_file_allowed = False

    def invoke(self, context, event):
        return super(May_Modifiy_Current_Blend, self).invoke(context, event)

    def get_warning_text(self, context) -> str:
        if self.get_file(context).status != 'normal':
            return (
                "You will irreversibly and permanently lose the changes you've made to this file:\n    "
                + self.file_rel_path
            )
        else:
            return "File will be updated to latest revision."

    def _execute(self, context: Context) -> Set[str]:
        self.svn_revert(context, self.file_rel_path)
        self.svn_download_file_revision(context, self.file_rel_path, self.revision)

        return {"FINISHED"}


class SVN_OT_add_file(SVN_Operator_Single_File, Operator):
    bl_idname = "svn.add_file"
    bl_label = "Add File"
    bl_description = (
        "Mark this file for addition to the remote repository. It can then be committed"
    )
    bl_options = {'INTERNAL'}

    def _execute(self, context: Context) -> Set[str]:
        result = self.execute_svn_command(
            context, ["svn", "add", f"{self.file_rel_path}"]
        )

        if result:
            f = self.get_file(context)
        return {"FINISHED"}

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        file_entry.status = 'added'


class SVN_OT_unadd_file(SVN_Operator_Single_File, Operator):
    bl_idname = "svn.unadd_file"
    bl_label = "Un-Add File"
    bl_description = "Un-mark this file as being added to the remote repository. It will not be committed"
    bl_options = {'INTERNAL'}

    def _execute(self, context: Context) -> Set[str]:
        self.execute_svn_command(
            context, ["svn", "rm", "--keep-local", f"{self.file_rel_path}"]
        )

        return {"FINISHED"}

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        file_entry.status = 'unversioned'


class SVN_OT_trash_file(SVN_Operator_Single_File, Warning_Operator, Operator):
    bl_idname = "svn.trash_file"
    bl_label = "Trash File"
    bl_description = "Move this file to the recycle bin"
    bl_options = {'INTERNAL'}

    file_rel_path: StringProperty()
    missing_file_allowed = False

    def get_warning_text(self, context):
        return (
            "Are you sure you want to move this file to the recycle bin?\n    "
            + self.file_rel_path
        )

    def _execute(self, context: Context) -> Set[str]:
        send2trash([self.get_file_full_path(context)])

        f = self.get_file(context)
        # Since this operator is only available for Unversioned files,
        # we want to remove the file entry when removing the file.
        context.scene.svn.get_repo(context).remove_file_entry(f)
        return {"FINISHED"}


class SVN_OT_remove_file(SVN_Operator_Single_File, Warning_Operator, Operator):
    bl_idname = "svn.remove_file"
    bl_label = "Remove File"
    bl_description = "Mark this file for removal from the remote repository"
    bl_options = {'INTERNAL'}

    missing_file_allowed = True

    def get_warning_text(self, context):
        return (
            "This file will be deleted for everyone:\n    "
            + self.file_rel_path
            + "\nAre you sure?"
        )

    def _execute(self, context: Context) -> Set[str]:
        self.execute_svn_command(context, ["svn", "remove", f"{self.file_rel_path}"])

        return {"FINISHED"}

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        file_entry.status = 'deleted'


class SVN_OT_resolve_conflict(May_Modifiy_Current_Blend, Operator):
    bl_idname = "svn.resolve_conflict"
    bl_label = "Resolve Conflict"
    bl_description = "Resolve a conflict, by discarding either local or remote changes"
    bl_options = {'INTERNAL'}

    set_outdated_flag = False

    resolve_method: EnumProperty(
        name="Resolve Method",
        description="Method to use to resolve the conflict",
        items=[
            (
                'mine-full',
                'Keep Mine',
                'Overwrite the new changes downloaded from the remote, and keep the local changes instead',
            ),
            (
                'theirs-full',
                'Keep Theirs',
                'Overwrite the local changes with those downloaded from the remote',
            ),
        ],
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.alert = True
        col.label(text="Choose which version of the file to keep.")
        col.row().prop(self, 'resolve_method', expand=True)
        col.separator()
        if self.resolve_method == 'mine-full':
            col.label(text="Local changes will be kept.")
            col.label(
                text="When committing, the changes someone else made will be overwritten."
            )
        else:
            col.label(text="Local changes will be permanently lost.")
            super().draw(context)

    def _execute(self, context: Context) -> Set[str]:
        self.execute_svn_command(
            context,
            [
                "svn",
                "resolve",
                f"{self.file_rel_path}",
                "--accept",
                f"{self.resolve_method}",
            ],
        )
        if self.file_is_current_blend(context):
            # If user wants to keep their changes to the current file,
            # remove the outdated file warning UI.
            context.scene.svn.file_is_outdated = self.resolve_method != 'mine-full'

        return {"FINISHED"}

    def set_predicted_file_status(self, repo, file_entry: "SVN_file"):
        if self.resolve_method == 'mine-full':
            file_entry.status = 'modified'
        else:
            file_entry.status = 'normal'


class SVN_OT_cleanup(SVN_Operator, Operator):
    bl_idname = "svn.cleanup"
    bl_label = "SVN Cleanup"
    bl_description = "Resolve issues that can arise from previous SVN processes having been interrupted"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # Don't allow attempting to cleanup while Update/Commit is running.
        return not get_addon_prefs(context).is_busy

    def execute(self, context: Context) -> Set[str]:
        repo = context.scene.svn.get_repo(context)

        repo.external_files.clear()
        self.execute_svn_command(context, ["svn", "cleanup"])
        repo.reload_svn_log(context)

        Processes.kill('Commit')
        Processes.kill('Update')
        Processes.kill('Authenticate')
        Processes.kill('Activate File')

        Processes.restart('Status')
        Processes.restart('Log')
        Processes.restart('Redraw Viewport')

        self.report({'INFO'}, "SVN Cleanup complete.")

        return {"FINISHED"}


registry = [
    SVN_OT_update_single,
    SVN_OT_revert_and_update,
    SVN_OT_revert_file,
    SVN_OT_restore_file,
    SVN_OT_download_file_revision,
    SVN_OT_add_file,
    SVN_OT_unadd_file,
    SVN_OT_trash_file,
    SVN_OT_remove_file,
    SVN_OT_resolve_conflict,
    SVN_OT_cleanup,
]
