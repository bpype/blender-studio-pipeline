#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import filecmp
import os
import shutil
import sys

# The project base path (where shared, local and svn are located)
PATH_BASE = Path(__file__).resolve().parent.parent.parent
PATH_ARTIFACTS = PATH_BASE / 'shared' / 'artifacts' / 'blender'
PATH_PREVIOUS = PATH_ARTIFACTS / 'previous'
BACKUP_DIR = PATH_PREVIOUS / '00'

if not BACKUP_DIR.exists():
    BACKUP_DIR.mkdir()
    # Backup the current files
    for file in PATH_ARTIFACTS.iterdir():
        if file.is_file():
            shutil.copy(file, BACKUP_DIR)

cur_date_file = PATH_ARTIFACTS / "download_date"

paths = sorted(Path(PATH_PREVIOUS).iterdir())

print("Available builds:\n")

for index, path in enumerate(paths):
    date_file = path / "download_date"
    if not date_file.exists():
        print("ERROR: The backup folder %s is missing a datefile, exiting!" % path)

    with open(date_file, 'r') as file:
        date = file.read().rstrip()

    if filecmp.cmp(cur_date_file, date_file):
        print("\033[1mID:\033[0m\033[100m%3i (%s) <current>\033[0m" % (index, date))
    else:
        print("\033[1mID:\033[0m%3i (%s)" % (index, date))

num_prev_versions = len(paths)
input_error_mess = "Please select an index between 0 and " + str(num_prev_versions - 1)
selected_index = 0

if num_prev_versions == 0:
    print("No versions available to rollback to!")
    sys.exit(1)

while True:
    index_str = input("Select which Blender build number to switch to. (press ENTER to confirm): ")
    if not index_str.isnumeric():
        print(input_error_mess)
        continue
    index = int(index_str)
    if index >= 0 and index < num_prev_versions:
        selected_index = index
        break
    print(input_error_mess)

# Remove current files and move the selected snapshot into current folder
for file in PATH_ARTIFACTS.iterdir():
    if file.is_file():
        os.remove(file)

for file in paths[selected_index].iterdir():
    # Everything should be a file in here but have this check for sanity eitherway.
    if file.is_file():
        shutil.copy(file, PATH_ARTIFACTS)
