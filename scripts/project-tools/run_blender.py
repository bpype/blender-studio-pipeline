#!/usr/bin/env python3

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


def update_addon(addon_zip_name):
    addon_zip_sha = addon_zip_name + '.sha256'
    # This is the file that records all toplevel folders/files installed by this addon
    # It is used to cleanup old files and folders when updating or removing addons
    addon_zip_files = addon_zip_name + '.files'

    # Check if we have the latest add-ons from shared
    addon_artifacts_folder = PATH_ARTIFACTS / 'addons'
    artifact_archive = addon_artifacts_folder / addon_zip_name
    artifact_checksum = addon_artifacts_folder / addon_zip_sha
    local_artifact_dir = PATH_LOCAL / 'artifacts' / 'addons'

    # Sanity check
    if not local_artifact_dir.exists():
        local_artifact_dir.mkdir(parents=True, exist_ok=True)

    if not artifact_checksum.exists():
        logger.error("Missing file %s" % artifact_checksum)
        logger.error("Could not update add-ons")
        return

    local_checksum = local_artifact_dir / addon_zip_sha

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, artifact_checksum):
            logger.debug("Addon is up to date: " + addon_zip_name)
            return

    if not artifact_archive.exists():
        logger.error("Shasum exists but the archive file %s does not!" % artifact_archive)
        logger.error("Could not update add-ons")
        return

    logger.info("Updating addon from: " + addon_zip_name)

    # Extract the archive in a temp location and move the addons content to local
    src_path_base = Path(tempfile.mkdtemp())

    # Extract the zip file to the temporary directory
    with zipfile.ZipFile(artifact_archive, 'r') as zip_ref:
        zip_ref.extractall(src_path_base)

    dst_path_base = PATH_LOCAL / 'scripts' / 'addons'

    # Remove all files previously installed by the archive
    local_installed_files = local_artifact_dir / addon_zip_files
    if local_installed_files.exists():
        with open(local_installed_files) as file:
            lines = [line.rstrip() for line in file]
        for file in lines:
            old_file = dst_path_base / file
            if old_file.exists():
                shutil.rmtree(old_file)

    # Get a list of the top level content of the addon in case it doesn't just contain one folder
    addon_top_level_files = [entry.name for entry in src_path_base.iterdir()]

    with open(local_installed_files, 'w') as f:
        for addon_file in addon_top_level_files:
            f.write("%s\n" % addon_file)

    for addon_file in addon_top_level_files:
        logger.debug("Moving %s" % addon_file)
        src_dir_addon = src_path_base / addon_file
        dst_dir_addon = dst_path_base / addon_file
        shutil.move(src_dir_addon, dst_dir_addon)

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

    local_checksum = local_blender_path / f"{system_name}.sha256"

    if local_checksum.exists():
        if filecmp.cmp(local_checksum, blender_build_checksum):
            logger.debug("Blender is already up to date")
            return

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

    # Sanity check
    if not config_path.exists():
        config_path.mkdir(parents=True, exist_ok=True)
    if not script_path.exists():
        script_path.mkdir(parents=True, exist_ok=True)

    os.environ['BLENDER_USER_CONFIG'] = str(config_path)
    os.environ['BLENDER_USER_SCRIPTS'] = str(script_path)
    proc = subprocess.run([blender_path])
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


def update_addons():
    addon_artifacts_folder = PATH_ARTIFACTS / 'addons'
    if not addon_artifacts_folder.exists():
        logger.info("Addon artifacts folder not found at: " + str(addon_artifacts_folder))
        logger.info("Skipping addon updates.")
        return
    addons_list = [entry.name for entry in addon_artifacts_folder.iterdir() if entry.suffix == ".zip"]
    for zip_name in addons_list:
        update_addon(zip_name)


if __name__ == '__main__':

    args = parser.parse_args()

    if args.blender_path != "no_alt_binary":
        blender_path = Path(args.blender_path)
        if not blender_path.exists():
            logger.fatal("Can't run Blender! The supplied path does not exist!")
            sys.exit(1)
        run_blender(blender_path)

    logger.info('Updating Add-ons')
    update_addons()
    logger.info('Updating Blender')
    update_blender()
    logger.info('Launching Blender')
    launch_blender()
