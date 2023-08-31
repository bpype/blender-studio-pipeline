#!/usr/bin/env python3

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


# The project base path (where shared, local and svn are located)
PATH_BASE = Path(__file__).resolve().parent.parent.parent
PATH_ARTIFACTS = PATH_BASE / 'shared' / 'artifacts'
PATH_LOCAL = PATH_BASE / 'local'


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

    plist_data = plistlib.loads(mount_output.encode('utf-8'))
    mount_point = plist_data['system-entities'][0]['mount-point']

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

    dst_path.mkdir(parents=True, exist_ok=True)
    shutil.move(src_path, dst_path)

    shutil.rmtree(temp_dir)


def update_addon(addon_zip_name, path_in_zip_to_extract=''):
    addon_zip_sha = addon_zip_name + '.sha256'
    # This is the file that records all toplevel folders/files installed by this addon
    # It is used to cleanup old files and folders when updating or removing addons
    addon_zip_files = addon_zip_name + '.files'

    # Check if we have the latest add-ons from shared
    addon_artifacts_folder = PATH_ARTIFACTS / 'addons'
    artifact_archive = addon_artifacts_folder / addon_zip_name
    artifact_checksum = addon_artifacts_folder / addon_zip_sha

    if not artifact_checksum.exists():
        logger.error("Missing file %s" % artifact_checksum)
        logger.error("Could not update add-ons")
        return

    local_checksum = PATH_LOCAL / addon_zip_sha

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, artifact_checksum):
            logger.info("Already up to date")
            return

    if not artifact_archive.exists():
        logger.error("Shasum exists but the archive file %s does not!" % artifact_archive)
        logger.error("Could not update add-ons")
        return

    # Extract the archive in a temp location and move the addons content to local
    tmp_dir = Path(tempfile.mkdtemp())

    # Extract the zip file to the temporary directory
    with zipfile.ZipFile(artifact_archive, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)

    # Get the path of the folder to copy
    src_path_base = tmp_dir / path_in_zip_to_extract
    dst_path_base = PATH_LOCAL / 'scripts' / 'addons'

    # Remove all files previously installed by the archive
    local_installed_files = PATH_LOCAL / addon_zip_files
    if local_installed_files.exists():
        with open(local_installed_files) as file:
            lines = [line.rstrip() for line in file]
        for folder in lines:
            shutil.rmtree(dst_path_base / folder)

    # Get a list of directories inside the given directory
    addons = [subdir.name for subdir in src_path_base.iterdir() if subdir.is_dir()]

    with open(local_installed_files, 'w') as f:
        for addon_name in addons:
            f.write("%s\n" % addon_name)

    for addon_name in addons:
        logger.debug("Moving %s" % addon_name)
        src_dir_addon = src_path_base / addon_name
        dst_dir_addon = dst_path_base / addon_name
        shutil.move(src_dir_addon, dst_dir_addon)

    # Clean up the temporary directory
    shutil.rmtree(tmp_dir)

    # Update the sha256 file
    shutil.copy(artifact_checksum, local_checksum)


def update_blender():
    system_name = platform.system().lower()
    architecture = platform.machine()

    # Check if we have the latest blender archive from shared
    artifacts_path = PATH_ARTIFACTS / 'blender'
    archive_name_pattern = "blender*" + system_name + "." + architecture + "*.sha256"

    # Look for the appropriate Blender archive for this system
    matched_archives = glob.glob(str(artifacts_path / archive_name_pattern))

    # Check if we found any files
    if len(matched_archives) != 1:
        if len(matched_archives) == 0:
            logger.error("No Blender archives found for this system!")
            logger.error("System is: %s %s" % (system_name, architecture))
            return
        else:
            logger.error(
                "More than one candidate archive was found for this system. Only one is allowed!"
            )
            logger.error("The following candidates were found: %s" % str(matched_archives))
            return

    blender_build_checksum = Path(matched_archives[0])
    blender_build_archive = blender_build_checksum.with_suffix('')

    if not blender_build_archive.exists():
        logger.error(
            "Shasum exists but the target Blender archive %s does not!" % blender_build_archive
        )
        logger.error("Could not update blender")
        return

    local_checksum = PATH_LOCAL / 'blender' / f"{system_name}.sha256"

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, blender_build_checksum):
            logger.info("Already up to date")
            return

    src = artifacts_path / blender_build_archive
    dst = PATH_LOCAL / 'blender' / system_name
    if dst.exists():
        shutil.rmtree(dst)

    if system_name == 'linux':
        extract_tar_xz(src, dst)
    elif system_name == 'darwin':
        extract_dmg(src, 'Blender.app', dst)
    elif system_name == 'windows':
        extract_zip(src, dst)
    shutil.copy(blender_build_checksum, local_checksum)


def launch_blender():
    system_name = platform.system().lower()
    blender_path_base = PATH_LOCAL / 'blender' / system_name
    if system_name == 'linux':
        blender_path = blender_path_base / 'blender'
    elif system_name == 'darwin':
        blender_path = blender_path_base / 'Blender.app' / 'Contents' / 'MacOS' / 'Blender'
    elif system_name == 'windows':
        blender_path = blender_path_base / 'blender.exe'
    else:
        sys.exit(1)

    os.environ['BLENDER_USER_CONFIG'] = str(PATH_LOCAL / 'config')
    os.environ['BLENDER_USER_SCRIPTS'] = str(PATH_LOCAL / 'scripts')
    subprocess.run([blender_path])


def update_addons():
    path_in_zip_to_extract = Path('blender-studio-pipeline/scripts-blender/addons')
    update_addon('blender-studio-pipeline-main.zip', path_in_zip_to_extract)


if __name__ == '__main__':
    logger.info('Updating Add-ons')
    update_addons()
    logger.info('Updating Blender')
    update_blender()
    logger.info('Launching Blender')
    launch_blender()
