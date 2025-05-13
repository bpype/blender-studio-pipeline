#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import hashlib
from pathlib import Path
from urllib.request import urlretrieve
import sys
import requests
import glob
import os


def update_blender_studio_addons(download_folder_path: Path):
    if not download_folder_path.exists():
        print(
            f"Ensure script is run out of Project Tools directory {str(download_folder_path)} does not exist"
        )
        sys.exit(1)

    sha_file = download_folder_path.joinpath("blender_studio_add-ons_latest.zip.sha256")
    zip_file = download_folder_path.joinpath("blender_studio_add-ons_latest.zip")

    url_sha = "https://projects.blender.org/studio/blender-studio-tools/releases/download/latest/blender_studio_add-ons_latest.zip.sha256"
    url_zip = "https://projects.blender.org/studio/blender-studio-tools/releases/download/latest/blender_studio_add-ons_latest.zip"

    # Check current sha and early return if match
    web_sha = requests.get(url_sha).text.strip().lower()
    if sha_file.exists() & zip_file.exists():
        if shasum_matches(zip_file, web_sha):
            print(f"{zip_file.name} already up to date, canceling update")
            return
        else:
            # Remove current files
            if sha_file.exists():
                sha_file.unlink()
            if zip_file.exists():
                zip_file.unlink()

    print(f"Downloading {zip_file.name}......", end="")
    urlretrieve(url_zip, str(zip_file))
    print("Complete")
    print(f"Downloading {sha_file.name}......", end="")
    urlretrieve(url_sha, str(sha_file))
    print("Complete")

    if not shasum_matches(zip_file, web_sha):
        print(f"Downloaded file {zip_file.name} does not match its shasum, exiting!")
        exit(1)

    print("Blender Studio Add-Ons Successfully Updated for Current Project")
    print(
        "Blender Studio Add-Ons will be copied to your local directory next time you launch Blender via Projet Tools"
    )


def shasum_matches(file, sha_sum):
    with open(file, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        return sha_sum.startswith(digest.hexdigest())


def download_file(url, out_folder, filename):
    print("Downloading: " + url)
    local_filename = out_folder / filename

    # TODO Can't check any shasums before downloading so always remove and redownload everything for now
    prev_downloaded_files = glob.glob(f"{local_filename}*")
    for file in prev_downloaded_files:
        os.remove(file)

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=None):
                if chunk:
                    f.write(chunk)

    local_hash_filename = local_filename.with_suffix(".zip.sha256")
    with open(local_filename, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        with open(local_hash_filename, "w") as hash_file:
            hash_file.write(digest.hexdigest())

    return local_filename


current_file_folder_path = Path(__file__).parent
download_folder_path = (current_file_folder_path / "../../shared/artifacts/addons/").resolve()
update_blender_studio_addons(download_folder_path)

# Customize this script to download add-ons from other sources
# download_file(
#    "https://projects.blender.org/studio/blender-studio-tools/archive/main.zip",
#    download_folder_path,
#    "blender-studio-tools-main.zip",
# )
