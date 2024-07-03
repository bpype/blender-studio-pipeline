from bpy.types import AddonPreferences
from bpy.props import BoolProperty
from . import __package__ as base_package


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


class PoseShapeKeysPrefs(AddonPreferences):
    bl_idname = __package__

    show_shape_key_info: BoolProperty(
        name="Reveal Shape Key Properties",
        description="Show and edit the properties of the corresponding shape key",
        default=True,
    )
    no_warning: BoolProperty(
        name="No Danger Warning",
        description="Do not show a pop-up warning for dangerous operations",
    )
    grid_objects_on_jump: BoolProperty(
        name="Place Objects In Grid On Jump",
        description="When using the Jump To Storage Object operator, place the other storage objects in a grid",
        default=True,
    )

    def draw(self, context):
        self.layout.prop(self, 'no_warning')
        self.layout.prop(self, 'grid_objects_on_jump')


registry = [PoseShapeKeysPrefs]
