# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import StringProperty, IntProperty
from bpy.types import Object

from typing import List

def report_invalid_drivers(context, objects: List[Object]):
    blenlog = context.scene.blender_log

    cat_leftover = 'Leftover Driver'
    blenlog.clear_category(cat_leftover)

    cat_invalid = 'Invalid Driver'
    blenlog.clear_category(cat_invalid)

    counter = 0
    for obj in objects:
        if obj.library or obj.override_library:
            continue
        if not obj.animation_data:
            continue
        for fcurve in obj.animation_data.drivers:
            kwargs = {
                'icon': 'DRIVER_TRANSFORM',
                'operator': BLENLOG_OT_delete_driver.bl_idname,
                'op_kwargs': {
                    'object_name': obj.name,
                    'driver_path': fcurve.data_path,
                    'array_index': fcurve.array_index,
                },
            }
            try:
                obj.path_resolve(fcurve.data_path)
            except ValueError:
                # If the RNA path of the driver fails to resolve to some value,
                # that means the driver is pointing at nothing; A deleted modifier,
                # constraint, bone, whatever.
                blenlog.add(
                    description=f"Driver RNA path leads to nothing: '{fcurve.data_path}'.\nThis can happen when removing modifiers, constraints, bones, etc. that previously had drivers on them. Such driver can be safely deleted, else they will spam the console.",
                    name=obj.name,
                    category=cat_leftover,
                    **kwargs
                )
                counter += 1
                continue
            if not fcurve.driver.is_valid:
                blenlog.add(
                    description=f"Invalid Driver: '{fcurve.data_path}'.\nThis can happen when a driver var target datablock is removed, an expression is invalid, etc.",
                    name=obj.name,
                    category=cat_invalid,
                    **kwargs
                )
                counter += 1

    return counter

report_leftover_drivers = report_invalid_drivers

class BLENLOG_OT_report_invalid_drivers(bpy.types.Operator):
    """Report drivers that point to nothing"""

    bl_idname = "blenlog.report_invalid_drivers"
    bl_label = "Report Leftover Drivers"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        counter = report_invalid_drivers(context, bpy.data.objects)

        if counter > 0:
            self.report({'WARNING'}, f"Found {counter} invalid drivers.")
        else:
            self.report({'INFO'}, f"No invalid drivers found.")

        return {'FINISHED'}


class BLENLOG_OT_delete_driver(bpy.types.Operator):
    """Delete a driver on a local object"""

    bl_idname = "blenlog.delete_driver"
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
    BLENLOG_OT_report_invalid_drivers,
    BLENLOG_OT_delete_driver,
]
