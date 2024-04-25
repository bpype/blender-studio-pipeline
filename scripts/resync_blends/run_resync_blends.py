#!/usr/bin/env python3

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from pathlib import Path
import argparse
import os
import subprocess
import sys
import time
import re


def cancel_program(message: str) -> None:
    """Cancel Execution of this file"""
    print(message)
    sys.exit(0)


parser = argparse.ArgumentParser()
parser.add_argument(
    "path",
    help="Path folder on which to perform crawl.",
)

parser.add_argument(
    "-e",
    "--exec",
    help="user must provide blender executable path.",
    type=str,
    required=True,
)

parser.add_argument(
    "-f",
    "--filter",
    help="Only crawl files with the matching regex.",
    type=str,
    required=False,
)

def get_bbatch_script_path() -> str:
    """Returns path to script that runs with bbatch"""
    dir = Path(__file__).parent.absolute()
    return str(dir.joinpath("resync_blend_file.py"))


def get_files_to_crawl(project_path: Path, name_filter=None):  # -> returns list of paths

    blend_files = [
        f for f in project_path.glob("**/*") if f.is_file() and f.suffix == ".blend"
    ]

    regex = None
    if name_filter:
        regex = re.compile(name_filter)

    epoch_time = int(time.time())
    resync_blend_files = []
    for blend_file in blend_files:
        # Skip files if they don't match
        if regex and not re.match(regex, blend_file.name):
            continue

        elapse_time = epoch_time - os.path.getctime(blend_file)
        # if file hasn't been saved in more than 24 hours, resync
        if not elapse_time > 86400:
            print("Skipping recently saved file:", str(blend_file))
            continue
        resync_blend_files.append(blend_file)
    return resync_blend_files


def main():
    """Resync Blender Files in a given folder"""
    args = parser.parse_args()
    project_path = Path(args.path)
    if not project_path.exists():
        cancel_program("Provided Path does not exist")
    exec_path = Path(args.exec)
    if not exec_path.exists():
        cancel_program("Provided Executable path does not exist")
    script_path = get_bbatch_script_path()
    files_to_craw = get_files_to_crawl(project_path, args.filter)
    if len(files_to_craw) < 1:
        cancel_program("No Files to resync")

    os.chdir("../bbatch")
    print("Resyncing Files...")
    cmd_list = [
        'python',
        '-m',
        'bbatch',
        "--nosave",
        "--recursive",
        '--script',
        script_path,
        '--exec',
        exec_path,
    ]

    for item in files_to_craw:
        cmd_list.insert(3, item)

    process = subprocess.Popen(cmd_list, shell=False)
    if process.wait() != 0:
        cancel_program(f"Resync Failed!")
    print("Resync Completed Successfully")
    return 0


if __name__ == "__main__":
    main()
