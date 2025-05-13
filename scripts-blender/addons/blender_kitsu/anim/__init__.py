# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from . import opsdata, ops, ui


# ---------REGISTER ----------.


def reload():
    global opsdata
    global ops
    global ui

    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
