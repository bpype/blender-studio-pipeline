# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import importlib
from ..playblast import ops, ui


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
