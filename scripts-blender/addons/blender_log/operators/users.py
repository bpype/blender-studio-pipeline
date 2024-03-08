import bpy
from bpy.props import StringProperty
from ..id_types import get_id


class BLENLOG_OT_report_fake_users(bpy.types.Operator):
    """Report Fake User IDs. Ignores Text and Brush IDs"""

    bl_idname = "blenlog.report_fake_users"
    bl_label = "Report Fake Users"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        user_map = bpy.data.user_map()

        blenlog = context.scene.blender_log

        category = "Fake User ID"
        blenlog.clear_category(category)

        for id, users in user_map.items():
            if id.library or id.override_library:
                continue
            if id.id_type not in {'BRUSH', 'TEXT'} and id.use_fake_user:
                blenlog.add(
                    name=f"{id.id_type}: {id.name} (Users: {len(users)})",
                    category=category,
                    description="Datablocks with fake users can cause further referenced datablocks to linger in the file. It is recommended not to use fake users, in order to keep files clear of trash data.",
                    icon='FAKE_USER_ON',
                    operator=BLENLOG_OT_clear_fake_user.bl_idname,
                    op_kwargs={'id_name': id.name, 'id_type': id.id_type},
                    op_icon='FAKE_USER_OFF',
                )

        return {'FINISHED'}


class BLENLOG_OT_remap_users(bpy.types.Operator):
    """Remap users of an ID to another of the same type"""

    bl_idname = "blenlog.remap_users"
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

        context.scene.blender_log.remove_active()

        return {'FINISHED'}


class BLENLOG_OT_clear_fake_user(bpy.types.Operator):
    """Clear the fake user flag of an ID."""

    bl_idname = "blenlog.clear_fake_user"
    bl_label = "Clear Fake User"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    id_name: StringProperty()
    id_type: StringProperty()

    def execute(self, context):
        id = get_id(self.id_name, self.id_type)
        if not id:
            self.report({'INFO'}, f"{self.id_type} {self.id_name} had already been removed.")
        else:
            id.use_fake_user = False
            self.report(
                {'INFO'}, f"{self.id_type} {self.id_name} no longer marked with a fake user."
            )

        context.scene.blender_log.remove_active()

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_fake_users,
    BLENLOG_OT_remap_users,
    BLENLOG_OT_clear_fake_user,
]
