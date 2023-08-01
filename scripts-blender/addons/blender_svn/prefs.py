# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from typing import Optional, Any, Set, Tuple, List
import platform

import bpy
from bpy.props import IntProperty, CollectionProperty, BoolProperty, EnumProperty
from bpy.types import AddonPreferences

from .ui.ui_repo_list import draw_checkout, draw_repo_list
from .repository import SVN_repository
from .svn_info import get_svn_info
import json
from pathlib import Path
from .threaded.background_process import Processes


class SVN_addon_preferences(AddonPreferences):
    bl_idname = __package__

    is_svn_installed: BoolProperty(
        name="Is SVN Installed",
        description="Whether the `svn` command works at all in the user's command line. If not, user needs to install SVN",
        default=False
    )

    repositories: CollectionProperty(type=SVN_repository)

    def init_repo_list(self):
        # If we have any repository entries, make sure at least one is active.
        self.sync_repo_info_file()

        if self.active_repo_idx == -1 and len(self.repositories) > 0:
            self.active_repo_idx = 0
        elif self.active_repo_idx > len(self.repositories)-1:
            self.active_repo_idx = 0
        else:
            self.active_repo_idx = self.active_repo_idx

    def init_repo(self, context, repo_path: Path or str):
        """Attempt to initialize a repository based on a directory.
        This means executing `svn info` in the repo_path to get the URL and root dir.
        If we already have an SVN_repository instance with that root dir, just return it.
        Otherwise, initialize it by storing its directory, URL, and a display name, and then return it.
        """
        root_dir, base_url = get_svn_info(repo_path)
        if not root_dir:
            return
        existing_repo = self.repositories.get(root_dir)
        if existing_repo:
            if existing_repo.external_files_active_index > len(existing_repo.external_files):
                existing_repo.external_files_active_index = 0
            existing_repo.log_active_index = len(existing_repo.log)-1
            existing_repo.reload_svn_log(context)
            return existing_repo

        repo = self.repositories.add()
        repo.initialize(root_dir, base_url)
        self.active_repo_idx = len(self.repositories)-1

        return repo

    checkout_mode: BoolProperty(
        name="Checkout In Progress",
        description="Internal flag to indicate that the user is currently trying to create a new checkout",
        default=False
    )

    def update_active_repo_idx(self, context):
        if len(self.repositories) == 0:
            return
        active_repo = self.active_repo

        # Authenticate when switching repos.
        if (
            active_repo and
            not active_repo.auth_failed and
            active_repo.is_cred_entered
        ):
            Processes.start('Redraw Viewport')
            if active_repo.authenticated:
                Processes.restart('Status')
            else:
                active_repo.authenticate()
        else:
            Processes.kill('Status')

    active_repo_idx: IntProperty(
        name="SVN Repositories",
        options=set(),
        update=update_active_repo_idx
    )

    @property
    def active_repo(self) -> Optional[SVN_repository]:
        if not self.is_svn_installed:
            return
        if 0 <= self.active_repo_idx <= len(self.repositories)-1:
            return self.repositories[self.active_repo_idx]

    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable some debug UI",
        default=False
    )

    @property
    def is_busy(self):
        return Processes.is_running('Commit', 'Update')

    loading: BoolProperty(
        name="Loading",
        description="Disable the credential update callbacks while loading repo data to avoid infinite loops",
        default=False
    )

    def save_repo_info_to_file(self):
        saved_props = {'url', 'directory', 'name',
                       'username', 'password', 'display_name'}
        repo_data = {}
        for repo in self['repositories']:
            directory = repo.get('directory', '')

            repo_data[directory] = {
                key: value for key, value in repo.to_dict().items() if key in saved_props}

        filepath = Path(bpy.utils.user_resource('CONFIG')) / \
            Path("blender_svn.txt")
        with open(filepath, "w") as f:
            json.dump(repo_data, f, indent=4)

    def load_repo_info_from_file(self):
        self.loading = True
        try:
            filepath = Path(bpy.utils.user_resource(
                'CONFIG')) / Path("blender_svn.txt")
            if not filepath.exists():
                return

            with open(filepath, "r") as f:
                repo_data = json.load(f)

            for directory, repo_data in repo_data.items():
                repo = self.repositories.get(directory)
                if not repo:
                    repo = self.repositories.add()
                    repo.directory = directory
                    for key, value in repo_data.items():
                        setattr(repo, key, value)
        finally:
            self.loading = False

    def sync_repo_info_file(self):
        self.load_repo_info_from_file()
        self.save_repo_info_to_file()

    def draw(self, context):
        if not self.is_svn_installed:
            draw_prefs_no_svn(self, context)
            return

        if self.checkout_mode:
            draw_checkout(self, context)
        else:
            draw_repo_list(self, context)


def draw_prefs_no_svn(self, context):
    terminal, url = "terminal", "https://subversion.apache.org/packages.html"
    system = platform.system()
    if system == "Windows":
        terminal = "command line (cmd.exe)"
        url = "https://subversion.apache.org/packages.html#windows"
    elif system == "Darwin":
        terminal = "Mac terminal"
        url = "https://subversion.apache.org/packages.html#osx"

    layout = self.layout
    col = layout.column()
    col.alert=True
    col.label(text="Please ensure that Subversion (aka. SVN) is installed on your system.")
    col.label(text=f"Typing `svn` into the {terminal} should yield a result.")
    layout.operator("wm.url_open", icon='URL', text='Open Subversion Distribution Page').url=url


registry = [
    SVN_addon_preferences
]
