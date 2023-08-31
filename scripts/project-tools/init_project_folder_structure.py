#!/usr/bin/env python3

import argparse
import os
import pathlib
import json
import shutil
import sys


def valid_dir_arg(value):
    """Determine if the value is a valid directory"""
    filepath = pathlib.Path(value)

    if not filepath.exists() or not filepath.is_dir():
        msg = f"Error! This is not a directory: {value}"
        raise argparse.ArgumentTypeError(msg)
    else:
        return filepath


def create_folder_structure(cur_path, path_dict, source_folder):
    for path in path_dict:
        # Get next path to check for consistency
        next_path = (cur_path / path).resolve()
        print("Checking path: %s" % next_path)
        nested_item = path_dict[path]
        if type(nested_item) is not dict:
            # This is a file we should copy over
            if next_path.exists():
                continue
            print(f"Copying over: {next_path.name}")
            shutil.copy(source_folder / next_path.name, next_path)
        else:
            print(f"Creating folder: {next_path}")
            os.makedirs(next_path)
            create_folder_structure(next_path, nested_item, source_folder)


def main(args):
    parser = argparse.ArgumentParser(description="Generate project structure.")
    parser.add_argument("-t", "--target", type=valid_dir_arg)
    args = parser.parse_args(args)
    target_folder = args.target or pathlib.Path.cwd().parent.parent
    folder_structure = pathlib.Path(__file__).parent / "folder_structure.json"

    with open(folder_structure) as json_file:
        path_dict = json.load(json_file)
        create_folder_structure(target_folder, path_dict["../../"], folder_structure.parent)
        print("Done!")


if __name__ == "__main__":
    main(sys.argv[1:])
