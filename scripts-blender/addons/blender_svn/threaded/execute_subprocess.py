# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
from typing import List
from ..util import get_addon_prefs


def get_credential_commands(context) -> List[str]:
    repo = context.scene.svn.get_repo(context)
    assert (
        repo.is_cred_entered
    ), "No username or password entered for this repository. The UI shouldn't have allowed you to get into a state where you can press an SVN operation button without having your credentials entered, so this is a bug!"
    return ["--username", f"{repo.username}", "--password", f"{repo.password}"]


def execute_command(path: str, command: str) -> str:
    output_bytes = subprocess.check_output(
        command,
        shell=False,
        cwd=path + "/",
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    return output_bytes.decode(encoding='utf-8', errors='replace')


def execute_svn_command(
    context,
    command: List[str],
    *,
    ignore_errors=False,
    print_errors=True,
    use_cred=False,
) -> str:
    """Execute an svn command in the root of the current svn repository.
    So any file paths that are part of the command should be relative to the
    SVN root.
    """
    repo = context.scene.svn.get_repo(context)
    if "svn" not in command:
        command.insert(0, "svn")

    if use_cred:
        command += get_credential_commands(context)

    command.append("--non-interactive")
    command.append("--trust-server-cert")

    prefs = get_addon_prefs(context)
    if prefs.debug_mode:
        print(" ".join(command))

    try:
        if repo.is_valid_svn:
            return execute_command(repo.directory, command)
    except subprocess.CalledProcessError as error:
        if ignore_errors:
            return ""
        else:
            err_msg = error.stderr.decode()
            if print_errors:
                print(f"Command returned error: {command}")
                print(err_msg)
            raise error


def check_svn_installed():
    code, message = subprocess.getstatusoutput('svn')
    return code != 127
