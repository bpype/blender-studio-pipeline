#!/usr/bin/env python3

import os
import hashlib
import json

json_file_path = ""  # File Path to write JSON File to
folder_path = ""  # Create Map for items in this folder recursively


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


def generate_json_for_directory(directory_path):
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


if __name__ == "__main__":
    directory_path = folder_path
    generate_json_for_directory(directory_path)
