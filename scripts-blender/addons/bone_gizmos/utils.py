import bpy

def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    base_package = __package__
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences
