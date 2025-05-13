# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy

from ..models import FileListModel
from ..logger import LoggerFactory
from .. import prefs

logger = LoggerFactory.getLogger()

RD_PRESET_FILE_MODEL = FileListModel()
_rd_preset_enum_list: List[Tuple[str, str, str]] = []
_rd_preset_file_model_init: bool = False
# we need a second data dict because we want the enum properties data value to be the filepath
# but the ui (not only in enum dropdown mode) should display the label defined in the .py
# file with 'bl_label'. This dict is basically a mapping from filepath > label

_rd_preset_data_dict: Dict[str, str] = {}


def init_rd_preset_file_model(
    context: bpy.types.Context,
) -> None:
    global RD_PRESET_FILE_MODEL
    global _rd_preset_file_model_init
    addon_prefs = prefs.addon_prefs_get(context)

    # Is None if invalid.
    if not addon_prefs.lookdev.is_presets_dir_valid:
        logger.error(
            "Failed to initialize render settings file model. Invalid path. Check addon preferences"
        )
        return

    rd_settings_dir = addon_prefs.lookdev.presets_dir_path

    RD_PRESET_FILE_MODEL.reset()
    RD_PRESET_FILE_MODEL.root_path = rd_settings_dir
    valid_items = [file for file in RD_PRESET_FILE_MODEL.items_as_paths if file.suffix == ".py"]
    if not valid_items:
        # Update playblast_version prop.
        context.scene.lookdev.preset_file = ""

    else:
        # Update playblast_version prop.
        context.scene.lookdev.preset_file = valid_items[0].as_posix()

    _rd_preset_file_model_init = True


def get_rd_settings_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:
    global _rd_preset_enum_list
    global RD_PRESET_FILE_MODEL
    global init_rd_preset_file_model
    global _rd_preset_file_model_init
    global _rd_preset_data_dict

    # Init model if it did not happen.
    if not _rd_preset_file_model_init:
        init_rd_preset_file_model(context)

    # Reload model to update.
    RD_PRESET_FILE_MODEL.reload()

    # Get all Python files. Ignore hidden files.
    py_files = [
        f
        for f in RD_PRESET_FILE_MODEL.items_as_paths
        if f.suffix == ".py" and not f.name.startswith('.')
    ]
    py_labels: List[Tuple[Path, str]] = []

    # Get bl_label of each python file, if not use file name as label.
    for file in py_files:
        spec = importlib.util.spec_from_file_location(file.name, file.as_posix())

        # Load module.
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if "bl_label" not in dir(module):
            py_labels.append((file, file.name))
            continue
        py_labels.append((file, module.bl_label))

    # Generate final enum list and dict from py_labels.
    enum_list = []
    data_dict = {}
    for file, label in py_labels:
        data_dict[file.name] = label
        enum_list.append((file.as_posix(), label, ""))

    # Update global variables.
    _rd_preset_data_dict.clear()
    _rd_preset_data_dict.update(data_dict)
    _rd_preset_enum_list.clear()
    _rd_preset_enum_list.extend(enum_list)

    print(data_dict)
    return _rd_preset_enum_list
