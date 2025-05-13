# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from cache_manager import (
    cmglobals,
    logger,
    cache,
    models,
    prefs,
    propsdata,
    props,
    opsdata,
    ops,
    ui
)

logg = logger.LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Cache Manager",
    "author": "Paul Golter",
    "description": "Blender addon to streamline alembic caches of assets",
    "blender": (2, 93, 0),
    "version": (0, 1, 2),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    cmglobals = importlib.reload(cmglobals)
    logger = importlib.reload(logger)
    cache = importlib.reload(cache)
    models = importlib.reload(models)
    prefs = importlib.reload(prefs)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    prefs.register()
    props.register()
    propsdata.register()
    ops.register()
    ui.register()
    logg.info("Registered cache-manager")


def unregister():
    ui.unregister()
    ops.unregister()
    propsdata.unregister()
    props.unregister()
    prefs.unregister()


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    if not context:
        context = bpy.context
    from .. import __package__ as base_package
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


if __name__ == "__main__":
    register()
