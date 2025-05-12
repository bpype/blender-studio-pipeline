# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Optional

import bpy

from cache_manager import propsdata


class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir_root: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//cache",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
        description="Root directory in which the caches will be exported. Will create subfolders during export",
        update=propsdata.category_update_version_model,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "cachedir_root", text="Root Cache Directory")

        if not self.cachedir_root:
            row = box.row()
            row.label(text="Please specify the root cache directory.", icon="ERROR")

        if not bpy.data.filepath and self.cachedir_root.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path as root cache directory the current file needs to be saved.",
                icon="ERROR",
            )

    @property
    def cachedir_root_path(self) -> Optional[Path]:
        if not self.is_cachedir_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cachedir_root)))

    @property
    def is_cachedir_root_valid(self) -> bool:

        # Check if file is saved.
        if not self.cachedir_root:
            return False

        if not bpy.data.filepath and self.cachedir_root.startswith("//"):
            return False

        return True


# ---------REGISTER ----------.

classes = [CM_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
