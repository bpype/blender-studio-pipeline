# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional,Tuple
from pathlib import Path

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    EnumProperty,
    FloatProperty,
)

from .threaded import svn_log
from .threaded.background_process import Processes
from .operators.svn_commit import SVN_commit_line
from .svn_info import get_svn_info
from .util import get_addon_prefs
from . import constants


class SVN_file(PropertyGroup):
    """Property Group that can represent a version of a File in an SVN repository."""

    name: StringProperty(
        name="File Name",
        options=set()
    )

    @property
    def svn_path(self):
        return self.name

    @svn_path.setter
    def svn_path(self, value):
        self.name = value

    @property
    def file_name(self):
        return Path(self.svn_path).name

    absolute_path: StringProperty(
        name="Absolute Path",
        description="Absolute filepath",
        options=set()
    )

    status: EnumProperty(
        name="Status",
        description="SVN Status of the file in the local repository (aka working copy)",
        items=constants.ENUM_SVN_STATUS,
        default="normal",
        options=set()
    )
    repos_status: EnumProperty(
        name="Remote's Status",
        description="SVN Status of the file in the remote repository (periodically updated)",
        items=constants.ENUM_SVN_STATUS,
        default="none",
        options=set()
    )
    @property
    def will_conflict(self):
        return self.status != 'normal' and self.repos_status != 'none'

    status_prediction_type: EnumProperty(
        name="Status Predicted By Process",
        items=[
            ("NONE", "None", "File status is not predicted, but actual."),
            ("SVN_UP", "Update", "File status is predicted by `svn up`. Status is protected until process is finished."),
            ("SVN_COMMIT", "Commit",
             "File status is predicted by `svn commit`. Status is protected until process is finished."),
            ("SKIP_ONCE", "Skip Once", "File status is predicted by a working-copy svn file operation, like Revert. Next status update should be ignored, and this enum should be set to SKIPPED_ONCE."),
            ("SKIPPED_ONCE", "Skipped Once", "File status update was skipped. Next status update can be considered accurate, and this flag can be reset to NONE. Until then, operations on this file should remain disabled."),
        ],
        description="Internal flag that notes what process set a predicted status on this file. Should be empty string when the status is not predicted but confirmed. When svn commit/update predicts a status, that status should not be overwritten until the process is finished. With instantaneous processes, a single status update should be ignored since it may be outdated",
        options=set()
    )
    include_in_commit: BoolProperty(
        name="Commit",
        description="Whether this file should be included in the commit or not",
        default=False,
        options=set()
    )

    @property
    def is_outdated(self):
        return self.repos_status == 'modified' and self.status == 'normal'

    @property
    def is_dir(self):
        if self.exists:
            return Path(self.absolute_path).is_dir()
        else:
            # This file may not exist locally yet, but it could still exist on the SVN,
            # and in this case we still want to provide a guess as to whether it's a folder or not.
            return "." not in Path(self.absolute_path).name

    revision: IntProperty(
        name="Revision",
        description="Revision number",
        options=set()
    )

    @property
    def exists(self) -> bool:
        return Path(self.absolute_path).exists()

    @property
    def status_icon(self) -> str:
        return constants.SVN_STATUS_DATA[self.status][0]

    @property
    def status_name(self) -> str:
        if self.status == 'none':
            return 'Outdated'
        return self.status.title()

    @property
    def file_icon(self) -> str:
        if self.is_dir:
            return 'FILE_FOLDER'
        extension = Path(self.svn_path).suffix

        if extension in ['.abc']:
            return 'FILE_CACHE'
        elif 'blend' in extension:
            return 'FILE_BLEND'
        elif extension in [
            '.tga',
            '.bmp',
            '.tif',
            '.tiff',
            '.tga',
            '.png',
            '.dds',
            '.jpg',
            '.exr',
            '.hdr',
        ]:
            return 'TEXTURE'
        elif extension in ['.psd', '.kra']:
            return 'IMAGE_DATA'
        elif extension in ['.mp4', '.mov']:
            return 'SEQUENCE'
        elif extension in ['.mp3', '.ogg', '.wav']:
            return 'SPEAKER'

        return 'QUESTION'

    @property
    def has_default_status(self):
        return self.status == 'normal' and self.repos_status == 'none' and self.status_prediction_type == 'NONE'

    show_in_filelist: BoolProperty(
        name="Show In File List",
        description="Flag indicating whether this file should be drawn in the file list. This flag is updated for every file whenever the file search string is modified. If we did this filtering during drawing time, it is painfully slow",
        default=False
    )

    def get_file_size(self):
        num = self.file_size_KiB
        for unit in ("KiB", "MiB", "GiB", "TiB", "PiB", "EiB"):
            if num < 1024:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} YiB"

    def update_file_size(self, _context):
        self.file_size = self.get_file_size()

    file_size_KiB: FloatProperty(description="One KibiByte (KiB) is 1024 bytes", update=update_file_size)
    file_size: StringProperty(description="File size for displaying in the UI")


