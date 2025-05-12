# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import platform

from bpy.types import UIList, Operator, Menu
from bpy_extras.io_utils import ImportHelper

from ..util import get_addon_prefs
from .ui_log import draw_svn_log, is_log_useful
from .ui_file_list import draw_file_list, draw_process_info
from ..threaded.background_process import Processes

from pathlib import Path

class SVN_UL_repositories(UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        repo = item
        row = layout.row()

        row.label(text=repo.display_name)

        if not repo.dir_exists:
            row.alert = True
        row.prop(repo, 'directory', text="")


class SVN_OT_repo_add(Operator, ImportHelper):
    """Add a repository to the list"""

    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    bl_idname = "svn.repo_add"
    bl_label = "Add Repository"

    def execute(self, context):
        prefs = get_addon_prefs(context)
        repos = prefs.repositories

        path = Path(self.filepath)
        if not path.exists():
            # It's unlikely that a path that the user JUST BROWSED doesn't exist.
            # So, this actually happens when the user leaves a filename in the 
            # file browser text box while trying to select the folder...
            # Basically, Blender is dumb, and it will add that filename to the 
            # end of the browsed path. We need to discard that.
            path = path.parent
        if path.is_file():
            # Maybe the user actually did select an existing file in the repo.
            # We still want to discard the filename.
            path = path.parent

        existing_repos = repos[:]
        try:
            repo = prefs.init_repo(context, path)
        except Exception as e:
            self.report(
                {'ERROR'},
                "Failed to initialize repository. Ensure you have SVN installed, and that the selected directory is the root of a repository.",
            )
            print(e)
            return {'CANCELLED'}
        if not repo:
            self.report({'ERROR'}, "Failed to initialize repository.")
            return {'CANCELLED'}
        if repo in existing_repos:
            self.report({'INFO'}, "Repository already present.")
        else:
            self.report({'INFO'}, "Repository added.")
        prefs.active_repo_idx = repos.find(repo.directory)
        prefs.save_repo_info_to_file()
        return {'FINISHED'}


class SVN_OT_repo_remove(Operator):
    """Remove a repository from the list"""

    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    bl_idname = "svn.repo_remove"
    bl_label = "Remove Repository"

    @classmethod
    def poll(cls, context):
        return len(get_addon_prefs(context).repositories) > 0

    def execute(self, context):
        prefs = get_addon_prefs(context)
        active_index = prefs.active_repo_idx
        repos = prefs.repositories

        prefs.repositories.remove(prefs.active_repo_idx)
        to_index = min(active_index, len(repos) - 1)
        prefs.active_repo_idx = to_index
        prefs.save_repo_info_to_file()
        return {'FINISHED'}


class SVN_MT_add_repo(Menu):
    bl_idname = "SVN_MT_add_repo"
    bl_label = "Add Repo"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "svn.repo_add", text="Browse Existing Checkout", icon='FILE_FOLDER'
        )
        layout.operator(
            "svn.checkout_initiate", text="Create New Checkout", icon='URL'
        ).create = True


