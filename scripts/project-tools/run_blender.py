#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import filecmp
import glob
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

from pathlib import Path


parser = argparse.ArgumentParser(description="Run Blender for the local project.")
parser.add_argument(
    'blender_path',
    metavar='<blender_path>',
    nargs='?',
    help="If a path to a blender binary is supplied, skip all update logic and run that blender binary with the project environmental variables.",
    type=str,
    default='no_alt_binary',
)
parser.add_argument(
    '--only-update',
    help="Only update the local install of Blender/extensions, don't launch Blender.",
    action='store_true'
)

parser.add_argument(
    "--python",
    metavar="<python_script>",
    help="Run the given Python script file.",
    type=str,
    nargs='?',
)

parser.add_argument(
    "--background",
    help="Run in background (often used for UI-less rendering).",
    action='store_true',
)

# The project base path (where shared, local and svn are located)
PATH_BASE = Path(__file__).parent.parent.parent
PATH_ARTIFACTS = PATH_BASE / 'shared' / 'artifacts'
PATH_LOCAL = PATH_BASE / 'local'
PATH_CUSTOM_SPLASH = Path(__file__).parent / "custom_splash.png"


def setup_logger():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a StreamHandler that outputs log messages to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    # Create a formatter for the log messages
    formatter = logging.Formatter('%(levelname)s - %(message)s')

    # Set the formatter for the StreamHandler
    stream_handler.setFormatter(formatter)

    # Add the StreamHandler to the logger
    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()


def extract_dmg(dmg_file: Path, internal_pah, dst_path: Path):
    # Execute hdiutil to mount the dmg file
    mount_process = subprocess.run(
        ['hdiutil', 'attach', dmg_file, '-plist'], capture_output=True, text=True
    )
    mount_output = mount_process.stdout

    # Parse the mount_output to retrieve the mounted volume name
    import plistlib

    mount_point = None
    plist_data = plistlib.loads(mount_output.encode('utf-8'))
    for entry in plist_data['system-entities']:
        if entry['content-hint'] == 'Apple_HFS':
            mount_point = entry['mount-point']
            break

    if mount_point == None:
        logger.fatal("Could not find the dmg mount point after mounting %s" % dmg_file.name)
        sys.exit(1)

    # Ensure destination directory exists
    dst_path = dst_path / internal_pah
    dst_path.mkdir(parents=True, exist_ok=True)

    # Extract the contents of the mounted dmg to the destination directory
    file_in_dmg = os.path.join(mount_point, internal_pah)
    subprocess.run(['ditto', file_in_dmg, dst_path])

    # Unmount the dmg file
    subprocess.run(['hdiutil', 'detach', mount_point])


def extract_tar_xz(file_path: Path, dst_path: Path):
    dst_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'tar',
            'xf',
            file_path,
            '--directory',
            dst_path,
            '--strip-components=1',
            '--checkpoint=.1000',
        ]
    )


