# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from typing import Any, List, Tuple
from pathlib import Path
from .. import prefs
import bpy

from ..models import FileListModel
from ..logger import LoggerFactory

EDIT_EXPORT_FILE_MODEL = FileListModel()
_edit_export_enum_list: List[Tuple[str, str, str]] = []
_edit_export_file_model_init: bool = False

logger = LoggerFactory.getLogger()

# TODO Compare to Playblast opsdata, maybe centralize some repeated code


def init_edit_export_file_model(
    context: bpy.types.Context,
) -> None:
    global EDIT_EXPORT_FILE_MODEL
    global _edit_export_file_model_init

    addon_prefs = prefs.addon_prefs_get(context)
    kitsu_props = context.scene.kitsu
    edit_export_dir = Path(addon_prefs.edit_export_dir)

    # Is None if invalid.
    if addon_prefs.edit_export_dir == "" or not edit_export_dir.exists():
        logger.error(
            "Failed to initialize edit export file model. Invalid path. Check addon preferences"
        )
        return

    EDIT_EXPORT_FILE_MODEL.filter_name = Path(kitsu_props.edit_export_file).name
    EDIT_EXPORT_FILE_MODEL.reset()
    EDIT_EXPORT_FILE_MODEL.root_path = edit_export_dir

    if not EDIT_EXPORT_FILE_MODEL.versions:
        EDIT_EXPORT_FILE_MODEL.append_item("v001")
        # Update edit_export_version prop.
        kitsu_props.edit_export_version = "v001"

    else:
        # Update edit_export_version prop.
        kitsu_props.edit_export_version = EDIT_EXPORT_FILE_MODEL.versions[0]

    _edit_export_file_model_init = True


def add_edit_export_version_increment(context: bpy.types.Context) -> str:
    # Init model if it did not happen.
    if not _edit_export_file_model_init:
        init_edit_export_file_model(context)

    # Should be already sorted.
    versions = EDIT_EXPORT_FILE_MODEL.versions

    if len(versions) > 0:
        latest_version = versions[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    EDIT_EXPORT_FILE_MODEL.append_item(increment)
    return increment


def get_edit_export_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:
    global _edit_export_enum_list
    global EDIT_EXPORT_FILE_MODEL
    global init_edit_export_file_model
    global _edit_export_file_model_init

    # Init model if it did not happen.
    if not _edit_export_file_model_init:
        init_edit_export_file_model(context)

    # Clear all versions in enum list.
    _edit_export_enum_list.clear()
    _edit_export_enum_list.extend(EDIT_EXPORT_FILE_MODEL.versions_as_enum_list)

    return _edit_export_enum_list


def add_version_custom(custom_version: str) -> None:
    global _edit_export_enum_list
    global EDIT_EXPORT_FILE_MODEL

    EDIT_EXPORT_FILE_MODEL.append_item(custom_version)
