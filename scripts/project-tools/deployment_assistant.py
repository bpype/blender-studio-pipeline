#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import json
from pathlib import Path
import sys
import platform


def print_header(text: str, level: int = 1):
    """
    Prints a header surrounded by asterisks.
    The higher the level, the more rows of asterisks above and below.
    """
    print()
    print()
    stars = '*' * max(20, len(text) + 4)
    for _ in range(level):
        print(stars)
    print(f"* {text.center(len(stars) - 4)} *")
    for _ in range(level):
        print(stars)


def run_script(args):
    """
    Run a script or command using subprocess and handle errors.
    """
    result = subprocess.run(args)
    if result.returncode != 0:
        print(f"Failed to run {args[0]}: {result.returncode}")
        sys.exit(result.returncode)


def main():
    # Run Blender for First Time
    print("Running Blender for the first time to initialize the environment...")

    print_header("Blender Studio Tools Deployment Assistant", 2)

    run_blender = Path(__file__).parent.joinpath("run_blender.py")
    set_blender_kitsu_prefs = Path(__file__).parent.joinpath("set_blender_kitsu_prefs.py")
    run_script(
        [run_blender.as_posix(), "--background", "--python", set_blender_kitsu_prefs.as_posix()]
    )

    print_header("Shortcut to launch Project Blender", 1)

    if platform.system() == "Linux":
        # On Windows, we need to run the update script in a new console window
        install_shortcut = Path(__file__).parent.joinpath("install_desktop_file.sh")
        run_script([install_shortcut.as_posix()])
        print("Shortcut Successfully created!")
    else:
        print("Skipping desktop file creation on non-Linux systems.")
        print("To learn how to create a desktop file, please refer to the documentation.")
        print("https://studio.blender.org/tools/td-guide/blender_setup#create-shortcut")
        return

    print_header("Completed! Deployment Assistant", 2)


if __name__ == "__main__":
    main()
