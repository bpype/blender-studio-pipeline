# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import AddonPreferences
from bpy.props import BoolProperty
from . import __package__ as base_package

class LatticeMagicPreferences(AddonPreferences):
    bl_idname = base_package

    update_active_shape_key: BoolProperty(
        name='Update Active Shape Key',
        description="Update the active shape key on frame change based on the current frame and the shape key's name",
        default=False,
    )


def get_addon_prefs(context=None):
    return context.preferences.addons[base_package].preferences


registry = [LatticeMagicPreferences]
