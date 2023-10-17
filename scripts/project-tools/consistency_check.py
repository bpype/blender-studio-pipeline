#!/usr/bin/env python3

import argparse
import os
import pathlib
import json


parser = argparse.ArgumentParser(description="Check if the folder structure matches that one in folder_structure.json")
parser.add_argument(
    '--create_json_file',
    help="Instead of checking, create a json file with the folder structure from the specified path",
    nargs=2,
    metavar=('<path_to_parse>', '<output_json_file>')
)


def create_path_dict(startpath, max_depth):
    path_structure_dict = {}
    start_folder_name = os.path.basename(start_search_path)
    for root, dirs, files in os.walk(startpath, followlinks=True):
        # We are only interested in the files and folders inside the start path.
        cur_path = root.replace(startpath, start_folder_name)
        level = cur_path.count(os.sep)
        # Sanity check. We don't expect the directory tree to be too deep.
        # Therefore, we will stop if we go too deep.
        # This avoids infinite loops that can happen when we follow symlinks
        if level > max_depth:
            print("We have gone too deep in the file structure, stopping...")
            exit(1)

        # Insert the data into the dictionary
        nested_dict = path_structure_dict
        key_path = cur_path.split(os.sep)
        final_key = key_path[-1]
        for key in key_path[:-1]:
            nested_dict = nested_dict[key]

        files_dict = {}
        for f in files:
            files_dict[f] = "file"

        nested_dict[final_key] = files_dict

        # Print the files structure to we can see the traversed file tree
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)

        for f in files:
            print('{}{}'.format(subindent, f))
    return path_structure_dict


def check_if_structure_is_consistent(cur_path, path_dict, error_list):
    for path in path_dict:
        # Get next path to check for consistency
        next_path = (cur_path / path).resolve()
        print("Checking path: %s" % next_path)
        if next_path.exists():
            nested_item = path_dict[path]
            if type(nested_item) is not dict:
                if next_path.is_file():
                    continue
                else:
                    # This must be a file, warn if it is not
                    error_list += ["ERROR: %s is not a file, when it should be!" % next_path]
            check_if_structure_is_consistent(next_path, nested_item, error_list)
        else:
            error_list += ["ERROR: %s doesn't exist!" % next_path]


args = parser.parse_args()

if args.create_json_file:

    start_search_path = args.create_json_file[0]
    output_file = args.create_json_file[1]
    path_dict = create_path_dict(start_search_path, 5)
    json_data = json.dumps(path_dict, indent=4)
    with open(output_file, "w") as outfile:
        outfile.write(json_data)
    exit(0)

# path_dict pre-generated. This is the stucture the consistency check will ensure is there
path_dict = {}
current_file_folder = pathlib.Path(__file__).parent
with open(current_file_folder / "folder_structure.json") as json_file:
    path_dict = json.load(json_file)

# TODO perhaps make a function to pretty print out the path_dict for easier inspection

error_list = []
check_if_structure_is_consistent(current_file_folder, path_dict, error_list)

print()
if len(error_list) == 0:
    print("Consistency check: PASSED")
    exit(0)
else:
    print("Consistency check: FAILED")
    print()
    for error in error_list:
        print(error)
# Exit with error as we didn't pass the consistency check
exit(1)
