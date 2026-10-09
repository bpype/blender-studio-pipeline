# SPDX-FileCopyrightText: 2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later


import bpy


def save_images():
    for img in bpy.data.images:
        if not img.is_dirty:
            continue
        try:
            if img.source == "GENERATED" or img.packed_file:
                img.pack()
            else:
                img.save()
        except Exception:
            # Should never happen.
            # https://projects.blender.org/blender/blender/issues/152638
            print(f"Incremental Autosave: Failed to save dirty image: {img.name}")
