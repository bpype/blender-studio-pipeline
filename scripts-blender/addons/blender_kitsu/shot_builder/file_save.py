# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import bpy
import functools


def save_shot_timer_target(file_path: str) -> None:
    bpy.ops.wm.save_mainfile(filepath=file_path, relative_remap=True)


def save_shot_builder_file(file_path: str) -> bool:
    """Save Shot File within Folder of matching name.
    Set Shot File to relative Paths."""
    if Path(file_path).exists():
        print(f"Shot Builder cannot overwrite existing file '{file_path}'")
        return False
    dir_path = Path(file_path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    bpy.app.timers.register(
        functools.partial(save_shot_timer_target, file_path=file_path),
        first_interval=0.1,
    )
    return True
