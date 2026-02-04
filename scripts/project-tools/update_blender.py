#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
from dataclasses import dataclass
import email.utils
import glob
import hashlib
import os
import pathlib
from typing import TypedDict, cast
import requests
import shutil
import json

# Example usage:
# ./update_blender.py --platform windows linux

BUILDS_INDEX = "https://builder.blender.org/download/daily/?format=json&v=1"
BUILDS_INDEX_ARCHIVE = "https://builder.blender.org/download/daily/archive/?format=json&v=1"

# Use a value found in the "branch" property. For example "v33", "v34", "main", etc.
BLENDER_BRANCH = "main"

# Filter specific builds types when not on the main branch For example, "stable", "beta", "alpha" or "candidate".
VALID_RISK_ID = "stable"

# Dictionary containing all platforms to download and their filetype
platforms_dict = {
    "windows": "zip",
    "darwin": "dmg",
    "linux": "xz",
}


class BlenderBuildData(TypedDict):
    branch: str
    risk_id: str
    version: str
    platform: str
    file_extension: str
    url: str
    architecture: str


# Get all urls for the blender builds
def get_all_download_urls(build_index_url: str, exit_if_missing: bool):
    download_info: list[tuple[str, str, str]] = []
    found_plaforms: set[str] = set()
    reqs = requests.get(build_index_url)
    available_downloads = cast(list[BlenderBuildData], json.loads(reqs.text))
    check_version = build_index_url == BUILDS_INDEX_ARCHIVE
    target_version = None

    if check_version:
        highest_subversion = -1
        for download in available_downloads:
            if download["branch"] != BLENDER_BRANCH:
                continue

            if BLENDER_BRANCH != "main":
                # If we are not on the main branch, we only want builds of a certain risk id
                if download["risk_id"] != VALID_RISK_ID:
                    continue

            version = download["version"]
            subversion = int(version.split(".")[-1])
            if subversion > highest_subversion:
                highest_subversion = subversion
                target_version = version

    for download in available_downloads:
        if download["branch"] != BLENDER_BRANCH:
            continue

        if BLENDER_BRANCH != "main":
            # If we are not on the main branch, we only want builds of a certain risk id
            if download["risk_id"] != VALID_RISK_ID:
                continue

        if check_version:
            if download["version"] != target_version:
                continue

        for platform in platforms_dict:
            if download["platform"] != platform:
                continue
            file_extension = platforms_dict[platform]
            if download["file_extension"] != file_extension:
                continue
            download_info.append((platform, download["url"], download["architecture"]))
            found_plaforms.add(platform)

    missing_platforms = platforms_dict.keys() - found_plaforms
    if len(missing_platforms) != 0:
        if exit_if_missing:
            print(f"The following platforms were not found for download: {missing_platforms}")
            print(
                "Exiting! Either remove the missing platforms from the platforms_dict or look into why they are not available"
            )
            exit(1)
        else:
            return None
    return download_info


def download_file(url: str, out_folder: pathlib.Path):
    print("Downloading: " + url)
    local_filename = out_folder / url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    f.write(chunk)
    return local_filename


def shasum_matches(file, sha_sum):
    with open(file, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        return digest.hexdigest() == sha_sum


def update_blender(download_info):
    current_file_folder_path = pathlib.Path(__file__).parent
    download_folder_path = (current_file_folder_path / "../../shared/artifacts/blender").resolve()
    backup_folder_path = download_folder_path / "previous/current_snapshot"
    # This can happen if someone has run the rollback script, so we need to check for it.
    backup_exists = (download_folder_path / "previous/00").exists()

    os.makedirs(download_folder_path, exist_ok=True)

    if not backup_exists:
        # Backup the old files
        os.makedirs(backup_folder_path, exist_ok=True)

        for f in os.listdir(download_folder_path):
            path_to_file = download_folder_path / f
            if path_to_file.is_file():
                shutil.copy(path_to_file, backup_folder_path)

    updated_current_files = False
    new_files_downloaded = False
    # Download new builds if the shasums doesn't match
    for info in download_info:
        platform = info[0]
        file_extension = platforms_dict[platform]
        url = info[1]
        url_sha = url + ".sha256"
        sha = requests.get(url_sha).text.strip().lower()
        arch = info[2]

        current_platform_file = glob.glob(
            f"{download_folder_path}/*{platform}.{arch}*{file_extension}"
        )
        if len(current_platform_file) > 1:
            print(
                f"Platform {platform} has multiple downloaded files in the artifacts directory, exiting!"
            )
            exit(1)
        # Check if we need to download the file by looking at the shasum of the currently downloaded file (if any)
        if len(current_platform_file) == 1:
            current_file = current_platform_file[0]
            if shasum_matches(current_file, sha):
                # We already have the current file
                continue
            else:
                updated_current_files = True
                os.remove(current_file)
                os.remove(current_file + ".sha256")

        download_file(url_sha, download_folder_path)
        downloaded_file = download_file(url, download_folder_path)
        # Check that the file we downloaded is not corrupt
        if not shasum_matches(downloaded_file, sha):
            print(f"Downloaded file {downloaded_file} does not match its shasum, exiting!")
            exit(1)
        new_files_downloaded = True

    if new_files_downloaded:
        # Save download date for use in the rollback script
        with open(download_folder_path / "download_date", "w") as date_file:
            date_file.write(email.utils.formatdate(localtime=True))
        print("Updated to the latest files")

    if updated_current_files:
        backup_path = download_folder_path / "previous"
        if not backup_exists:
            # Put the current backup first in the directory listing
            os.rename(backup_folder_path, backup_path / "00")
        backup_dirs = os.listdir(backup_path)
        backup_dirs.sort(reverse=True)

        # Remove older backup folders if there are more than 10
        folders_to_remove = len(backup_dirs) - 10
        if folders_to_remove > 0:
            for dir in backup_dirs[:folders_to_remove]:
                shutil.rmtree(backup_path / dir)
            backup_dirs = backup_dirs[folders_to_remove:]

        # Bump all folder names
        # Assign a number to each file, reverse the processing order to not overwrite any files.
        folder_number = len(backup_dirs)
        for dir in backup_dirs:
            old_dir = backup_path / dir
            os.rename(old_dir, backup_path / str(folder_number).zfill(2))
            folder_number -= 1
    else:
        if not backup_exists:
            shutil.rmtree(backup_folder_path)
        if not new_files_downloaded:
            print("Nothing downloaded, everything was up to date")


@dataclass
class Arguments(argparse.Namespace):
    """Define argument types parsed with argparse"""

    platform: list[str] | None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update blender script, downloads Blender for the given platforms"
    )
    parser.add_argument(
        "-P",
        "--platform",
        type=str,
        nargs="+",
        choices=["windows", "darwin", "linux"],
        help="Download Blender for the specified platforms",
    )
    args = parser.parse_args(namespace=Arguments)

    if BLENDER_BRANCH == "main":
        download_info = get_all_download_urls(BUILDS_INDEX, True)
    else:
        download_info = get_all_download_urls(BUILDS_INDEX, False)
        if not download_info:
            # We are not able to get the builds we want from the latest snapshots, check if we can from the archive.
            download_info = get_all_download_urls(BUILDS_INDEX_ARCHIVE, True)

    if not download_info:
        raise ValueError("No download info")

    # Filter platforms if passed as argument
    if args.platform:
        download_info = [info for info in download_info if info[0] in args.platform]

    update_blender(download_info)
