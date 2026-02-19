import bpy

from . import __package__ as base_package
def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if bpy.app.version >= (4, 2, 0) and base_package.startswith('bl_ext'):
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences
