#!/usr/bin/env python3

import os
import hashlib
import json
from pathlib import Path

json_file_path = ""  # File Path to read/write JSON File to
folder_path = ""  # Create Map for items in this folder recursively


gold_file_map_json = Path(json_file_path)
gold_file_map_data = open(gold_file_map_json)
gold_file_map_dict = json.load(gold_file_map_data)


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
    data = gold_file_map_dict

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


if __name__ == "__main__":
    directory_path = folder_path
    generate_json_for_directory(directory_path)
