# SPDX-License-Identifier: GPL-2.0-or-later

import bpy, os
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty
from . import __package__ as base_package


def get_default_blend_path():
    filedir = os.path.dirname(os.path.realpath(__file__))
    return os.sep.join(filedir.split(os.sep) + ['geonodes.blend'])


class GNSK_Preferences(AddonPreferences):
    bl_idname = __package__

    no_alt_key: BoolProperty(
        name="No Alt Key",
        description="When trying to change a GeoNode shape key on multiple objects at once, you can normally hold the Alt key while you click and drag on the value. If you don't have an Alt key, you can enable this to show a button next to the slider with this behaviour",
    )
    node_import_type: EnumProperty(
        name="Nodes Import Method",
        description="Whether the Geometry Nodes should be linked or appended",
        items=[
            (
                'APPEND',
                'Append',
                'Append the nodes, making it local to the currently opened blend file',
            ),
            ('LINK', 'Link', 'Link the node tree from the specified blend file'),
        ],
    )
    blend_path: StringProperty(
        name="Nodes File",
        description=(
            "Path to the file containing the GeoNode ShapeKey nodes.\n"
            "Default path points to a file packaged with the add-on"
        ),
        subtype='FILE_PATH',
        default=get_default_blend_path(),
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout = layout.column(align=True)

        layout.prop(self, 'blend_path')
        layout.row().prop(self, 'node_import_type', expand=True)

        layout.separator()

        layout.prop(self, 'no_alt_key')


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


registry = [GNSK_Preferences]