def draw_repo_list(self, context) -> None:
    layout = self.layout

    auth_in_progress = False
    auth_error = False
    auth_proc = Processes.get('Authenticate')
    if auth_proc:
        auth_in_progress = auth_proc.is_running
        auth_error = auth_proc.error

    repo_col = layout.column()
    split = repo_col.row().split()
    split.row().label(text="SVN Repositories:")

    # Secret debug toggle (invisible, to the right of the SVN Repositories label.)
    row = split.row()
    row.alignment = 'RIGHT'
    row.prop(self, 'debug_mode', text="", icon='BLANK1', emboss=False)

    repo_col.enabled = not auth_in_progress

    list_row = repo_col.row()
    col = list_row.column()
    col.template_list(
        "SVN_UL_repositories",
        "svn_repo_list",
        self,
        "repositories",
        self,
        "active_repo_idx",
    )

    op_col = list_row.column()
    op_col.menu('SVN_MT_add_repo', icon='ADD', text="")
    op_col.operator('svn.repo_remove', icon='REMOVE', text="")

    if len(self.repositories) == 0:
        return
    if self.active_repo_idx - 1 > len(self.repositories):
        return
    if not self.active_repo:
        return

    repo_col.prop(self.active_repo, 'display_name', icon='FILE_TEXT')
    repo_col.prop(self.active_repo, 'url', icon='URL')
    repo_col.prop(self.active_repo, 'username', icon='USER')
    repo_col.prop(self.active_repo, 'password', icon='LOCKED')

    draw_process_info(context, layout.row())

    if not self.active_repo.dir_exists:
        draw_repo_error(layout, "Repository not found on file system.")
        return
    if not self.active_repo.is_valid_svn:
        draw_repo_error(layout, "Directory is not an SVN repository.")
        split = layout.split(factor=0.24)
        split.row()
        split.row().operator(
            "svn.checkout_initiate", text="Create New Checkout", icon='URL'
        ).create = False
        return
    if not self.active_repo.authenticated and not auth_in_progress and not auth_error:
        draw_repo_error(layout, "Repository not authenticated. Enter your credentials.")
        return

    if len(self.repositories) > 0 and self.active_repo.authenticated:
        layout.separator()
        layout.label(text="SVN Files: ")
        draw_file_list(context, layout)

        if is_log_useful(context):
            layout.separator()
            layout.label(text="Revision History: ")
            draw_svn_log(context, layout)


def draw_repo_error(layout, message):
    split = layout.split(factor=0.24)
    split.row()
    col = split.column()
    col.alert = True
    col.label(text=message, icon='ERROR')


def draw_checkout(self, context):
    def get_terminal_howto():
        msg_windows = "If you don't, cancel this operation and toggle it using Window->Toggle System Console."
        msg_linux = "If you don't, quit Blender and re-launch it from a terminal."
        msg_mac = msg_linux

        system = platform.system()
        if system == "Windows":
            return msg_windows
        elif system == "Linux":
            return msg_linux
        elif system == "Darwin":
            return msg_mac

    layout = self.layout
    col = layout.column()
    col.alert = True

    col.label(text="IMPORTANT! ", icon='ERROR')
    col.label(text="Make sure you have Blender's terminal open!")
    col.label(text=get_terminal_howto())
    col.separator()
    col.label(
        text="Downloading a repository can take a long time, and the UI will be locked."
    )
    col.label(
        text="Without a terminal, you won't be able to track the progress of the checkout."
    )
    col.separator()

    col = layout.column()
    col.label(
        text="To interrupt the checkout, you can press Ctrl+C in the terminal.",
        icon='INFO',
    )
    col.label(
        text="You can resume it by re-running this operation, or with the SVN Update button.",
        icon='INFO',
    )
    col.separator()

    prefs = get_addon_prefs(context)
    repo = prefs.repositories[-1]
    col.prop(repo, 'directory')
    for other_repo in prefs.repositories:
        if other_repo == repo:
            continue
        if other_repo.directory == repo.directory:
            row = col.row()
            row.alert = True
            row.label(
                text="A repository at this filepath is already specified.", icon='ERROR'
            )
            break

    col.prop(repo, 'display_name', text="Folder Name", icon='NEWFOLDER')
    col.prop(repo, 'url', icon='URL')
    for other_repo in prefs.repositories:
        if other_repo == repo:
            continue
        if other_repo.url == repo.url:
            sub = col.column()
            sub.alert = True
            sub.label(text="A repository with this URL is already specified.")
            sub.label(
                text="If you're sure you want to checkout another copy of the repo, feel free to proceed."
            )
            break
    col.prop(repo, 'username', icon='USER')
    col.prop(repo, 'password', icon='LOCKED')

    op_row = layout.row()
    op_row.operator('svn.checkout_finalize', text="Checkout", icon='CHECKMARK')
    op_row.operator('svn.checkout_cancel', text="Cancel", icon="X")


registry = [SVN_UL_repositories, SVN_OT_repo_add, SVN_OT_repo_remove, SVN_MT_add_repo]
