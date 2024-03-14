import bpy
from pathlib import Path
from .. import bkglobals
from . import core
import json


OUTPUT_COL_CREATE = {
    "anim": True,
    "comp": False,
    "fx": True,
    "layout": True,
    "lighting": False,
    "previz": True,
    "rendering": False,
    "smear_to_mesh": False,
    "storyboard": True,
}

OUTPUT_COL_LINK_MAPPING = {
    "anim": None,
    "comp": ['anim', 'fx'],
    "fx": ['anim'],
    "layout": None,
    "lighting": ['anim'],
    "previz": None,
    "rendering": None,
    "smear_to_mesh": None,
    "storyboard": None,
}

LOAD_EDITORIAL_REF = {
    "anim": True,
    "comp": False,
    "fx": False,
    "layout": True,
    "lighting": False,
    "previz": False,
    "rendering": False,
    "smear_to_mesh": False,
    "storyboard": False,
}

ASSET_TYPE_TO_OVERRIDE = {
    "CH": True,  # Character
    "PR": True,  # Rigged Prop
    "LI": True,  # Library/Environment Asset
    "SE": False,  # Set
    "LG": True,  # Lighting Rig
    "CA": True,  # Camera Rig
}


def settings_filepath_get() -> Path:
    directory = core.get_shot_builder_config_dir(bpy.context)
    json_file_path = directory.joinpath(bkglobals.BUILD_SETTINGS_FILENAME)
    return json_file_path


def settings_dict_get(file_path_str: str = "") -> dict:
    if file_path_str == "":
        json_file_path = settings_filepath_get()
    else:
        json_file_path = Path(file_path_str)
    if not json_file_path.exists():
        return
    return json.load(open(json_file_path))


def settings_load(json_file_path: str = ""):
    global OUTPUT_COL_CREATE
    global OUTPUT_COL_LINK_MAPPING
    global LOAD_EDITORIAL_REF
    global ASSET_TYPE_TO_OVERRIDE

    json_content = settings_dict_get(json_file_path)

    if not json_content:
        return
    try:
        OUTPUT_COL_CREATE = json_content["OUTPUT_COL_CREATE"]
        OUTPUT_COL_LINK_MAPPING = json_content["OUTPUT_COL_LINK_MAPPING"]
        LOAD_EDITORIAL_REF = json_content["LOAD_EDITORIAL_REF"]
        ASSET_TYPE_TO_OVERRIDE = json_content["ASSET_TYPE_TO_OVERRIDE"]
        return True
    except KeyError:
        return


def filepath_get(filename: str = "") -> Path:
    config_dir = core.get_shot_builder_config_dir(bpy.context)
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    return config_dir.joinpath(filename)


def example_filepath_get(filename: str = "") -> Path:
    config_dir = Path(__file__).parent
    return config_dir.joinpath(f"config_examples/{filename}")


def copy_json_file(source_file: Path, target_file: Path) -> None:
    # Read contents
    with source_file.open() as source:
        contents = source.read()

    # Write contents to target file
    with target_file.open('w') as target:
        target.write(contents)


def template_example_dir_get() -> Path:
    return Path(__file__).parent.joinpath(f"templates")


def template_dir_get() -> Path:
    return core.get_shot_builder_config_dir(bpy.context).joinpath("templates")
