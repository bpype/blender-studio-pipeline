#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import hashlib
import json
import os

JSON_FILE_KEY = 'json_file_path'
CRAWL_DIR_KEY = 'folder_path'


def get_current_dir():
    return Path(__file__).parent.resolve()


def get_variable_file_path():
    directory = get_current_dir()
    variables_dir = directory.joinpath("var")
    if not variables_dir.exists():
        variables_dir.mkdir()
    return variables_dir.joinpath("remap_variables.json")


def get_variable_file():
    env_file = get_variable_file_path()
    if env_file.exists():
        return env_file


def remove_variable_file():
    env_file = get_variable_file_path()
    Path.unlink(env_file)


def get_variables():
    var_file = Path(get_variable_file())
    var_file_data = open(var_file)
    var_file_dict = json.load(var_file_data)

    return var_file_dict


def set_variable_file():
    file_path = get_variable_file_path()
    variables = {}

    dir_to_map = get_dir_to_map()
    json_file = get_josn_file_dir()

    variables[JSON_FILE_KEY] = f"{json_file}"
    variables[CRAWL_DIR_KEY] = f"{dir_to_map}"

    with open(file_path, 'w') as json_file:
        json.dump(variables, json_file, indent=4)
    return variables


def get_dir_recursively(prompt: str):
    iterations = 0
    dir_to_map = input(prompt)
    if Path(dir_to_map).is_dir():
        iterations += 1
        return dir_to_map
    if iterations > 10:
        raise Exception('Provided path is not a directory')
    else:
        print('Provided path is not a directory')
        return get_dir_recursively(prompt)


def get_dir_to_map() -> str:
    return get_dir_recursively("Please enter directory to map: ")


def get_josn_file_dir() -> str:
    json_dir = get_dir_recursively("Please enter directory to store JSON map: ")
    return Path(json_dir).joinpath("dir_map.json").__str__()


def get_bbatch_command():
    directory = get_current_dir()
    source_file = directory.joinpath('remap_blender_paths.py')
    variables = get_variables()
    print(
        "To update your .blend file references open the bbatch directory and run the following command"
    )
    print(
        f'python -m bbatch {variables[CRAWL_DIR_KEY]} --nosave --recursive --script {source_file} --args "{variables[JSON_FILE_KEY]}"'
    )


def generate_checksum(filepath: str) -> str:
    """
    Generate a checksum for a zip file
    Arguments:
        archive_path: String of the archive's file path
    Returns:
        sha256 checksum for the provided archive as string
    """
    with open(filepath, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest()


def generate_json_for_directory(directory_path, json_file_path):
    # TODO Centralize duplicate code from 'update_json_for_directory()'
    data = {}

    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            sha256 = generate_checksum(file_path)

            if sha256 in data:
                data[sha256]['old'].append(file_path)
            else:
                data[sha256] = {'old': [file_path], 'new': ''}
                print(f"Making hash for {file_name}")

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def update_json_for_directory(directory_path, json_file_path):
    file_map_json = Path(json_file_path)
    file_map_data = open(file_map_json)
    file_map_dict = json.load(file_map_data)

    data = file_map_dict

    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            sha256 = generate_checksum(file_path)

            if not data.get(sha256):
                print(f"Cannot find file in dict {file_path}")
                continue

            if sha256 in data:
                data[sha256]['new'] = file_path
                print(f"Updating path for {file_path}")

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def main():
    if not get_variable_file():
        print("Starting new remap session")
        variables = set_variable_file()
        print(f"Generating map for directory '{variables[CRAWL_DIR_KEY]}'")
        generate_json_for_directory(variables[CRAWL_DIR_KEY], variables[JSON_FILE_KEY])
        print(
            f"Directory '{variables[CRAWL_DIR_KEY]}' can now be re-organized before re-running this tool to update it's map"
        )

    else:
        variables = get_variables()
        answer = input(
            f"Continune with existing session to update map for dir '{variables[CRAWL_DIR_KEY]}'? yes or no: "
        )
        answer_lw = answer.lower()
        if answer_lw == "yes" or answer_lw == 'y':
            print(f"Updating map for directory '{variables[CRAWL_DIR_KEY]}'")
            update_json_for_directory(
                variables[CRAWL_DIR_KEY], variables[JSON_FILE_KEY]
            )
            print('Map update is complete')
            get_bbatch_command()
        elif answer_lw == "no" or answer_lw == 'n':
            remove_variable_file()
            main()
        else:
            print("Please enter yes or no.")


if __name__ == "__main__":
    print("Welcome to 'remap', a tool to assist in a re-organization of folders")
    main()
