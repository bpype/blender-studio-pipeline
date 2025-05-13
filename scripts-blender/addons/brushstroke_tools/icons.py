# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import bpy.utils.previews
import os

icon_previews = {}

def register():
    # register custom icons
    dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll = bpy.utils.previews.new()
    for entry in os.scandir(dir):
        if entry.name.endswith(".png"):
            name = os.path.splitext(entry.name)[0]
            pcoll.load(name.upper(), entry.path, "IMAGE")
    global icon_previews
    icon_previews["main"] = pcoll

def unregister():
    # unregister custom icons
    global icon_previews
    for pcoll in icon_previews.values():
        bpy.utils.previews.remove(pcoll)
    icon_previews.clear()
