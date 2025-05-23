# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from ..sqe import opsdata, checkstrip, pull, push, ops, ui, draw


# ---------REGISTER ----------.


def reload():
    global opsdata
    global checkstrip
    global pull
    global push
    global ops
    global ui
    global draw

    opsdata = importlib.reload(opsdata)
    checkstrip = importlib.reload(checkstrip)
    pull = importlib.reload(pull)
    push = importlib.reload(push)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    draw = importlib.reload(draw)


def register():
    ops.register()
    ui.register()
    draw.register()


def unregister():
    ui.unregister()
    ops.unregister()
    draw.unregister()
