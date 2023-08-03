from bpy.types import AddonPreferences
from bpy.props import BoolProperty

class AnimCupboardPreferences(AddonPreferences):
    bl_idname = __package__

    warn_about_absolute_libs: BoolProperty(
        name = "Warn About Libraries",
        description = "On file save, create a pop-up if there are any absolute path or broken libraries in the blend file",
        default = True
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'warn_about_absolute_libs')

registry = [
    AnimCupboardPreferences
]