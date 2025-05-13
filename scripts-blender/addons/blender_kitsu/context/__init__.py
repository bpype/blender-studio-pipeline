# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from ..context import ops, ui


# ---------REGISTER ----------.


def reload():
    global ops
    global ui

    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
