from bpy.types import AddonPreferences
from bpy.props import BoolProperty


class LatticeMagicPreferences(AddonPreferences):
    bl_idname = __package__

    update_active_shape_key: BoolProperty(
        name='Update Active Shape Key',
        description="Update the active shape key on frame change based on the current frame and the shape key's name",
        default=False,
    )

def get_addon_prefs(context=None):
    return context.preferences.addons[__package__].preferences

registry = [
	LatticeMagicPreferences
]
