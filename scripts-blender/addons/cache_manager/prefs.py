# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Optional, Any

import bpy
from bpy.app.handlers import persistent

from . import opsdata


def update_cache_version_property(context: bpy.types.Context) -> None:
    items = opsdata.VERSION_DIR_MODEL.items
    if not items:
        context.scene.cm.cache_version = ""
    else:
        context.scene.cm.cache_version = items[0]


def category_update_version_model(self: Any, context: bpy.types.Context) -> None:
    opsdata.init_version_dir_model(context)
    update_cache_version_property(context)


def addon_prefs_get(context: bpy.types.Context=None) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    if not context:
        context = bpy.context
    from . import __package__ as base_package
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir_root: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//cache",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
        description="Root directory in which the caches will be exported. Will create subfolders during export",
        update=category_update_version_model,
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

@persistent
def load_post_handler_init_model_cache_version(dummy: Any) -> None:
    category_update_version_model(None, bpy.context)


classes = [CM_AddonPreferences]


def register():
    bpy.app.handlers.load_post.append(load_post_handler_init_model_cache_version)
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    bpy.app.handlers.load_post.remove(load_post_handler_init_model_cache_version)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
