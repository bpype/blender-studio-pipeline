#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
from pathlib import Path
import shutil
import hashlib
from datetime import datetime, timezone
import argparse


REPO_ROOT_DIR = Path(__file__).parent.parent.parent
parser = argparse.ArgumentParser()
parser.add_argument(
    'output_folder',
    metavar='<output_folder>',
    help="The output folder where all the zips and shasums will be stored.",
    type=str,
)


def write_file(file_path, content):
    file = open(file_path, 'w')
    file.writelines(content)
    file.close()


def generate_checksum(archive_path):
    with open(archive_path, 'rb') as file:
        digest = hashlib.file_digest(file, "sha256")
    return digest.hexdigest()


def package_addons(addons_folder, output_folder):
    addon_dirs = [
        name
        for name in os.listdir(addons_folder)
        if os.path.isdir(addons_folder.joinpath(name))
    ]
    addon_output_dir = Path(output_folder)

    print("Packaging all addons to: " + output_folder)

    for dir in addon_dirs:
        directory = addons_folder / dir
        name = directory.name
        # As we are uploading addons with potentially non commited changes,
        # use the current UTC time as the version
        # version = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        version = "main"
        zip_name = Path(f"{name}-{version}")

        zipped_addon = shutil.make_archive(
            addon_output_dir / zip_name,
            'zip',
            directory.parent,
            directory.name,
        )
        checksum = generate_checksum(zipped_addon)
        chechsum_name = zip_name.with_suffix(".zip.sha256")
        checksum_path = addon_output_dir / chechsum_name
        checksum_file = write_file(
            checksum_path,
            f"{checksum} {name}-{version}.zip",
        )
        print("Successfully packaged: " + name)


args = parser.parse_args()
package_addons(REPO_ROOT_DIR / "scripts-blender/addons", args.output_folder)