def extract_zip(file_path: Path, dst_path: Path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    try:
        src_path = [subdir for subdir in Path(temp_dir).iterdir()][0]
    except IndexError:
        logger.fatal("The archive %s does not contain any directory" % file_path.name)
        sys.exit(1)

    shutil.move(src_path, dst_path)

    shutil.rmtree(temp_dir)


def update_extension(extension_zip_name, src_folder_name='extensions', dst_path_base=PATH_LOCAL / 'extensions' / 'system'):
    extension_zip_sha = extension_zip_name + '.sha256'
    # This is the file that records all toplevel folders/files installed by this extension
    # It is used to cleanup old files and folders when updating or removing extensions
    extension_zip_files = extension_zip_name + '.files'

    # Check if we have the latest extensions from shared
    extension_artifacts_folder = PATH_ARTIFACTS / src_folder_name
    artifact_archive = extension_artifacts_folder / extension_zip_name
    artifact_checksum = extension_artifacts_folder / extension_zip_sha
    local_artifact_dir = PATH_LOCAL / 'artifacts' / src_folder_name

    # Sanity check
    if not local_artifact_dir.exists():
        local_artifact_dir.mkdir(parents=True, exist_ok=True)

    if not artifact_checksum.exists():
        logger.error("Missing file %s" % artifact_checksum)
        logger.error("Could not update extension")
        return

    local_checksum = local_artifact_dir / extension_zip_sha

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, artifact_checksum):
            logger.debug("Extension is up to date: " + extension_zip_name)
            return

    if not artifact_archive.exists():
        logger.error("Shasum exists but the archive file %s does not!" % artifact_archive)
        logger.error("Could not update extensions")
        return

    logger.info("Updating extension from: " + extension_zip_name)

    # Extract the archive in a temp location and move the extensions content to local
    src_path_base = Path(tempfile.mkdtemp())

    # Extract the zip file to the temporary directory
    with zipfile.ZipFile(artifact_archive, 'r') as zip_ref:
        zip_ref.extractall(src_path_base)

    # Remove all files previously installed by the archive
    local_installed_files = local_artifact_dir / extension_zip_files
    if local_installed_files.exists():
        with open(local_installed_files) as file:
            lines = [line.rstrip() for line in file]
        for file in lines:
            old_file = dst_path_base / file
            if old_file.exists():
                shutil.rmtree(old_file)

    # Get a list of the top level content of the extension in case it doesn't just contain one folder
    extension_top_level_files = [entry.name for entry in src_path_base.iterdir()]

    with open(local_installed_files, 'w') as f:
        for extension_file in extension_top_level_files:
            f.write("%s\n" % extension_file)

    for extension_file in extension_top_level_files:
        logger.debug("Moving %s" % extension_file)
        src_dir_extension = src_path_base / extension_file
        dst_dir_extension = dst_path_base / extension_file
        shutil.move(src_dir_extension, dst_dir_extension)

    # Clean up the temporary directory
    shutil.rmtree(src_path_base)

    # Update the sha256 file
    shutil.copy(artifact_checksum, local_checksum)


def update_blender(artifacts_path = PATH_ARTIFACTS / 'blender', local_blender_path = PATH_LOCAL / 'blender'):
    system_name = platform.system().lower()
    architecture = platform.machine()

    # Check if we have the latest blender archive from shared
    archive_name_pattern = "blender*" + system_name + "." + architecture + "*.sha256"

    # Look for the appropriate Blender archive for this system
    matched_archives = glob.glob(str(artifacts_path / archive_name_pattern))

    # Check if we found any files
    if len(matched_archives) != 1:
        if len(matched_archives) == 0:
            logger.fatal("No Blender archives found for this system!")
            logger.fatal("System is: %s %s" % (system_name, architecture))
            sys.exit(1)
        else:
            logger.fatal(
                "More than one candidate archive was found for this system. Only one is allowed!"
            )
            logger.fatal("The following candidates were found: %s" % str(matched_archives))
            sys.exit(1)

    blender_build_checksum = Path(matched_archives[0])
    blender_build_archive = blender_build_checksum.with_suffix('')

    if not blender_build_archive.exists():
        logger.fatal(
            "Shasum exists but the target Blender archive %s does not!" % blender_build_archive
        )
        logger.fatal("Could not update blender")
        sys.exit(1)

    local_checksum = local_blender_path / f"{system_name}.sha256"

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, blender_build_checksum):
            logger.debug("Blender is already up to date")
            return
        else:
            os.remove(local_checksum)

    src = artifacts_path / blender_build_archive
    dst = local_blender_path / system_name
    if dst.exists():
        shutil.rmtree(dst)

    if system_name == 'linux':
        extract_tar_xz(src, dst)
    elif system_name == 'darwin':
        extract_dmg(src, 'Blender.app', dst)
    elif system_name == 'windows':
        extract_zip(src, dst)
    else:
        logger.fatal("Can't extract the blender binary archive, operating system: " + system_name)
        sys.exit(1)
    shutil.copy(blender_build_checksum, local_checksum)
    download_date_file = artifacts_path / 'download_date'
    if download_date_file.exists():
        shutil.copy(download_date_file, local_blender_path / 'download_date')


