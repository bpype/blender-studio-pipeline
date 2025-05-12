# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import (
    util,
    props,
    opsdata,
    checksqe,
    ops,
    ui,
    draw,
)


_need_reload = "ops" in locals()


if _need_reload:
    import importlib

    util = importlib.reload(util)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    checksqe = importlib.reload(checksqe)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)


def register():
    props.register()
    ops.register()
    ui.register()
    draw.register()


def unregister():
    draw.unregister()
    ui.unregister()
    ops.unregister()
    props.unregister()
