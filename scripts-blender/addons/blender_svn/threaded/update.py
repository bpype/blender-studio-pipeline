# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

from typing import List, Dict, Union, Any, Set, Optional, Tuple

from .execute_subprocess import execute_svn_command
from .background_process import BackgroundProcess, Processes


class BGP_SVN_Update(BackgroundProcess):
    name = "Update"
    needs_authentication = True
    timeout = 5*60
    repeat_delay = 1
    debug = False

    def __init__(self, revision=0):
        super().__init__()

        self.revision = revision

    def acquire_output(self, context, prefs):
        Processes.kill('Status')

        repo = context.scene.svn.get_repo(context)
        files = [f for f in repo.external_files if f.repos_status != 'none']
        if files:
            file = files[0]
            print("Updating file: ", file.svn_path)
            command = ["svn", "up", file.svn_path, "--accept", "postpone"]
            if self.revision > 0:
                command.insert(2, f"-r{self.revision}")
            self.output = execute_svn_command(context, command, use_cred=True)
            file.repos_status = 'none'  # Without this, it would keep updating the same file.
        else:
            self.stop()

    def handle_error(self, context, error):
        Processes.start('Status')
        super().handle_error(context, error)

    def process_output(self, context, prefs):
        print("SVN Update complete:")
        print("\n".join(self.output.split("\n")[1:]))
        for f in context.scene.svn.get_repo(context).external_files:
            if f.status_prediction_type == 'SVN_UP':
                f.status_prediction_type = 'SKIP_ONCE'

    def get_ui_message(self, context) -> str:
        """Return a string that should be drawn in the UI for user feedback, 
        depending on the state of the process."""

        if self.is_running:
            return f"Updating files..."
        return ""

    def stop(self):
        super().stop()
        Processes.start('Log')
        Processes.start('Status')