def run_blender(blender_path):
    config_path = PATH_LOCAL / 'config'
    script_path = PATH_LOCAL / 'scripts'
    extensions_path = PATH_LOCAL / 'extensions'

    # Sanity check
    if not config_path.exists():
        config_path.mkdir(parents=True, exist_ok=True)
    if not script_path.exists():
        script_path.mkdir(parents=True, exist_ok=True)

    os.environ['BLENDER_USER_CONFIG'] = str(config_path)
    os.environ['BLENDER_USER_SCRIPTS'] = str(script_path)
    os.environ['BLENDER_SYSTEM_EXTENSIONS'] = str(extensions_path)
    if PATH_CUSTOM_SPLASH.exists():
        os.environ['BLENDER_CUSTOM_SPLASH'] = str(PATH_CUSTOM_SPLASH)

    args = parser.parse_args()
    subprocess_args = [blender_path]

    if args.background:
        subprocess_args.append('--background')

    if args.python:
        subprocess_args.append('--python')
        subprocess_args.append(args.python)

    proc = subprocess.run(subprocess_args)
    if proc.returncode != 0:
        print("--- Blender seems to have crashed ---")
    sys.exit(proc.returncode)


def launch_blender(local_blender_path = PATH_LOCAL / 'blender'):
    system_name = platform.system().lower()
    blender_path_base = local_blender_path / system_name
    if system_name == 'linux':
        blender_path = blender_path_base / 'blender'
    elif system_name == 'darwin':
        blender_path = blender_path_base / 'Blender.app' / 'Contents' / 'MacOS' / 'Blender'
    elif system_name == 'windows':
        blender_path = blender_path_base / 'blender.exe'
    else:
        logger.fatal("Can't run Blender! Unsupported operating system: " + system_name)
        sys.exit(1)

    if not blender_path.exists():
        logger.fatal("Can't run Blender! No blender executable available for system: " + system_name)
        sys.exit(1)

    run_blender(blender_path)


def update_extensions():
    extension_artifacts_folder = PATH_ARTIFACTS / 'extensions'
    if not extension_artifacts_folder.exists():
        logger.info("Extension artifacts folder not found at: " + str(extension_artifacts_folder))
        logger.info("Skipping extension updates.")
        return
    extensions_list = [entry.name for entry in extension_artifacts_folder.iterdir() if entry.suffix == ".zip" and entry.name[0] != "."]
    local_artifact_dir = PATH_LOCAL / 'artifacts' / 'extensions'
    # Remove extensions that doesn't exist in the artifact directory anymore.
    if local_artifact_dir.exists():
        local_extension_list = [entry.stem for entry in local_artifact_dir.iterdir() if entry.suffix == ".files"]
        extensions_to_remove = set(local_extension_list) - set(extensions_list)
        for extension in extensions_to_remove:
            logger.info("Removing extension: " + extension)
            extension_files = local_artifact_dir / (extension + ".files")
            extension_checksum = local_artifact_dir / (extension + ".sha256")
            with open(extension_files) as file:
                lines = [line.rstrip() for line in file]
            for file in lines:
                old_file = PATH_LOCAL / 'extensions' / file
                if old_file.exists():
                    shutil.rmtree(old_file)
            extension_files.unlink()
            if extension_checksum.exists():
                extension_checksum.unlink()

    for zip_name in extensions_list:
        update_extension(zip_name)


def update_presets():
    preset_artifacts_folder = PATH_ARTIFACTS / 'presets'
    if not preset_artifacts_folder.exists():
        logger.info("Presets artifacts folder not found at: " + str(preset_artifacts_folder))
        logger.info("Skipping preset updates.")
        return
    presets_list = [entry.name for entry in preset_artifacts_folder.iterdir() if entry.suffix == ".zip" and entry.name[0] != "."]
    for zip_name in presets_list:
        update_extension(zip_name, 'presets', PATH_LOCAL / 'scripts' / 'presets')

if __name__ == '__main__':

    args = parser.parse_args()

    if args.blender_path != "no_alt_binary":
        blender_path = Path(args.blender_path)
        if not blender_path.exists():
            logger.fatal("Can't run Blender! The supplied path does not exist!")
            sys.exit(1)
        run_blender(blender_path)

    logger.info('Updating Extensions')
    update_extensions()
    logger.info('Updating Presets')
    update_presets()
    logger.info('Updating Blender')
    update_blender()
    if args.only_update:
        sys.exit(0)
    logger.info('Launching Blender')
    launch_blender()
