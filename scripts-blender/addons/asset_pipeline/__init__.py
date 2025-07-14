# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib

from . import ui, ops, props, prefs

bl_info = {
    "name": "Asset Pipeline",
    "author": "Nick Alberelli",
    "description": "Asset data merger for studio collaboration",
    "blender": (5, 0, 0),
    "version": (0, 3, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts-blender/addons/asset_pipeline",
    "category": "Generic",
}


def reload() -> None:
    global ui
    global ops
    global props
    global prefs
    importlib.reload(ui)
    importlib.reload(ops)
    importlib.reload(props)
    importlib.reload(prefs)


_need_reload = "ui" in locals()
if _need_reload:
    reload()

# ----------------REGISTER--------------.


def register() -> None:
    ui.register()
    ops.register()
    props.register()
    prefs.register()


def unregister() -> None:
    ui.unregister()
    ops.unregister()
    props.unregister()
    prefs.unregister()
