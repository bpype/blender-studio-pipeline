import bpy
from bpy.types import Object
from .utils import get_addon_prefs

mode_history = []
suspend_hook = False

def on_weight_paint_enter():
    context = bpy.context
    obj = context.active_object
    wm = context.window_manager

    viewports = []
    for window in wm.windows:
        for area in window.workspace.screens[0].areas:
            if area.spaces.active.type == 'VIEW_3D':
                viewports.append(area.spaces.active)

    prefs = get_addon_prefs(context)
    tool_settings = context.scene.tool_settings
    if prefs.always_show_zero_weights:
        tool_settings.vertex_group_user = 'ACTIVE'
    if prefs.always_auto_normalize:
        tool_settings.use_auto_normalize = True
    if prefs.always_multipaint:
        tool_settings.use_multipaint = True

    # Store old visibility settings in a Custom Property in the WindowManager.
    if 'weight_paint_toggle' not in wm:
        wm['weight_paint_toggle'] = {}

    wp_toggle = wm['weight_paint_toggle']

    # ENSURING ARMATURE VISIBILITY
    armature = get_armature_of_meshob(obj)
    if not armature:
        return
    # Save all object visibility related info so it can be restored later.
    wp_toggle['arm_disabled'] = armature.hide_viewport
    wp_toggle['arm_hide'] = armature.hide_get()
    wp_toggle['arm_in_front'] = armature.show_in_front
    wp_toggle['arm_coll_assigned'] = False
    armature.hide_viewport = False
    armature.hide_set(False)
    armature.show_in_front = True

    for viewport in viewports:
        if viewport.local_view:
            wp_toggle['arm_local_view'] = armature.local_view_get(viewport)
            armature.local_view_set(viewport, True)

    # If the armature is still not visible, add it to the scene root collection.
    if not armature.visible_get() and not armature.name in context.scene.collection.objects:
        context.scene.collection.objects.link(armature)
        wp_toggle['arm_coll_assigned'] = True

    if armature.visible_get():
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        context.view_layer.objects.active = obj

    return armature.visible_get()


def on_weight_paint_leave():
    context = bpy.context
    obj = context.active_object
    wm = context.window_manager

    viewports = []
    for window in wm.windows:
        for area in window.workspace.screens[0].areas:
            if area.spaces.active.type == 'VIEW_3D':
                viewports.append(area.spaces.active)

    if 'weight_paint_toggle' not in wm:
        # There is no saved data to restore from, nothing else to do.
        return

    wp_toggle = wm['weight_paint_toggle']
    wp_toggle_as_dict = wp_toggle.to_dict()

    # Reset the stored data
    wm['weight_paint_toggle'] = {}

    armature = get_armature_of_meshob(obj)
    if not armature:
        return

    if armature.visible_get():
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = obj

    # If an armature was un-hidden, hide it again.
    armature.hide_viewport = wp_toggle_as_dict['arm_disabled']
    armature.hide_set(wp_toggle_as_dict['arm_hide'])
    armature.show_in_front = wp_toggle_as_dict['arm_in_front']

    # Restore whether the armature is in local view or not.
    for viewport in viewports:
        if 'arm_local_view' in wp_toggle_as_dict and viewport.local_view:
            armature.local_view_set(viewport, wp_toggle_as_dict['arm_local_view'])

    # Remove armature from scene root collection if it was moved there.
    if wp_toggle_as_dict['arm_coll_assigned']:
        context.scene.collection.objects.unlink(armature)


def get_armature_of_meshob(obj: Object):
    """Find and return the armature that deforms this mesh object."""
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            return mod.object

@bpy.app.handlers.persistent
def detect_mode_switch(scene=None, depsgraph=None):
    global suspend_hook
    if suspend_hook:
        return
    context = bpy.context
    mode_history.append(context.mode)
    if mode_history[-1] == 'PAINT_WEIGHT' and (len(mode_history)==1 or mode_history[-2] != 'PAINT_WEIGHT'):
        suspend_hook = True
        on_weight_paint_enter()
        suspend_hook = False
    elif len(mode_history) > 1 and mode_history[-2] == 'PAINT_WEIGHT' and mode_history[-1] != 'PAINT_WEIGHT':
        suspend_hook = True
        on_weight_paint_leave()
        suspend_hook = False

def register():
    bpy.app.handlers.depsgraph_update_post.append(detect_mode_switch)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(detect_mode_switch)