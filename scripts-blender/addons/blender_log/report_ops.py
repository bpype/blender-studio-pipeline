import bpy
from bpy.props import StringProperty, IntProperty
from .id_types import get_id

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


class BLENLOG_OT_report_leftover_drivers(bpy.types.Operator):
    """Report drivers that point to nothing"""

    bl_idname = "scene.report_leftover_drivers"
    bl_label = "Report Leftover Drivers"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        blenlog = context.scene.blender_log

        category = 'Leftover Driver'
        blenlog.clear_category(category)

        for obj in bpy.data.objects:
            if obj.library or obj.override_library:
                continue
            if not obj.animation_data:
                continue
            for driver in obj.animation_data.drivers:
                try:
                    obj.path_resolve(driver.data_path)
                except ValueError:
                    # If the RNA path of the driver fails to resolve to some value,
                    # that means the driver is pointing at nothing; A deleted modifier,
                    # constraint, bone, whatever.
                    blenlog.add(
                        description=f"Driver RNA path leads to nothing: '{driver.data_path}'.\nThis can happen when removing modifiers, constraints, bones, etc. that previously had drivers on them. Such driver can be safely deleted, else they will spam the console.",
                        icon='DRIVER_TRANSFORM',
                        name=obj.name,
                        category=category,
                        operator='object.delete_driver',
                        op_kwargs={
                            'object_name': obj.name,
                            'driver_path': driver.data_path,
                            'array_index': driver.array_index,
                        },
                    )

        return {'FINISHED'}


class BLENLOG_OT_delete_driver(bpy.types.Operator):
    """Delete a driver on a local object"""

    bl_idname = "object.delete_driver"
    bl_label = "Delete Driver"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    object_name: StringProperty()
    driver_path: StringProperty()
    array_index: IntProperty()

    def execute(self, context):
        obj = bpy.data.objects.get((self.object_name, None))
        if not obj:
            self.report({'INFO'}, f'Object "{self.object_name}" had already been removed.')
            return {'CANCELLED'}
        if not obj.animation_data or not obj.animation_data.drivers:
            self.report(
                {'INFO'}, f'All drivers of object "{self.object_name}" had already been removed.'
            )
            return {'CANCELLED'}

        logs = context.scene.blender_log

        driver = obj.animation_data.drivers.find(self.driver_path, index=self.array_index)
        if driver:
            obj.animation_data.drivers.remove(driver)
            self.report({'INFO'}, f'Removed driver "{self.driver_path}" from object "{obj.name}"')
        else:
            self.report(
                {'INFO'},
                f'Driver "{self.driver_path} on object "{obj.name}" had already been removed.',
            )

        logs.remove(logs.active_log)

        return {'FINISHED'}


class BLENLOG_OT_rename_id(bpy.types.Operator):
    """Rename a local ID"""

    bl_idname = "object.blenlog_rename_id"
    bl_label = "Rename Object"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    id_name: StringProperty()
    id_type: StringProperty()
    new_name: StringProperty()

    def invoke(self, context, _event):
        if not self.new_name:
            self.new_name = self.id_name
            if self.new_name[-4] == "." and str.isdecimal(self.new_name[-3:]):
                self.new_name = self.new_name[:-4]

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'new_name')
        if get_id(self.new_name, self.id_type):
            self.layout.alert = True
            self.layout.label(text="This name is already taken.", icon='ERROR')

    def execute(self, context):
        obj = get_id(self.id_name, self.id_type)
        if not obj:
            self.report({'ERROR'}, f"ID no longer exists: {self.id_name}.")
            return {'CANCELLED'}
        existing_obj = get_id(self.new_name, self.id_type)
        if existing_obj:
            self.report({'ERROR'}, f"ID name already taken: {self.new_name}.")
            return {'CANCELLED'}

        obj.name = self.new_name
        self.report({'INFO'}, f"{self.id_type.title()} successfully renamed from {self.id_name} to {self.new_name}.")
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

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_collections_with_fake_user,
    BLENLOG_OT_disable_collection_fake_user,
    BLENLOG_OT_report_obdata_names,
    BLENLOG_OT_rename_obdata,
    BLENLOG_OT_report_leftover_drivers,
    BLENLOG_OT_delete_driver,
    BLENLOG_OT_rename_id,
    BLENLOG_OT_remap_users
]
