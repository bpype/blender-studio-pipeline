# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik
from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty, EnumProperty

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

    svn_path: StringProperty(
        name="SVN Path",
        description="Filepath relative to the SVN root",
        options=set()
    )
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
        if '.' not in self.name:
            return 'FILE_FOLDER'
        extension = self.name.split(".")[-1] if "." in self.name else ""

        if extension in ['abc']:
            return 'FILE_CACHE'
        elif extension in ['blend', 'blend1']:
            return 'FILE_BLEND'
        elif extension in ['tga', 'bmp', 'tif', 'tiff', 'tga', 'png', 'dds', 'jpg', 'exr', 'hdr']:
            return 'TEXTURE'
        elif extension in ['psd', 'kra']:
            return 'IMAGE_DATA'
        elif extension in ['mp4', 'mov']:
            return 'SEQUENCE'
        elif extension in ['mp3', 'ogg', 'wav']:
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
        description="List of file entries that were affected by this revision"
    )

    def changes_file(self, file: SVN_file) -> bool:
        for affected_file in self.changed_files:
            if affected_file.svn_path == "/"+file.svn_path:
                return True
        return False

    matches_filter: BoolProperty(
        name="Matches Filter",
        description="Whether the log entry matches the currently typed in search filter",
        default=True
    )

    def changed_file(self, svn_path: str) -> bool:
        for f in self.changed_files:
            if f.svn_path == "/"+svn_path:
                return True
        return False

    @property
    def text_to_search(self) -> str:
        """Return a string containing all searchable information about this log entry."""
        # TODO: For optimization's sake, this shouldn't be a @property, but instead
        # saved as a proper variable when the log entry is created.
        rev = "r"+str(self.revision_number)
        auth = self.revision_author
        files = " ".join([f.svn_path for f in self.changed_files])
        msg = self.commit_message
        date = self.revision_date_simple
        return " ".join([rev, auth, files, msg, date]).lower()

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
    def active_log(self):
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
        return absolute_path.relative_to(svn_dir)

    def svn_to_absolute_path(self, svn_path: Path) -> Path:
        if type(svn_path) == str:
            svn_path = Path(svn_path)
        svn_dir = Path(self.directory)
        return svn_dir / svn_path

    def get_file_by_svn_path(self, svn_path: str or Path) -> Optional[SVN_file]:
        if isinstance(svn_path, Path):
            # We must use isinstance() instead of type() because apparently
            # the Path() constructor returns a WindowsPath object on Windows.
            svn_path = str(svn_path.as_posix())

        for file in self.external_files:
            if file.svn_path == svn_path:
                return file

    def get_file_by_absolute_path(self, abs_path: str or Path) -> Optional[SVN_file]:
        if isinstance(abs_path, Path):
            # We must use isinstance() instead of type() because apparently
            # the Path() constructor returns a WindowsPath object on Windows.
            abs_path = str(abs_path.as_posix())
        else:
            abs_path = str(Path(abs_path).as_posix())

        for file in self.external_files:
            if file.absolute_path == abs_path:
                return file

    def get_index_of_file(self, file_entry) -> Optional[int]:
        for i, file in enumerate(self.external_files):
            if file == file_entry:
                return i

    def update_active_file(self, context):
        """When user clicks on a different file, the latest log entry of that file
        should become the active log entry.
        NOTE: Try to only trigger this on explicit user actions!
        """

        if self.external_files_active_index == self.prev_external_files_active_index:
            return
        self.prev_external_files_active_index = self.external_files_active_index

        latest_rev = self.get_latest_revision_of_file(
            self.active_file.svn_path)
        # SVN Revisions are not 0-indexed, so we need to subtract 1.
        self.log_active_index = latest_rev-1

        space = context.space_data
        if space and space.type == 'FILE_BROWSER':
            space.params.directory = Path(self.active_file.absolute_path).parent.as_posix().encode()
            space.params.filename = self.active_file.name.encode()

            space.deselect_all()
            # Set the active file in the file browser to whatever was selected 
            # in the SVN Files panel.
            space.activate_file_by_relative_path(       # This doesn't actually work, due to what I assume is a bug.
                relative_path=self.active_file.name)
            Processes.start('Activate File')            # This is my work-around.

        # Set the filter flag of the log entries based on whether they affect the active file or not.
        self.log.foreach_set(
            'affects_active_file',
            [log_entry.changes_file(self.active_file)
             for log_entry in self.log]
        )

    prev_external_files_active_index: IntProperty(
        name="Previous Active Index",
        description="Internal value to avoid triggering the update callback unnecessarily",
        options=set()
    )
    external_files_active_index: IntProperty(
        name="File List",
        description="Files tracked by SVN",
        update=update_active_file,
        options=set()
    )

    @property
    def active_file(self) -> SVN_file:
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
        svn_file = self.get_file_by_svn_path(svn_path)

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
