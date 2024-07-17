import bpy
from bpy.types import Object, Operator, VIEW3D_MT_paint_weight, VIEW3D_MT_object
from .prefs import get_addon_prefs

# This operator is added to the Object menu.

# It does the following:
#  Set active object to weight paint mode
#  Find first armature via the object's modifiers.
#   Ensure it is visible, select it and set it to pose mode.

# This allows you to start weight painting with a single button press from any state.

# When running the operator again, it should restore all armature visibility related settings to how it was before.


def get_armature_of_meshob(obj: Object):
    """Find and return the armature that deforms this mesh object."""
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            return mod.object


def enter_wp(context) -> bool:
    """Enter weight paint mode, change the necessary settings, and save their
    original states so they can be restored when leaving wp mode."""

    obj = context.active_object
    wm = context.window_manager

    prefs = get_addon_prefs(context)
    tool_settings = context.scene.tool_settings
    if prefs.always_show_zero_weights:
        tool_settings.vertex_group_user = 'ACTIVE'
    if prefs.always_auto_normalize:
        tool_settings.use_auto_normalize = True
    if prefs.always_multipaint:
        tool_settings.use_multipaint = True

    # Store old shading settings in a Custom Property dictionary in the WindowManager.
    if 'weight_paint_toggle' not in wm:
        wm['weight_paint_toggle'] = {}

    wp_toggle = wm['weight_paint_toggle']
    wp_toggle_as_dict = wp_toggle.to_dict()

    # If we are entering WP mode for the first time or if the last time
    # the operator was exiting WP mode, then save current state.
    if 'last_switch_in' not in wp_toggle_as_dict or wp_toggle_as_dict['last_switch_in'] == False:
        wp_toggle['active_object'] = obj

    # This flag indicates that the last time this operator ran, we were
    # switching INTO wp mode.
    wp_toggle['last_switch_in'] = True
    wp_toggle['mode'] = obj.mode

    # Enter WP mode.
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

    # ENSURING ARMATURE VISIBILITY
    armature = get_armature_of_meshob(obj)
    if not armature:
        return
    # Save all object visibility related info so it can be restored later.
    wp_toggle['arm_enabled'] = armature.hide_viewport
    wp_toggle['arm_hide'] = armature.hide_get()
    wp_toggle['arm_in_front'] = armature.show_in_front
    wp_toggle['arm_coll_assigned'] = False
    armature.hide_viewport = False
    armature.hide_set(False)
    armature.show_in_front = True
    if context.space_data.local_view:
        wp_toggle['arm_local_view'] = armature.local_view_get(context.space_data)
        armature.local_view_set(context.space_data, True)

    # If the armature is still not visible, add it to the scene root collection.
    if not armature.visible_get() and not armature.name in context.scene.collection.objects:
        context.scene.collection.objects.link(armature)
        wp_toggle['arm_coll_assigned'] = True

    if armature.visible_get():
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')

    context.view_layer.objects.active = obj
    return armature.visible_get()


def leave_wp(context):
    """Leave weight paint mode, then find, restore, and delete the data
    that was stored about shading settings in enter_wp()."""

    obj = context.active_object
    wm = context.window_manager

    if 'weight_paint_toggle' not in wm or 'mode' not in wm['weight_paint_toggle'].to_dict():
        # There is no saved data to restore from, nothing else to do.
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

    wp_toggle = wm['weight_paint_toggle']
    wp_toggle_as_dict = wp_toggle.to_dict()

    # Restore mode.
    bpy.ops.object.mode_set(mode=wp_toggle_as_dict['mode'])

    # Reset the stored data
    wm['weight_paint_toggle'] = {}
    # Flag to save that the last time the operator ran we were EXITING wp mode.
    wm['weight_paint_toggle']['last_switch_in'] = False

    armature = get_armature_of_meshob(obj)
    if not armature:
        return
    # If an armature was un-hidden, hide it again.
    armature.hide_viewport = wp_toggle_as_dict['arm_enabled']
    armature.hide_set(wp_toggle_as_dict['arm_hide'])
    armature.show_in_front = wp_toggle_as_dict['arm_in_front']

    # Restore whether the armature is in local view or not.
    if 'arm_local_view' in wp_toggle_as_dict and context.space_data.local_view:
        armature.local_view_set(context.space_data, wp_toggle_as_dict['arm_local_view'])

    # Remove armature from scene root collection if it was moved there.
    if wp_toggle_as_dict['arm_coll_assigned']:
        context.scene.collection.objects.unlink(armature)

    return


class EASYWEIGHT_OT_toggle_weight_paint(Operator):
    """Enter weight paint mode on a mesh object and pose mode on its armature"""

    bl_idname = "object.weight_paint_toggle"
    bl_label = "Toggle Weight Paint Mode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            cls.poll_message_set("Active object must be a mesh.")
            return False
        return True

    def execute(self, context):
        obj = context.active_object

        if obj.mode != 'WEIGHT_PAINT':
            armature_visible = enter_wp(context)
            if armature_visible == False:
                # This should never happen, but it also doesn't break anything.
                self.report({'WARNING'}, "Could not make Armature visible.")
            return {'FINISHED'}
        else:
            leave_wp(context)
            wm = context.window_manager
            if 'weight_paint_toggle' in wm:
                del wm['weight_paint_toggle']
            return {'FINISHED'}


def draw_in_menu(self, context):
    self.layout.operator(EASYWEIGHT_OT_toggle_weight_paint.bl_idname)


registry = [EASYWEIGHT_OT_toggle_weight_paint]


def register():
    VIEW3D_MT_paint_weight.append(draw_in_menu)
    VIEW3D_MT_object.append(draw_in_menu)


def unregister():
    VIEW3D_MT_paint_weight.remove(draw_in_menu)
    VIEW3D_MT_object.remove(draw_in_menu)
