# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re
from typing import Union

import bpy

from . import bkglobals


def ui_redraw() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_version(str_value: str, format: type = str) -> Union[str, int, None]:
    match = re.search(bkglobals.VERSION_PATTERN, str_value)
    if match:
        version = match.group()
        if format == str:
            return version
        if format == int:
            return int(version.replace("v", ""))
    return None


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    # NOTE: This was moved out of prefs.py to resolve a circular dependency with cache.py.
    if not context:
        context = bpy.context
    base_package = __package__
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences
