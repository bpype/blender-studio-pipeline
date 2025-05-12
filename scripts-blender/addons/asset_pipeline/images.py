# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from .prefs import get_addon_prefs


def save_images():
    prefs = get_addon_prefs()
    user_path = Path(prefs.save_images_path)
    default_path = Path(bpy.data.filepath).parent.joinpath("images")
    save_path = default_path if prefs.save_images_path == "" else user_path
    for img in bpy.data.images:
        if img.is_dirty:
            filepath = save_path.joinpath(img.name).__str__() + ".png"
            img.save(filepath=filepath)
