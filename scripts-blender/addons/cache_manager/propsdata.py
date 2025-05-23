# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Any

import bpy
from bpy.app.handlers import persistent

from cache_manager import opsdata
from cache_manager.logger import LoggerFactory
from . import addon_prefs_get

logger = LoggerFactory.getLogger(__name__)


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def update_cache_version_property(context: bpy.types.Context) -> None:
    items = opsdata.VERSION_DIR_MODEL.items
    if not items:
        context.scene.cm.cache_version = ""
    else:
        context.scene.cm.cache_version = items[0]


def category_update_version_model(self: Any, context: bpy.types.Context) -> None:
    opsdata.init_version_dir_model(context)
    update_cache_version_property(context)


def _get_scene_name() -> str:
    if not bpy.data.filepath:
        return ""

    filepath = Path(os.path.abspath(bpy.path.abspath(bpy.data.filepath)))
    return filepath.parents[1].name


def _get_shot_name() -> str:
    if not bpy.data.filepath:
        return ""

    filepath = Path(os.path.abspath(bpy.path.abspath(bpy.data.filepath)))
    return filepath.parents[0].name


def _gen_cacheconfig_filename() -> str:
    return f"{_get_shot_name()}.cacheconfig.{bpy.context.scene.cm.cache_version}.json"


def gen_cachedir_path_str(self: Any) -> str:

    addon_prefs = addon_prefs_get()

    if not addon_prefs.is_cachedir_root_valid:
        return ""

    p = (
        Path(addon_prefs.cachedir_root_path)
        / _get_scene_name()
        / _get_shot_name()
        / bpy.context.scene.cm.cache_version
    )

    return p.absolute().as_posix()


def gen_cacheconfig_path_str(self: Any) -> str:

    cachedir_str = gen_cachedir_path_str(None)

    if not cachedir_str:
        return ""

    p = Path(cachedir_str) / _gen_cacheconfig_filename()

    return p.absolute().as_posix()


def gen_cache_coll_filename(collection: bpy.types.Collection) -> str:
    return (
        f"{_get_shot_name()}.{collection.name}.{bpy.context.scene.cm.cache_version}.abc"
    )


def gen_cachepath_collection(
    collection: bpy.types.Collection, context: bpy.types.Context
) -> Path:
    cachedir_path = Path(gen_cachedir_path_str(None))

    if not cachedir_path:
        raise ValueError(
            f"Failed to generate cachepath for collection: {collection.name}. Invalid cachepath: {str(cachedir_path)}"
        )
    return cachedir_path.joinpath(gen_cache_coll_filename(collection)).absolute()


def get_cache_version_dir_path_str(self: Any) -> str:
    addon_prefs = addon_prefs_get()

    if not addon_prefs.is_cachedir_root_valid:
        return ""

    p = Path(addon_prefs.cachedir_root_path) / _get_scene_name() / _get_shot_name()

    return p.absolute().as_posix()


def rm_deleted_colls_from_list(context: bpy.types.Context) -> None:

    for category in [context.scene.cm.colls_export, context.scene.cm.colls_import]:

        category_name = context.scene.cm.category
        colls = [item.coll_ptr for item in category]
        colls.reverse()

        # Make sure to remove list from the back to not throw off the subsequent indexes.
        for idx, coll in enumerate(colls):
            org_idx = len(colls) - 1 - idx
            if not coll:
                # Remove item for that category at that index.
                category.remove(org_idx)
                logger.info(
                    "Removed index %i from %s list. Does not exists anymore.",
                    org_idx,
                    category_name.lower(),
                )
                # Update selection index.
                curr_index = context.scene.cm.colls_export_index
                if category_name == "IMPORT":
                    curr_index = context.scene.cm.colls_import_index

                if curr_index == org_idx and curr_index > 0:

                    if category_name == "IMPORT":
                        context.scene.cm.colls_import_index = curr_index - 1
                    else:
                        context.scene.cm.colls_export_index = curr_index - 1
    ui_redraw()


@persistent
def load_post_handler_init_model_cache_version(dummy: Any) -> None:
    category_update_version_model(None, bpy.context)


# ---------REGISTER ----------.


def register():
    # Add handlers.
    bpy.app.handlers.load_post.append(load_post_handler_init_model_cache_version)


def unregister():
    # Clear handlers.
    bpy.app.handlers.load_post.remove(load_post_handler_init_model_cache_version)
