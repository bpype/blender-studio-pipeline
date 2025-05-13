# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Dict, Union, Any, Set, Optional, Tuple

from bpy.types import Operator
from bpy.props import BoolProperty

from .simple_commands import SVN_Operator
from ..util import get_addon_prefs
from ..threaded.background_process import Processes

import subprocess
from pathlib import Path


class SVN_OT_checkout_initiate(Operator):
    bl_idname = "svn.checkout_initiate"
    bl_label = "Initiate SVN Checkout"
    bl_description = "Checkout a remote SVN repository"
    bl_options = {'INTERNAL'}

    create: BoolProperty(
        name="Create Repo Entry",
        description="Whether a new repo entry should be created, or the active one used",
        default=True
    )

    def execute(self, context):
        prefs = get_addon_prefs(context)
        if self.create:
            prefs.repositories.add()
            prefs.active_repo_idx = len(prefs.repositories)-1

        prefs.checkout_mode = True
        return {'FINISHED'}


class SVN_OT_checkout_finalize(Operator, SVN_Operator):
    bl_idname = "svn.checkout_finalize"
    bl_label = "Finalize SVN Checkout"
    bl_description = "Checkout the specified SVN repository to the selected path"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        prefs = get_addon_prefs(context)
        repo = prefs.active_repo
        # `svn checkout` is an outlier in every way from other SVN commands:
        # - Credentials are provided with an equal sign
        # - We need live output in the console, but we don't need to store it.
        # - It needs to be able to run even if the current directory isn't a valid repo.
        # So, we're not going to use our `execute_subprocess` api here.
        self.execute_svn_command(
            context,
            ['svn', 'cleanup']
        )
        p = subprocess.Popen(
            ["svn", "checkout", f"--username={repo.username}",
                f"--password={repo.password}", repo.url, repo.display_name],
            shell=False,
            cwd=repo.directory+"/",
            stdout=subprocess.PIPE,
            start_new_session=True
        )
        repo.directory = str((Path(repo.directory) / repo.display_name))
        while True:
            line = p.stdout.readline().decode()
            print(line.replace("\n", ""))
            if not line:
                break
        prefs = get_addon_prefs(context)
        prefs.checkout_mode = False
        prefs.save_repo_info_to_file()
        Processes.start('Authenticate')
        return {'FINISHED'}


class SVN_OT_checkout_cancel(Operator):
    bl_idname = "svn.checkout_cancel"
    bl_label = "Cancel SVN Checkout"
    bl_description = "Cancel the checkout UI"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        prefs = get_addon_prefs(context)
        prefs.checkout_mode = False
        repo = prefs.active_repo
        if not repo.url and not repo.username and not repo.password and not repo.directory:
            prefs.repositories.remove(prefs.active_repo_idx)
        return {'FINISHED'}


registry = [
    SVN_OT_checkout_initiate,
    SVN_OT_checkout_finalize,
    SVN_OT_checkout_cancel
]