class SVN_log(PropertyGroup):
    """Property Group that can represent an SVN log entry."""

    revision_number: IntProperty(
        name="Revision Number",
        description="Revision number of the current .blend file",
    )
    revision_date: StringProperty(
        name="Revision Date",
        description="Date when the current revision was committed",
    )
    revision_date_simple: StringProperty(
        name="Revision Date",
        description="Date when the current revision was committed",
    )

    revision_author: StringProperty(
        name="Revision Author",
        description="SVN username of the revision author",
    )
    commit_message: StringProperty(
        name="Commit Message",
        description="Commit message written by the commit author to describe the changes in this revision",
    )

    changed_files: CollectionProperty(
        type=SVN_file,
        name="Changed Files",
        description="List of file entries that were affected by this revision. Note that these are NOT pointers to the actual file entries stored in repository.external_files. These are copies, merely serving to store a file path",
    )

    def changes_file(self, file: SVN_file) -> bool:
        """Return whether the given file is among this log entry's changed files list."""
        for affected_file in self.changed_files:
            if affected_file.svn_path == "/"+file.svn_path:
                return True
        return False

    text_to_search: StringProperty(
        name="Text to Search",
        description="Text to be used by the search filter. This should be set by calling set_search_string() when the log entry is created, and then never touched again",
    )

    def set_search_string(self):
        rev = "r"+str(self.revision_number)
        auth = self.revision_author
        files = " ".join([f.svn_path for f in self.changed_files])
        msg = self.commit_message
        date = self.revision_date_simple

        self.text_to_search = " ".join([rev, auth, files, msg, date]).lower()

    # Cached variables; Things that update when active file or search filter changes,
    # so that they don't have to be re-calculated on each re-draw of the log UI.
    matches_filter: BoolProperty(
        name="Matches Filter",
        description="Whether the log entry matches the currently typed in search filter. This is cached, and should be re-calculated ONLY whenever the search filter changes",
        default=True,
    )
    affects_active_file: BoolProperty(
        name="Affects Active File",
        description="Flag set whenever the active file index updates. Used to accelerate drawing performance by moving filtering logic from the drawing code to update callbacks and flags",
        default=False
    )


