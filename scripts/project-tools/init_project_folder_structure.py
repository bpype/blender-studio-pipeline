#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from pathlib import Path
import json
import shutil
import sys


def folder(path_string):
    """Determine if the value is a valid directory"""
    filepath = Path(path_string)

    if filepath.exists() and not filepath.is_dir():
        msg = f"Error! This is not a directory: {path_string}"
        raise argparse.ArgumentTypeError(msg)
    else:
        return filepath


parser = argparse.ArgumentParser(description="Generate project structure.")
parser.add_argument(
    'target_folder',
    metavar='<target_folder>',
    help="The target folder to initialize the project structure in.",
    type=folder
)
parser.add_argument(
    '--json_file',
    help="The json file with the folder structure. Will default to folder_structure.json",
    nargs='?',
    metavar='<json file>',
    default=Path(__file__).parent / "folder_structure.json",
    type=str
)


def create_folder_structure(cur_path, path_dict, source_folder):
    for path in path_dict:
        # Get next path to check for consistency
        next_path = (cur_path / path).resolve()
        nested_item = path_dict[path]
        if type(nested_item) is not dict:
            print("Checking file: %s" % next_path)
            # This is a file we should copy over
            if next_path.exists():
                continue
            print(f"Copying over: {next_path.name}")
            shutil.copy(source_folder / next_path.name, next_path)
        else:
            print("Checking path: %s" % next_path)
            if not next_path.exists():
                print(f"Creating folder: {next_path}")
                os.makedirs(next_path)
            create_folder_structure(next_path, nested_item, source_folder)


args = parser.parse_args()

with open(args.json_file) as json_file:
    path_dict = json.load(json_file)
    first_key = list(path_dict.keys())[0]
    create_folder_structure(Path(args.target_folder), path_dict[first_key], Path(__file__).parent)
    print("Done!")
