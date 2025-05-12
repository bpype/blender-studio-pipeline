#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import email.utils
import glob
import hashlib
import os
import pathlib
import requests
import shutil
import json

BUILDS_INDEX = "https://builder.blender.org/download/daily/?format=json&v=1"

# Use a value found in the "branch" property. For example "v33", "v34", "main", etc.
BLENDER_BRANCH = "main"


def download_file(url, out_folder):
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

# Get all urls for the blender builds
platforms_dict = {
    "windows": "zip",
    "darwin": "dmg",
    "linux": "xz",
}

download_info = []
branch_string = "+" + BLENDER_BRANCH
reqs = requests.get(BUILDS_INDEX)
available_downloads = json.loads(reqs.text)
for download in available_downloads:
    if download["branch"] != BLENDER_BRANCH:
        continue
    for platform in platforms_dict:
        if download["platform"] != platform:
            continue
        file_extension = platforms_dict[platform]
        if download["file_extension"] != file_extension:
            continue
        download_info.append((platform, download["url"], download["architecture"]))

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

    current_platform_file = glob.glob(f"{download_folder_path}/*{platform}.{arch}*{file_extension}")
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
