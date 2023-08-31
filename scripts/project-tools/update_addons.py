#!/usr/bin/env python3

import glob
import hashlib
import os
import pathlib
import requests


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


current_file_folder_path = pathlib.Path(__file__).parent
download_folder_path = (current_file_folder_path / "../../shared/artifacts/addons/").resolve()

# Ensure that the download directory exists
os.makedirs(download_folder_path, exist_ok=True)

download_file(
    "https://projects.blender.org/studio/blender-studio-pipeline/archive/main.zip",
    download_folder_path,
    "blender-studio-pipeline-main.zip",
)
