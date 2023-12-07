from pathlib import Path
from .. import constants
import bpy


def find_file_version(published_file: Path) -> int:
    """Returns the version number from a published file's name

    Args:
        file (Path): Path to a publish file, naming convention is
        asset_name-v{3-digit_version}.blend`

    Returns:
        int: returns current version in filename as integer
    """
    name_without_ext = published_file.name.strip(".blend")

    # Support Legacy Delimiter
    # TODO Remove this is legacy code (coordinate with team)
    if "." in name_without_ext:
        return int(name_without_ext.split(".")[1].replace("v", ""))

    return int(name_without_ext.split(constants.FILE_DELIMITER)[1].replace("v", ""))


def get_next_published_file(
    current_file: Path, publish_type=constants.ACTIVE_PUBLISH_KEY
) -> Path:
    """Returns the path where the next published file version should be saved to

    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory
        publish_type (_type_, optional): Publish type, 'publish', 'staged', 'review'. Defaults to 'publish'.

    Returns:
        Path: Path where the next published file should be saved to, path doesn't exist yet
    """ """"""
    last_publish = find_latest_publish(current_file, publish_type)
    base_name = bpy.context.scene.asset_pipeline.name
    publish_dir = current_file.parent.joinpath(publish_type)
    if not last_publish:
        new_version_number = 1

    else:
        new_version_number = find_file_version(last_publish) + 1
    new_version = "{0:0=3d}".format(new_version_number)
    return publish_dir.joinpath(
        base_name + constants.FILE_DELIMITER + "v" + new_version + ".blend"
    )


def create_next_published_file(
    current_file: Path, publish_type=constants.ACTIVE_PUBLISH_KEY
) -> None:
    """Creates new Published version of a given Publish Type

    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory
        publish_type (_type_, optional): Publish type, 'publish', 'staged', 'review'. Defaults to 'publish'.
    """
    new_file_path = get_next_published_file(current_file, publish_type)
    if publish_type == constants.ACTIVE_PUBLISH_KEY:
        bpy.context.scene.asset_pipeline.asset_collection.asset_mark()
    bpy.ops.wm.save_as_mainfile(filepath=new_file_path.__str__(), copy=True)
    bpy.context.scene.asset_pipeline.asset_collection.asset_clear()


def find_all_published(current_file: Path, publish_type: str) -> list[Path]:
    """Retuns a list of published files of a given type,
    each publish type is seperated into its own folder at the
    root of the asset's directory
    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory
        publish_type (_type_, optional): Publish type, 'publish', 'staged', 'review'. Defaults to 'publish'.

    Returns:
        list[Path]: list of published files of a given publish type
    """
    publish_dir = current_file.parent.joinpath(publish_type)
    if not publish_dir.exists():
        return
    published_files = list(publish_dir.glob('*.blend'))
    published_files.sort(key=find_file_version)
    return published_files


def find_latest_publish(
    current_file: Path, publish_type=constants.ACTIVE_PUBLISH_KEY
) -> Path:
    """Returns the path to the latest published file in a given folder

    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory
        publish_type (_type_, optional): Publish type, 'publish', 'staged', 'review'. Defaults to 'publish'.

    Returns:
        Path: Path to latest publish file of a given publish type
    """
    published_files = find_all_published(current_file, publish_type)
    if published_files:
        return published_files[-1]


def find_sync_target(current_file: Path) -> Path:
    """Returns the latest published file to use as push/pull a.k.a sync target
    this will either be the latest active publish, or the latest staged asset if
    any asset is staged

    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory

    Returns:
       Path: Path to latest active or staged publish file
    """ """"""
    latest_staged = find_latest_publish(
        current_file, publish_type=constants.STAGED_PUBLISH_KEY
    )
    if latest_staged:
        return latest_staged
    return find_latest_publish(current_file, publish_type=constants.ACTIVE_PUBLISH_KEY)


def is_staged_publish(current_file: Path) -> bool:
    """Checks if there is a staged publish file, which
    will be used as the push/pull target.

    Args:
        current_file (Path): Current file, which must be a task file at root of asset directory

    Returns:
        bool: True if staged file exists
    """
    return bool(
        find_latest_publish(current_file, publish_type=constants.STAGED_PUBLISH_KEY)
    )
