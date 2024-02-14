import bpy
from bpy.props import StringProperty


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


class BLENLOG_OT_rename_obdata(bpy.types.Operator):
    """Disable fake user flag on the collection"""

    bl_idname = "object.rename_data"
    bl_label = "Rename Object Data"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    obj_name: StringProperty()

    def execute(self, context):
        logs = context.scene.blender_log

        obj = bpy.data.objects.get((self.obj_name, None))
        if not obj:
            self.report({'WARNING'}, "Object no longer exists.")
        else:
            obj.data.name = obj.name
            if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                obj.data.shape_keys.name = obj.name
            self.report({'INFO'}, "Object data renamed.")

        logs.remove(logs.active_log)

        return {'FINISHED'}


class BLENLOG_OT_report_obdata_names(bpy.types.Operator):
    """Report objects with data or shape keys not named the same as the object"""

    bl_idname = "scene.report_obdata_name_mismatch"
    bl_label = "Report Mis-Named Object Datas"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        blenlog = context.scene.blender_log

        category = "Object Data Name Mismatch"
        blenlog.clear_category(category)

        counter = 0
        for obj in bpy.data.objects:
            if not obj.data:
                continue
            # Skip if obj or data is linked
            if obj.library or obj.override_library or obj.data.library or obj.data.override_library:
                continue

            if obj.data.name != obj.name:
                blenlog.add(
                    name=obj.name + " (Data)",
                    category=category,
                    description="Object data is not named the same as the containing object. This is unavoidable for multi-user object datas though.",
                    icon='FILE_TEXT',
                    operator=BLENLOG_OT_rename_obdata.bl_idname,
                    op_kwargs={'obj_name': obj.name},
                    op_icon='GREASEPENCIL',
                )
                counter += 1

            if not hasattr(obj.data, 'shape_keys'):
                continue
            if not obj.data.shape_keys:
                continue

            if obj.data.shape_keys.name != obj.name:
                blenlog.add(
                    name=obj.name + " (Shape Key Data)",
                    category=category,
                    description="Shape Key datablock is not named the same as the containing object. This is unavoidable for multi-user object datas though.",
                    icon='FILE_TEXT',
                    operator=BLENLOG_OT_rename_obdata.bl_idname,
                    op_kwargs={'obj_name': obj.name},
                    op_icon='GREASEPENCIL',
                )
                counter += 1

        if counter == 0:
            self.report({'INFO'}, "No objects with mismatched data names.")
        else:
            self.report({'WARNING'}, f"Found {counter} mismatched datablock names.")

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_collections_with_fake_user,
    BLENLOG_OT_disable_collection_fake_user,
    BLENLOG_OT_report_obdata_names,
    BLENLOG_OT_rename_obdata,
]
