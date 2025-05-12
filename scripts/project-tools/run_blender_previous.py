#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import filecmp
import sys
from run_blender import update_blender, launch_blender

# The project base path (where shared, local and svn are located)
PATH_BASE = Path(__file__).resolve().parent.parent.parent
PATH_ROLLBACK_LOCAL = PATH_BASE / 'local' / 'blender_previous'
PATH_ARTIFACTS = PATH_BASE / 'shared' / 'artifacts' / 'blender'
PATH_PREVIOUS = PATH_ARTIFACTS / 'previous'

cur_date_file = PATH_ROLLBACK_LOCAL / "download_date"

paths = sorted(Path(PATH_PREVIOUS).iterdir())

if cur_date_file.exists():
    with open(cur_date_file, 'r') as file:
        date = file.read().rstrip()
        print("Current build: \033[100m%s\033[0m" % date)
        print()

print("Available builds:\n")

for index, path in enumerate(paths):
    date_file = path / "download_date"
    if not date_file.exists():
        print("ERROR: The backup folder %s is missing a datefile, exiting!" % path)

    with open(date_file, 'r') as file:
        date = file.read().rstrip()

    if cur_date_file.exists() and filecmp.cmp(cur_date_file, date_file):
        print("\033[1mID:\033[0m\033[100m%3i (%s) <current>\033[0m" % (index, date))
    else:
        print("\033[1mID:\033[0m%3i (%s)" % (index, date))

num_prev_versions = len(paths)
input_error_mess = "Please select an index between 0 and " + str(num_prev_versions - 1) + " or press ENTER to launch current version"
selected_index = 0

if num_prev_versions == 0:
    print("No versions available to rollback to!")
    sys.exit(1)

while True:
    index_str = input("Select which Blender build number to run. (press ENTER to confirm): ")
    if index_str == "" and cur_date_file.exists():
        selected_index = -1
        break
    if not index_str.isnumeric():
        print(input_error_mess)
        continue
    index = int(index_str)
    if index >= 0 and index < num_prev_versions:
        selected_index = index
        break
    print(input_error_mess)

if selected_index > -1:
    update_blender(paths[selected_index], PATH_ROLLBACK_LOCAL)
launch_blender(PATH_ROLLBACK_LOCAL)