class SVN_repository(PropertyGroup):
    ### Basic SVN Info. ###
    @property
    def name(self):
        return self.directory

    def update_repo_info_file(self, context):
        get_addon_prefs(context).save_repo_info_to_file()

    display_name: StringProperty(
        name="Display Name",
        description="Display name of this SVN repository",
        update=update_repo_info_file
    )

    url: StringProperty(
        name="URL",
        description="URL of the remote repository",
    )

    def update_directory(self, context):
        self.name = self.directory

        root_dir, base_url = get_svn_info(self.directory)
        if root_dir and base_url:
            self.initialize(root_dir, base_url)

    directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
        update=update_directory
    )

    @property
    def dir_exists(self):
        dir_path = Path(self.directory)
        return dir_path.exists() and dir_path.is_dir()

    @property
    def is_valid_svn(self):
        dir_path = Path(self.directory)
        # TODO: This property is checked pretty often, so we run `svn info` pretty often. Might not be a big deal, but maybe it's a bit overkill?
        root_dir, base_url = get_svn_info(self.directory)
        return (
            dir_path.exists() and
            dir_path.is_dir() and
            root_dir and base_url and
            root_dir == self.directory and
            base_url == self.url
        )

    def initialize(self, directory: str, url: str, display_name="", username="", password=""):
        self.url = url
        if username:
            self.username = username
        if password:
            self.password = password
        if self.directory != directory:
            # Don't set this if it's already set, to avoid infinite recursion
            # via the update callback.
            self.directory = directory
        if display_name:
            self.display_name = display_name
        else:
            self.display_name = Path(directory).name

        return self

    ### Credentials. ###
    def update_cred(self, context):
        if not (self.username and self.password):
            # Only try to authenticate if BOTH username AND pw are entered.
            self.authenticated = False
            return
        if get_addon_prefs(context).loading:
            return

        self.authenticate()
        self.update_repo_info_file(context)

    def authenticate(self):
        self.auth_failed = False
        if self.is_valid_svn and self.is_cred_entered:
            Processes.start('Authenticate')
            # Trigger the file list filtering.
            self.file_search_filter = self.file_search_filter

    username: StringProperty(
        name="Username",
        description="User name used for authentication with this SVN repository",
        update=update_cred
    )
    password: StringProperty(
        name="Password",
        description="Password used for authentication with this SVN repository. This password is stored in your Blender user preferences as plain text. Somebody with access to your user preferences will be able to read your password",
        subtype='PASSWORD',
        update=update_cred
    )

    @property
    def is_cred_entered(self) -> bool:
        """Check if there's a username and password entered at all."""
        return bool(self.username and self.password)

    authenticated: BoolProperty(
        name="Authenticated",
        description="Internal flag to mark whether the last entered credentials were confirmed by the repo as correct credentials",
        default=False
    )
    auth_failed: BoolProperty(
        name="Authentication Failed",
        description="Internal flag to mark whether the last entered credentials were rejected by the repo",
        default=False
    )

    ### SVN Commit Message. ###
    commit_lines: CollectionProperty(type=SVN_commit_line)

    @property
    def commit_message(self):
        return "\n".join([l.line for l in self.commit_lines]).strip()

    @commit_message.setter
    def commit_message(self, msg: str):
        self.commit_lines.clear()
        for line in msg.split("\n"):
            line_entry = self.commit_lines.add()
            line_entry.line = line
        while len(self.commit_lines) < 3:
            self.commit_lines.add()

    ### SVN Log / Revision History. ###
    log: CollectionProperty(type=SVN_log)
    log_active_index: IntProperty(
        name="SVN Log",
        options=set()
    )

    reload_svn_log = svn_log.reload_svn_log

    @property
    def log_file_path(self) -> Path:
        return Path(self.directory+"/.svn/svn.log")

    @property
    def active_log(self) -> SVN_log | None:
        try:
            return self.log[self.log_active_index]
        except IndexError:
            return None

    def get_log_by_revision(self, revision: int) -> Tuple[int, SVN_log]:
        for i, log in enumerate(self.log):
            if log.revision_number == revision:
                return i, log

    def get_latest_revision_of_file(self, svn_path: str) -> int:
        """Return the revision number of the last log entry that affects the given file."""
        svn_path = str(svn_path)
        for log in reversed(self.log):
            for changed_file in log.changed_files:
                if changed_file.svn_path == "/"+str(svn_path):
                    return log.revision_number
        return 0

    def is_file_outdated(self, file: SVN_file) -> bool:
        """A file may have the 'modified' state while also being outdated.
        In this case SVN is of no use, we need to detect and handle this case
        by ourselves.
        """
        latest = self.get_latest_revision_of_file(file.svn_path)
        current = file.revision
        return latest > current

    def get_file_abspath(self, file: SVN_file) -> Path:
        """Return the absolute path of an SVN file if it were in this repo."""
        return Path(self.directory) / Path(file.svn_path)

    ### SVN File List. ###
    external_files: CollectionProperty(type=SVN_file)

    def remove_file_entry(self, file_entry: SVN_file):
        """Remove a file entry from the file list, based on its filepath."""
        for i, f in enumerate(self.external_files):
            if f == file_entry:
                self.external_files.remove(i)
                if i <= self.external_files_active_index:
                    self.external_files_active_index -= 1
                return

    def absolute_to_svn_path(self, absolute_path: Path) -> Path:
        if type(absolute_path) == str:
            absolute_path = Path(absolute_path)
        svn_dir = Path(self.directory)
        try:
            return absolute_path.relative_to(svn_dir)
        except ValueError:
            return None

    def svn_to_absolute_path(self, svn_path: Path) -> Path:
        if type(svn_path) == str:
            svn_path = Path(svn_path)
        svn_dir = Path(self.directory)
        return svn_dir / svn_path

    def get_file_by_absolute_path(self, abs_path: str or Path) -> Optional[SVN_file]:
        rel_path = str(self.absolute_to_svn_path(abs_path))
        if rel_path:
            return self.external_files.get(rel_path)

    def get_index_of_file(self, file_entry) -> Optional[int]:
        for i, file in enumerate(self.external_files):
            if file == file_entry:
                return i

    def force_update_ui_caches(self, context):
        """Update UI caches even if the active file index hasn't changed.
        This is used when loading a file.
        """
        self.prev_active_file_name = ""
        self.update_ui_caches(context)

    def update_ui_caches(self, context):
        """When user clicks on a different file, the latest log entry of that file
        should become the active log entry.
        NOTE: Try to only trigger this on explicit user actions!
        """

        if not self.active_file:
            return
        if self.active_file.name == self.prev_active_file_name:
            return
        self.prev_active_file_name = self.active_file.name

        latest_rev = self.get_latest_revision_of_file(
            self.active_file.svn_path)
        # SVN Revisions are not 0-indexed, so we need to subtract 1.
        self.log_active_index = latest_rev-1

        space = context.space_data
        if space and space.type == 'FILE_BROWSER':
            space.params.directory = Path(self.active_file.absolute_path).parent.as_posix().encode()
            space.params.filename = self.active_file.file_name.encode()

            space.deselect_all()
            # Set the active file in the file browser to whatever was selected
            # in the SVN Files panel.
            space.activate_file_by_relative_path(       # This doesn't actually work, due to what I assume is a bug.
                relative_path=self.active_file.file_name)
            Processes.start('Activate File')            # This is my work-around.

        # Set the filter flag of the log entries based on whether they affect the active file or not.
        self.log.foreach_set(
            'affects_active_file',
            [log_entry.changes_file(self.active_file)
             for log_entry in self.log]
        )

    prev_active_file_name: StringProperty(
        name="Previous Active File",
        description="Internal value to avoid triggering the update callback unnecessarily",
        options=set()
    )
    external_files_active_index: IntProperty(
        name="File List",
        description="Files tracked by SVN",
        update=update_ui_caches,
        options=set(),
    )

    @property
    def active_file(self) -> SVN_file:
        if len(self.external_files) == 0:
            return
        return self.external_files[self.external_files_active_index]

    def is_filebrowser_directory_in_repo(self, context) -> bool:
        assert context.space_data.type == 'FILE_BROWSER', "This function needs a File Browser context."

        params = context.space_data.params
        abs_path = Path(params.directory.decode())

        if not abs_path.exists():
            return False

        return Path(self.directory) in [abs_path] + list(abs_path.parents)

    def get_filebrowser_active_file(self, context) -> SVN_file:
        assert context.space_data.type == 'FILE_BROWSER', "This function needs a File Browser context."

        params = context.space_data.params
        abs_path = Path(params.directory.decode()) / Path(params.filename)

        if not abs_path.exists():
            return

        if Path(self.directory) not in abs_path.parents:
            return False

        svn_path = self.absolute_to_svn_path(abs_path)
        svn_file = self.external_files.get(svn_path)

        return svn_file

    @property
    def current_blend_file(self) -> SVN_file:
        return self.get_file_by_absolute_path(bpy.data.filepath)

    ### File List UIList filter properties ###
    def refresh_ui_lists(self, context):
        """Refresh the file UI list based on filter settings.
        Also triggers a refresh of the SVN UIList, through the update callback of
        external_files_active_index."""

        UI_LIST = bpy.types.UI_UL_list
        if self.file_search_filter:
            filter_list = UI_LIST.filter_items_by_name(
                self.file_search_filter,
                1,
                self.external_files,
                "name",
                reverse=False
            )
            filter_list = [bool(val) for val in filter_list]
            self.external_files.foreach_set('show_in_filelist', filter_list)
        else:
            for file in self.external_files:
                if file == self.current_blend_file:
                    file.show_in_filelist = True
                    continue

                file.show_in_filelist = not file.has_default_status

        if len(self.external_files) == 0:
            return

        # Make sure the active file isn't now being filtered out.
        # If it is, change the active file to the first visible one.
        if self.active_file.show_in_filelist:
            return
        for i, file in enumerate(self.external_files):
            if file.show_in_filelist:
                self.external_files_active_index = i
                return

    file_search_filter: StringProperty(
        name="Search Filter",
        description="Only show entries that contain this string",
        update=refresh_ui_lists
    )


registry = [
    SVN_file,
    SVN_log,
    SVN_repository,
]
