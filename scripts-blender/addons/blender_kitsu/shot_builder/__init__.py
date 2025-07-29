# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import ops, ui


def register():
    ops.register()
    ui.register()


def unregister():
    ui.unregister()
    ops.unregister()
