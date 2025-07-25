# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import (
    prefs,
    props,
    opsdata,
    ops,
    ui,
    geo,
    geo_seq,
)
from .log import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Contactsheet",
    "author": "Paul Golter",
    "description": "Blender addon to create a contactsheet from sequence editor strips",
    "blender": (3, 0, 0),
    "version": (0, 1, 2),
    "location": "Sequence Editor",
    "category": "Sequencer",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    geo_seq = importlib.reload(geo_seq)
    geo = importlib.reload(geo)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    props.register()
    prefs.register()
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()


if __name__ == "__main__":
    register()
