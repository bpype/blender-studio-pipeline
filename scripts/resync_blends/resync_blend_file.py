#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import contextlib


def main():
    if len(bpy.data.libraries) == 0:
        return

    for lib in bpy.data.libraries:
        lib.reload()

    with override_save_version():
        bpy.ops.wm.save_mainfile()
        print(f"Reloaded & Saved file: '{bpy.data.filepath}'")
        bpy.ops.wm.quit_blender()


@contextlib.contextmanager
def override_save_version():
    """Overrides the save version settings"""
    save_version = bpy.context.preferences.filepaths.save_version

    try:
        bpy.context.preferences.filepaths.save_version = 0
        yield

    finally:
        bpy.context.preferences.filepaths.save_version = save_version


if __name__ == "__main__":
    main()
