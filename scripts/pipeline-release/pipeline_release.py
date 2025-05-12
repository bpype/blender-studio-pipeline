#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
import shutil
import hashlib
import subprocess
import tempfile
import sys
import requests
import json
from requests import Response

BASE_PATH = "https://projects.blender.org/api/v1"
REPO_PATH = '/studio/blender-studio-tools'
RELEASE_PATH = BASE_PATH + f'/repos{REPO_PATH}/releases'
TAG_PATH = BASE_PATH + f'/repos{REPO_PATH}/tags'
API_TOKEN = None

RELEASE_TITLE = "Blender Studio Add-Ons Latest"
RELEASE_VERSION = "latest"
RELEASE_DESCRIPTION = "Latest Release of Blender Studio Pipeline Add-Ons"

ZIP_NAME = "blender_studio_add-ons_latest"


def main():
    get_api_token()
    latest_release = get_release()
    temp_dir = Path(tempfile.mkdtemp(prefix=ZIP_NAME + "_"))
    release_files = create_latest_addons_zip(ZIP_NAME, temp_dir)
    remove_existing_release_assets(latest_release["id"])
    for file in release_files:
        upload_asset_to_release(latest_release["id"], file)
    shutil.rmtree(temp_dir)
    print("Blender Studio Add-Ons Successfully Released")


def remove_existing_release_assets(release_id: int) -> None:
    """Removes all existing release assets for the given release ID.

    Args:
        release_id (int): The ID of the release to remove assets from.

    Returns:
        None
    """

    all_assets = send_get_request(RELEASE_PATH + f"/{release_id}/assets").json()
    for asset in all_assets:
        if asset["name"] == ZIP_NAME + ".zip" or asset["name"] == ZIP_NAME + ".zip.sha256":
            send_delete_request(RELEASE_PATH + f"/{release_id}/assets/{asset['id']}")
            print(f"Deleted {asset['name']} created on: {asset['created_at']}")


def upload_asset_to_release(release_id: int, file: str) -> None:
    """Uploads an asset to the specified release.

    Args:
        release_id (int): The id of the release to upload to.
        file (str): The path to the file to upload.

    Returns:
        None
    """

    file_name = Path(file.name).name
    payload = open(file, 'rb')
    file_content = [
        ('attachment', (file_name, payload, 'application/zip')),
    ]
    print(f"Uploading '{file_name}'......", end="")
    response = requests.post(
        url=f"{RELEASE_PATH}/{release_id}/assets?name={file_name}&token={API_TOKEN}",
        files=file_content,
    )

    response.raise_for_status()

    if not response.status_code == 201:
        print(f"Failed to upload.")
    else:
        print(f"Completed")


def get_release() -> dict:
    """Gets the latest release matching the configured title and version.

    Removes any existing release with the same title and version first before
    returning the latest release to ensure it represents the current commit.

    Returns:
        dict: The release object for the latest matching release.
    """

    # Remove Previous Release so Release is always based on Current Commit
    for release in send_get_request(RELEASE_PATH).json():
        if release["name"] == RELEASE_TITLE and release["tag_name"] == RELEASE_VERSION:
            send_delete_request(RELEASE_PATH + f"/{release['id']}")
            send_delete_request(TAG_PATH + f"/{release['tag_name']}")
    return create_new_release()


def create_new_release() -> dict:
    """Create a new release on Gitea with the given title, version and description.

    Makes a POST request to the Gitea API to create a new release with the specified
    parameters. Checks if a tag with the same version already exists first. If not,
    creates the tag before creating the release.

    Returns:
        dict: The release object for the latest matching release.

    """
    # Create New Tag
    existing_tag = send_get_request(TAG_PATH + f'/{RELEASE_VERSION}')
    if existing_tag.status_code == 404:
        tag_content = {
            "message": RELEASE_DESCRIPTION,
            "tag_name": RELEASE_VERSION,
            "target": f"main",
        }

        send_post_request(TAG_PATH, tag_content)

    # Create New Release
    release_content = {
        "body": RELEASE_DESCRIPTION,
        "draft": False,
        "name": RELEASE_TITLE,
        "prerelease": False,
        "tag_name": RELEASE_VERSION,
        "target_commitish": "string",  # will default to latest
    }

    return send_post_request(RELEASE_PATH, release_content).json()


def get_api_token() -> None:
    """Get API token from environment file.

    Reads the API token from the api_token.env file and assigns it to the global
    API_TOKEN variable. Exits with error if file not found. Exists if API token is invalid.

    """
    global API_TOKEN
    api_token_file = Path(__file__).parent.joinpath("api_token.env")
    if not api_token_file.exists():
        print("API Token File not Found")
        sys.exit(1)
    API_TOKEN = open(api_token_file, 'r').read().strip()
    # Don't use send_get_request() so we can print custom error message to user
    response = requests.get(url=f"{BASE_PATH}/settings/api?token={API_TOKEN}")
    if response.status_code != 200:
        print("API Token is invalid")
        print(f"Error: {response.status_code}: '{response.reason}'")
        sys.exit(1)


def create_latest_addons_zip(name: str, temp_dir: Path):
    """Generate a pipeline release.

    Args:
        name (str): The name of the release.

    Returns:
        list: A list containing the path to the zipped release and checksum file.
    """

    output_dir = Path(temp_dir).joinpath(name)
    output_dir.mkdir()
    addons_dir = Path(__file__).parents[2].joinpath("scripts-blender/addons")

    zipped_release = shutil.make_archive(
        temp_dir.joinpath(name),
        'zip',
        addons_dir,
    )
    checksum = generate_checksum(zipped_release)
    chechsum_name = name + ".zip.sha256"
    checksum_path = temp_dir / chechsum_name
    write_file(
        checksum_path,
        f"{checksum} {name}.zip",
    )
    return [Path(zipped_release), Path(checksum_path)]


def write_file(file_path: Path, content: str) -> None:
    """Write content to file at given file path.

    Args:
        file_path (Path): Path to file to write to.
        content (str): Content to write to file.

    Returns:
        None
    """

    file = open(file_path, 'w')
    file.writelines(content)
    file.close()


def generate_checksum(archive_path: Path) -> str:
    """Generate checksum for archive file.

    Args:
        archive_path (Path): Path to archive file to generate checksum for.

    Returns:
        str: Hex digest string of checksum.
    """

    with open(archive_path, 'rb') as file:
        digest = hashlib.file_digest(file, "sha256")
    return digest.hexdigest()


def send_delete_request(url) -> Response:
    response = requests.delete(url=f"{url}?token={API_TOKEN}")
    if response.status_code != 204:
        print(f"Delete request for url: {url}\nFailed with error: {response.status_code}: '{response.reason}'")
        sys.exit(1)
    return response


def send_get_request(url: str) -> Response:
    response = requests.get(url=f"{url}?token={API_TOKEN}")
    if not (response.status_code == 200 or response.status_code == 404):
        print(f"Send request for: {url}\nFailed with error: {response.status_code}: '{response.reason}'")
        sys.exit(1)
    return response


def send_post_request(url: str, data: dict) -> Response:
    header_cont = {
        'Content-type': 'application/json',
    }
    response = requests.post(
        url=f"{url}?token={API_TOKEN}",
        headers=header_cont,
        data=json.dumps(data),
    )
    response_json = response.json()
    if response.status_code != 201:
        print(response_json["message"])
        sys.exit(1)
    return response


if __name__ == "__main__":
    main()
