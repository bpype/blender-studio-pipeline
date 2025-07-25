# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import ops
from .ui import topbar_file_new_draw_handler


def register():
    bpy.types.TOPBAR_MT_file_new.prepend(topbar_file_new_draw_handler)
    ops.register()


def unregister():
    bpy.types.TOPBAR_MT_file_new.remove(topbar_file_new_draw_handler)
    ops.unregister()
