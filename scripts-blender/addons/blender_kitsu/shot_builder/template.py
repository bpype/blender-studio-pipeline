# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from . import config


def list_dir_blend_files(p: Path) -> list[Path]:
    return list(p.glob('*.blend'))


def open_template_as_homefile(task_type_name: str) -> None:
    """Open Template File as Homefile so it has no filepath."""
    file_path = get_template_for_task_type(task_type_name)
    if not file_path.exists():
        raise FileNotFoundError(f"Template file '{file_path}' does not exist.")
    bpy.ops.wm.read_homefile(filepath=file_path.as_posix())


def get_template_for_task_type(task_type_name: str) -> Path:
    # Find Custom Template in Config Dir if available
    for file in list_dir_blend_files(config.template_dir_get()):
        if file.stem.lower() == task_type_name.lower():
            return file
    # Fall back to example templates if no custom templates found
    for file in list_dir_blend_files(config.template_example_dir_get()):
        if file.stem.lower() == task_type_name.lower():
            return file
    return
