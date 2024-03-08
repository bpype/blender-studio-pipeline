import bpy
from bpy.props import StringProperty, IntProperty


class BLENLOG_OT_report_leftover_drivers(bpy.types.Operator):
    """Report drivers that point to nothing"""

    bl_idname = "scene.report_leftover_drivers"
    bl_label = "Report Leftover Drivers"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        blenlog = context.scene.blender_log

        category = 'Leftover Driver'
        blenlog.clear_category(category)

        counter = 0
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
                    counter += 1

        if counter > 0:
            self.report({'WARNING'}, f"Found {counter} left-over drivers.")
        else:
            self.report({'INFO'}, f"No left-over drivers found.")

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


registry = [
    BLENLOG_OT_report_leftover_drivers,
    BLENLOG_OT_delete_driver,
]
