# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import StringProperty
from bpy.types import Context, Event, Operator

from ..merge import task_layer


class ASSETPIPE_OT_update_surrendered_object(Operator):
    bl_idname = "assetpipe.update_surrendered_object"
    bl_label = "Claim Surrendered"
    bl_description = """Claim Surrended Object Owner"""
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context: Context, event: Event):
        obj = context.active_object
        self._old_owner = obj.asset_id_owner
        # Set Asset ID Owner to a local ID
        obj.asset_id_owner = context.scene.asset_pipeline.get_local_task_layers()[0]
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()

        task_layer.draw_task_layer_selection(
            context,
            layout=row,
            prop_owner=context.active_object,
        )

    def execute(self, context: Context):
        obj = context.active_object
        if obj.asset_id_owner == self._old_owner:
            self.report({'ERROR'}, "Object Owner was not updated")
            return {'CANCELLED'}
        obj.asset_id_surrender = False
        return {'FINISHED'}


class ASSETPIPE_OT_update_surrendered_transfer_data(Operator):
    bl_idname = "assetpipe.update_surrendered_transfer_data"
    bl_label = "Claim Surrendered"
    bl_description = """Claim Surrended Transferable Data Owner"""
    bl_options = {'REGISTER', 'UNDO'}

    transfer_data_item_name: StringProperty(name="Transferable Data Item Name")

    _surrendered_transfer_data = None
    _old_owner = ""

    def invoke(self, context: Context, event: Event):
        obj = context.active_object
        for transfer_data_item in obj.transfer_data_ownership:
            if transfer_data_item.name == self.transfer_data_item_name:
                self._surrendered_transfer_data = transfer_data_item
                self._old_owner = self._surrendered_transfer_data.owner
        # Set Default Owner
        asset_pipe = context.scene.asset_pipeline
        owner, _ = task_layer.get_transfer_data_owner(
            asset_pipe, self._surrendered_transfer_data.type, self._surrendered_transfer_data.name
        )
        self._surrendered_transfer_data.owner = owner
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()

        task_layer.draw_task_layer_selection(
            context,
            layout=row,
            prop_owner=self._surrendered_transfer_data,
        )

    def execute(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        if self._surrendered_transfer_data.owner == self._old_owner:
            self.report({'ERROR'}, "Transferable Data Owner was not updated")
            return {'CANCELLED'}
        self._surrendered_transfer_data.surrender = False
        task_layer.get_transfer_data_owner(asset_pipe, self._surrendered_transfer_data.type)
        return {'FINISHED'}

registry = [
    ASSETPIPE_OT_update_surrendered_object,
    ASSETPIPE_OT_update_surrendered_transfer_data,
]
