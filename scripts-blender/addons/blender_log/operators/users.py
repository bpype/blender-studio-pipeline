import bpy
from bpy.props import StringProperty
from ..id_types import get_id


class BLENLOG_OT_report_collections_with_fake_user(bpy.types.Operator):
    """Report collections with fake user enabled"""

    bl_idname = "scene.report_collections_with_fake_user"
    bl_label = "Report Fake User Collections"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        blenlog = context.scene.blender_log

        category = "Fake User Collection"
        blenlog.clear_category(category)

        counter = 0
        for coll in bpy.data.collections:
            if coll.library:
                continue
            if coll.use_fake_user:
                blenlog.add(
                    name=coll.name,
                    category=category,
                    description="Collections with fake users can get stuck in a file. It is recommended not to use this flag in order to keep files clear of trash data.",
                    icon='OUTLINER_COLLECTION',
                    category_icon='FAKE_USER_ON',
                    operator=BLENLOG_OT_disable_collection_fake_user.bl_idname,
                    op_kwargs={'coll_name': coll.name},
                    op_icon='FAKE_USER_OFF',
                )
                counter += 1

        if counter == 0:
            self.report({'INFO'}, "No collections with fake user.")
        else:
            self.report({'WARNING'}, f"Found {counter} collections with fake user.")

        return {'FINISHED'}


class BLENLOG_OT_disable_collection_fake_user(bpy.types.Operator):
    """Disable fake user flag on the collection"""

    bl_idname = "collection.clear_fake_user"
    bl_label = "Clear Collection Fake User"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    coll_name: StringProperty()

    def execute(self, context):
        logs = context.scene.blender_log

        coll = bpy.data.collections.get((self.coll_name, None))
        if not coll:
            self.report({'WARNING'}, "Collection no longer exists.")
        else:
            coll.use_fake_user = False
            self.report({'INFO'}, "Collection fake user cleared.")

        logs.remove(logs.active_log)

        return {'FINISHED'}


class BLENLOG_OT_remap_users(bpy.types.Operator):
    """Remap users of an ID to another of the same type"""

    bl_idname = "object.blenlog_remap_users"
    bl_label = "Remap Users"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    redundant_id: StringProperty()
    id_type: StringProperty()
    preserved_id: StringProperty()

    def execute(self, context):
        redundant_id = get_id(self.redundant_id, self.id_type)
        if not redundant_id:
            self.report({'ERROR'}, f"ID no longer exists: {self.redundant_id}.")
            return {'CANCELLED'}
        preserved_id = get_id(self.preserved_id, self.id_type)
        if not preserved_id:
            self.report({'ERROR'}, f"ID no longer exists: {self.preserved_id}.")
            return {'CANCELLED'}

        redundant_id.user_remap(preserved_id)
        redundant_id.use_fake_user = False
        self.report({'INFO'}, f"{self.redundant_id} has been replaced with {self.preserved_id}")

        logs = context.scene.blender_log
        logs.remove(logs.active_log)

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_collections_with_fake_user,
    BLENLOG_OT_disable_collection_fake_user,
    BLENLOG_OT_remap_users,
]
