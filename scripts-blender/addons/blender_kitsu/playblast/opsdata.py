# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Dict, List, Tuple, Generator
from pathlib import Path

import bpy

from ..models import FileListModel
from ..logger import LoggerFactory

PLAYBLAST_FILE_MODEL = FileListModel()
_playblast_enum_list: List[Tuple[str, str, str]] = []
_playblast_file_model_init: bool = False

logger = LoggerFactory.getLogger()


def init_playblast_file_model(
    context: bpy.types.Context,
) -> None:
    global PLAYBLAST_FILE_MODEL
    global _playblast_file_model_init

    kitsu_props = context.scene.kitsu
    # TODO Make playblast dir variable (seq or shot)
    # Consider removing this string and use prefs instead

    # Is None if invalid.
    if not context.scene.kitsu.playblast_dir:
        logger.error(
            "Failed to initialize playblast file model. Invalid path. Check addon preferences"
        )
        return

    playblast_dir = Path(context.scene.kitsu.playblast_dir)

    PLAYBLAST_FILE_MODEL.reset()
    PLAYBLAST_FILE_MODEL.root_path = playblast_dir

    if not PLAYBLAST_FILE_MODEL.versions:
        PLAYBLAST_FILE_MODEL.append_item("v001")
        # Update playblast_version prop.
        kitsu_props.playblast_version = "v001"

    else:
        # Update playblast_version prop.
        kitsu_props.playblast_version = PLAYBLAST_FILE_MODEL.versions[0]

    _playblast_file_model_init = True


def add_playblast_version_increment(context: bpy.types.Context) -> str:
    # Init model if it did not happen.
    if not _playblast_file_model_init:
        init_playblast_file_model(context)

    # Should be already sorted.
    versions = PLAYBLAST_FILE_MODEL.versions

    if len(versions) > 0:
        latest_version = versions[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    PLAYBLAST_FILE_MODEL.append_item(increment)
    return increment


def get_playblast_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:
    global _playblast_enum_list
    global PLAYBLAST_FILE_MODEL
    global init_playblast_file_model
    global _playblast_file_model_init

    # Init model if it did not happen.
    if not _playblast_file_model_init:
        init_playblast_file_model(context)

    # Clear all versions in enum list.
    _playblast_enum_list.clear()
    _playblast_enum_list.extend(PLAYBLAST_FILE_MODEL.versions_as_enum_list)

    return _playblast_enum_list


def add_version_custom(custom_version: str) -> None:
    global _playblast_enum_list
    global PLAYBLAST_FILE_MODEL

    PLAYBLAST_FILE_MODEL.append_item(custom_version)
