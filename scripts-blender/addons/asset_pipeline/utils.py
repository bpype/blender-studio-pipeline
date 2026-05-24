from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .prefs import ASSET_PIPELINE_addon_preferences
import bpy
from bpy.types import Context

from . import __package__ as base_package


def get_addon_prefs(context: Context|None=None) -> ASSET_PIPELINE_addon_preferences:
    if not context:
        context = bpy.context
    if bpy.app.version >= (4, 2, 0) and base_package.startswith('bl_ext'):
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences
