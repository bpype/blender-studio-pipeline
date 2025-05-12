# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple

from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess, Processes


class BGP_SVN_Update(BackgroundProcess):
    name = "Update"
    needs_authentication = True
    timeout = 5*60
    repeat_delay = 0.01  # 0 means don't repeat
    debug = False

    def __init__(self, revision=0):
        super().__init__()

        self.revision = revision
        self.message = "Updating..."

    def set_predicted_file_status(self, file):
        if self.revision != 0:
            # File status prediction is not supported for reverting the entire
            # repository. It would be complicated to implement, and not really useful.
            return
        file.status_prediction_type = "SVN_UP"
        if file.repos_status == 'modified' and file.status == 'normal':
            # Modified on remote, exists on local.
            file.repos_status = 'none'
        elif file.repos_status == 'added' and file.status == 'none':
            # Added on remote, doesn't exist on local.
            file.status = 'normal'
        elif file.repos_status == 'deleted' and file.status == 'normal':
            # Deleted on remote, exists on local.
            # NOTE: File entry should just be deleted.
            file.status = 'none'
            file.repos_status = 'none'
        else:
            file.status = 'conflicted'

    def acquire_output(self, context, prefs):
        Processes.kill('Status')

        repo = context.scene.svn.get_repo(context)
        files = [
            f
            for f in repo.external_files
            if f.repos_status != 'none' or f.status_prediction_type == 'SVN_UP'
        ]
        dirs = [f for f in files if f.is_dir]
        if dirs:
            dirs.sort(key=lambda d: len(d.svn_path))
            file = dirs[0]
            self.message = "Creating folder: " + file.svn_path
        elif files:
            file = files[0]
            self.message = f"Updating file: {file.svn_path} ({file.file_size})"
        else:
            print("SVN Update complete.")
            self.stop()
            return

        print(self.message)
        self.set_predicted_file_status(file)
        command = ["svn", "up", file.svn_path, "--accept", "postpone", "--depth", "empty"]
        if self.revision > 0:
            command.insert(2, f"-r{self.revision}")
        self.output = execute_svn_command(context, command, use_cred=True)
        file.status_prediction_type = 'SKIP_ONCE'
        file.repos_status = 'none'  # Without this, it would keep updating the same file.

    def handle_error(self, context, error):
        Processes.start('Status')
        super().handle_error(context, error)

    def process_output(self, context, prefs):
        return

    def get_ui_message(self, context) -> str:
        """Return a string that should be drawn in the UI for user feedback, 
        depending on the state of the process."""

        if self.is_running:
            return self.message + "..."
        return ""

    def stop(self):
        super().stop()
        Processes.start('Log')
        Processes.start('Status')
