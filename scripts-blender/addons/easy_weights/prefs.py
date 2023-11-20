import bpy


class EASYWEIGHT_addon_preferences(bpy.types.AddonPreferences):
    hotkeys = []


registry = [EASYWEIGHT_addon_preferences]
