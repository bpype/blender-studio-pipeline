import bpy
from pathlib import Path
import json
from . import constants

TASK_LAYER_TYPES = {}
TRANSFER_DATA_DEFAULTS = {}
ATTRIBUTE_DEFAULTS = {}


def get_json_file():
    directory = Path(bpy.data.filepath).parent
    json_file_path = directory.joinpath(constants.TASK_LAYER_CONFIG_NAME)
    if json_file_path.exists():
        return json_file_path
    return


def get_task_layer_presets_path():
    return Path(__file__).parent.joinpath(constants.TASK_LAYER_CONFIG_DIR_NAME)


def verify_json_data(json_file_path=""):
    global TASK_LAYER_TYPES
    global TRANSFER_DATA_DEFAULTS
    global ATTRIBUTE_DEFAULTS
    directory = Path(bpy.data.filepath).parent
    if json_file_path == "":
        json_file_path = directory.joinpath(constants.TASK_LAYER_CONFIG_NAME)
    if not json_file_path.exists():
        return
    json_file = open(json_file_path)
    json_content = json.load(json_file)
    try:
        TASK_LAYER_TYPES = json_content["TASK_LAYER_TYPES"]
        TRANSFER_DATA_DEFAULTS = json_content["TRANSFER_DATA_DEFAULTS"]
        ATTRIBUTE_DEFAULTS = json_content["ATTRIBUTE_DEFAULTS"]
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
