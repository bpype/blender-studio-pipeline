import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty, EnumProperty


class GNSK_Preferences(AddonPreferences):
    bl_idname = __package__

    pablico_mode: BoolProperty(
        name="Pen Workaround",
        description="Add a button next to Influence sliders when multiple objects of the GeoNode ShapeKey are selected, to allow affecting all objects without having an Alt key",
    )
    node_import_type: EnumProperty(
        name="Node Group Import Type",
        description="Whether the GeometryNodes node tree should be linked or appended",
        items=[
            (
                'APPEND',
                'Append',
                'Append the node tree, making it local to the currently opened blend file',
            ),
            ('LINK', 'Link', 'Link the node tree from an external blend file'),
        ],
    )
    blend_path: StringProperty(
        name="Nodegroup File",
        description="Path to the file containing the GeoNode ShapeKey nodes",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout = layout.column(align=True)
        layout.prop(self, 'pablico_mode')
        layout.separator()

        layout.row().prop(self, 'node_import_type', expand=True)
        layout.prop(self, 'blend_path')


registry = [GNSK_Preferences]


@bpy.app.handlers.persistent
def autofill_node_blend_path(context, _dummy):
    if type(context) == str:
        context = bpy.context
    addon_prefs = context.preferences.addons[__package__].preferences
    current_path = addon_prefs.blend_path
    if not current_path:
        filedir = os.path.dirname(os.path.realpath(__file__))
        addon_prefs.blend_path = os.sep.join(filedir.split(os.sep) + ['geonodes.blend'])


def register():
    bpy.app.handlers.load_post.append(autofill_node_blend_path)


def unregister():
    bpy.app.handlers.load_post.remove(autofill_node_blend_path)
