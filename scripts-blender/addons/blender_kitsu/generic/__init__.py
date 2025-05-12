# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from ..generic import ops


# ---------REGISTER ----------.


def reload():
    global ops

    ops = importlib.reload(ops)


def register():
    ops.register()


def unregister():
    ops.unregister()
