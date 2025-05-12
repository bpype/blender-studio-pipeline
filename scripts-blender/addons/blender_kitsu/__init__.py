# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import dependencies

dependencies.preload_modules()

from . import (
    shot_builder,
    render_review,
    lookdev,
    bkglobals,
    types,
    cache,
    models,
    playblast,
    propsdata,
    props,
    prefs,
    sqe,
    util,
    generic,
    auth,
    context,
    anim,
    tasks,
    ui,
    edit,
)


from .logger import LoggerFactory, LoggerLevelManager

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Blender Kitsu",
    "author": "Paul Golter",
    "description": "Blender addon to interact with Kitsu",
    "blender": (2, 93, 0),
    "version": (0, 1, 6),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "props" in locals()

if _need_reload:
    import importlib

    lookdev.reload()
    bkglobals = importlib.reload(bkglobals)
    cache = importlib.reload(cache)
    types = importlib.reload(types)
    models = importlib.reload(models)
    playblast = importlib.reload(playblast)
    propsdata = importlib.reload(propsdata)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    ui = importlib.reload(ui)
    sqe.reload()
    util = importlib.reload(util)
    generic.reload()
    auth.reload()
    context.reload()
    tasks.reload()
    anim.reload()
    edit.reload()


def register():
    lookdev.register()
    prefs.register()
    cache.register()
    props.register()
    sqe.register()
    generic.register()
    auth.register()
    context.register()
    # tasks.register()
    playblast.register()
    anim.register()
    shot_builder.register()
    render_review.register()
    edit.register()

    LoggerLevelManager.configure_levels()
    logger.info("Registered blender-kitsu")


def unregister():
    anim.unregister()
    # tasks.unregister()
    context.unregister()
    auth.unregister()
    generic.unregister()
    sqe.unregister()
    props.unregister()
    cache.unregister()
    prefs.unregister()
    lookdev.unregister()
    playblast.unregister()
    shot_builder.unregister()
    render_review.unregister()
    edit.unregister()
    LoggerLevelManager.restore_levels()


if __name__ == "__main__":
    register()
