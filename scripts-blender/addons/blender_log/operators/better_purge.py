import bpy


class OUTLINER_OT_better_purge(bpy.types.Operator):
    """Like Blender's purge, but clears fake users from linked IDs and collections"""

    bl_idname = "outliner.better_purge"
    bl_label = "Better Purge"

    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        better_purge(context)
        return {'FINISHED'}


def better_purge(context, clear_coll_fake_users=True):
    """Call Blender's purge function, but first Python-override all library IDs'
    use_fake_user to False.
    Otherwise, linked IDs essentially do not get purged properly.
    """

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            break
    else:
        assert False, "Error: This operation requires a 3D view to be present."

    if clear_coll_fake_users:
        for coll in bpy.data.collections:
            coll.use_fake_user = False

    id_list = list(bpy.data.user_map().keys())
    for id in id_list:
        if id.library:
            id.use_fake_user = False

    with context.temp_override(area=area):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def draw_purge_ui(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(OUTLINER_OT_better_purge.bl_idname)


registry = [OUTLINER_OT_better_purge]


def register():
    bpy.types.TOPBAR_MT_file_cleanup.append(draw_purge_ui)


def unregister():
    bpy.types.TOPBAR_MT_file_cleanup.append(draw_purge_ui)
