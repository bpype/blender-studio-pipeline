# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from ..lookdev import prefs
from ..lookdev import props
from ..lookdev import opsdata
from ..lookdev import ops
from ..lookdev import ui


# ---------REGISTER ----------.


def reload():
    global prefs
    global props
    global opsdata
    global ops
    global ui

    prefs = importlib.reload(prefs)
    props = importlib.reload(props)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)


def register():
    prefs.register()
    props.register()
    ops.register()
    ui.register()


def unregister():
    ops.unregister()
    ui.unregister()
    props.unregister()
    prefs.unregister()
