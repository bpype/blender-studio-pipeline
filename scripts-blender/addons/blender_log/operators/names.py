# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import StringProperty
from ..id_types import get_id


def get_blender_number_suffix(name):
    if name[-4] == "." and str.isdecimal(name[-3:]):
        return name[-4:]
    return ""


def name_without_number(name):
    suffix = get_blender_number_suffix(name)
    if suffix:
        return name[:-4]


class BLENLOG_OT_rename_obdata(bpy.types.Operator):
    """Disable fake user flag on the collection"""

    bl_idname = "blenlog.rename_object_data"
    bl_label = "Rename Object Data"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    obj_name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get((self.obj_name, None))
        if not obj:
            self.report({'WARNING'}, "Object no longer exists.")
        else:
            if obj.data.name != obj.name:
                obj.data.name = obj.name
            if hasattr(obj.data, 'shape_keys') and obj.data.shape_keys:
                if obj.data.shape_keys.name != obj.name:
                    obj.data.shape_keys.name = obj.name
            self.report({'INFO'}, "Object data renamed.")

        context.scene.blender_log.remove_active()

        return {'FINISHED'}


class BLENLOG_OT_report_obdata_names(bpy.types.Operator):
    """Report objects with data or shape keys not named the same as the object"""

    bl_idname = "blenlog.report_obdata_name_mismatch"
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


class BLENLOG_OT_rename_id(bpy.types.Operator):
    """Rename a local ID"""

    bl_idname = "blenlog.rename_id"
    bl_label = "Rename ID"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    id_name: StringProperty()
    id_type: StringProperty()
    new_name: StringProperty(name="Name")

    def invoke(self, context, _event):
        if not self.new_name:
            self.new_name = self.id_name
            if get_blender_number_suffix(self.new_name):
                self.new_name = name_without_number(self.new_name)

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'new_name')
        if get_id(self.new_name, self.id_type):
            self.layout.alert = True
            self.layout.label(text="This name is already taken.", icon='ERROR')

    def execute(self, context):
        id = get_id(self.id_name, self.id_type)
        if not id:
            self.report({'ERROR'}, f"ID no longer exists: {self.id_name}.")
            return {'CANCELLED'}
        existing_id = get_id(self.new_name, self.id_type)
        if existing_id:
            self.report({'ERROR'}, f"ID name already taken: {self.new_name}.")
            return {'CANCELLED'}

        if id.name != self.new_name:
            id.name = self.new_name
        self.report(
            {'INFO'},
            f"{self.id_type.title()} successfully renamed from {self.id_name} to {self.new_name}.",
        )
        context.scene.blender_log.remove_active()
        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_obdata_names,
    BLENLOG_OT_rename_obdata,
    BLENLOG_OT_rename_id,
]
