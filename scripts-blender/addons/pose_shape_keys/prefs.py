from bpy.types import AddonPreferences
from bpy.props import BoolProperty


class PoseShapeKeysPrefs(AddonPreferences):
    bl_idname = __package__

    show_shape_key_info: BoolProperty(
        name="Reveal Shape Key Properties",
        description="Show and edit the properties of the corresponding shape key",
        default=True,
    )
    no_warning: BoolProperty(
        name="No Warning",
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
