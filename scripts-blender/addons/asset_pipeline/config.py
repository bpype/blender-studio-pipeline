import bpy
from pathlib import Path
import json
from . import constants


# TODO could refactor this into a class, but only one instance of that class will be needed

TASK_LAYER_TYPES = {}
TRANSFER_DATA_DEFAULTS = {}
ATTRIBUTE_DEFAULTS = {}
ASSET_CATALOG_ID = ""


def get_task_layer_json_filepath() -> Path:
    directory = Path(bpy.data.filepath).parent
    json_file_path = directory.joinpath(constants.TASK_LAYER_CONFIG_NAME)
    return json_file_path


def get_task_layer_dict(file_path_str="") -> dict:
    if file_path_str == "":
        json_file_path = get_task_layer_json_filepath()
    else:
        json_file_path = Path(file_path_str)
    if not json_file_path.exists():
        return
    return json.load(open(json_file_path))


def get_task_layer_presets_path():
    return Path(__file__).parent.joinpath(constants.TASK_LAYER_CONFIG_DIR_NAME)


def verify_task_layer_json_data(json_file_path=""):
    global TASK_LAYER_TYPES
    global TRANSFER_DATA_DEFAULTS
    global ATTRIBUTE_DEFAULTS
    global ASSET_CATALOG_ID

    json_content = get_task_layer_dict(json_file_path)

    if not json_content:
        return
    try:
        TASK_LAYER_TYPES = json_content["TASK_LAYER_TYPES"]
        TRANSFER_DATA_DEFAULTS = json_content["TRANSFER_DATA_DEFAULTS"]
        ATTRIBUTE_DEFAULTS = json_content["ATTRIBUTE_DEFAULTS"]

        # Asset Catalog is an optional value in task_layers.json and doesn't exist by default
        if "ASSET_CATALOG_ID" in json_content:
            ASSET_CATALOG_ID = json_content["ASSET_CATALOG_ID"]
        return True
    except KeyError:
        return


def write_json_file(asset_path: Path, source_file_path: Path):
    json_file_path = asset_path.joinpath(constants.TASK_LAYER_CONFIG_NAME)
    json_file = open(source_file_path)
    json_content = json.load(json_file)
    json_dump = json.dumps(json_content, indent=4)
    with open(json_file_path, "w") as config_output:
        config_output.write(json_dump)


def update_task_layer_json_data(task_layer_dict: dict):
    filepath = get_task_layer_json_filepath()
    with filepath.open("w") as json_file:
        json.dump(task_layer_dict, json_file, indent=4)
    verify_task_layer_json_data()
