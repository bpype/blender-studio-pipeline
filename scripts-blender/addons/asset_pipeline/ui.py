import bpy

from pathlib import Path
from .merge.transfer_data.transfer_ui import draw_transfer_data
from .merge.task_layer import draw_task_layer_selection
from .config import verify_json_data
from .prefs import get_addon_prefs
from . import constants
from .merge.publish import is_staged_publish


class ASSETPIPE_PT_sync(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipe 2'
    bl_label = "Asset Management"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline
        if not asset_pipe.is_asset_pipeline_file:
            layout.prop(asset_pipe, "new_file_mode", expand=True)
            layout.prop(asset_pipe, "task_layer_config_type")
            if asset_pipe.new_file_mode == "BLANK":
                layout.prop(asset_pipe, "name")
                layout.prop(asset_pipe, "prefix")
                layout.prop(asset_pipe, "dir")
            else:
                layout.prop(asset_pipe, "asset_collection")
            layout.operator("assetpipe.create_new_asset")
            return

        if not Path(bpy.data.filepath).exists:
            layout.label(text="File is not saved", icon="ERROR")
            return

        if asset_pipe.sync_error or asset_pipe.asset_collection.name.endswith(
            constants.LOCAL_SUFFIX
        ):
            layout.alert = True
            row = layout.row()
            row.label(text="Merge Process has Failed", icon='ERROR')
            row.operator("assetpipe.revert_file", text="Revert", icon="FILE_TICK")
            return

        # TODO Move this call out of the UI because we keep re-loading this file every draw
        if not verify_json_data():
            layout.label(text="Task Layer Config is invalid", icon="ERROR")
            return

        layout.label(text="Local Task Layers:")
        box = layout.box()
        row = box.row(align=True)
        for task_layer in asset_pipe.local_task_layers:
            row.label(text=task_layer.name)

        layout.prop(asset_pipe, "asset_collection")

        staged = is_staged_publish(Path(bpy.data.filepath))
        sync_target_name = "Staged" if staged else "Active"
        layout.operator(
            "assetpipe.sync_push", text=f"Push to {sync_target_name}", icon="TRIA_UP"
        )
        layout.operator(
            "assetpipe.sync_pull",
            text=f"Pull from {sync_target_name}",
            icon="TRIA_DOWN",
        )

        layout.separator()
        if staged:
            layout.operator("assetpipe.publish_staged_as_active", icon="LOOP_FORWARDS")
        layout.operator("assetpipe.publish_new_version", icon="PLUS")
        # TODO Find new way to determine if we are in a published file more explicitly
        # if asset_pipe.is_asset_pipeline_file and asset_pipe.task_layer_name == "NONE":
        # asset_pipe = context.scene.asset_pipeline
        # box = layout.box()
        # box.label(text="Published File Settings")
        # box.prop(asset_pipe, "is_depreciated")


class ASSETPIPE_PT_sync_tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipe 2'
    bl_label = "Tools"
    bl_parent_id = "ASSETPIPE_PT_sync"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("assetpipe.batch_ownership_change")
        layout.operator("assetpipe.revert_file", icon="FILE_TICK")


class ASSETPIPE_PT_sync_advanced(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipe 2'
    bl_label = "Advanced"
    bl_parent_id = "ASSETPIPE_PT_sync"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        prefs = get_addon_prefs()
        return prefs.is_advanced_mode

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.operator("assetpipe.update_ownership", text="Update Ownership")
        box.operator("assetpipe.reset_ownership", icon="LOOP_BACK")
        box = layout.box()
        box.operator("assetpipe.fix_prefixes", icon="CHECKMARK")

        # Task Layer Updater
        box = layout.box()
        box.label(text="Change Local Task Layers")

        row = box.row()
        asset_pipe = context.scene.asset_pipeline
        all_task_layers = asset_pipe.all_task_layers
        for task_layer in all_task_layers:
            row.prop(task_layer, "is_local", text=task_layer.name)
        box.operator("assetpipe.update_local_task_layers")


class ASSETPIPE_PT_ownership_inspector(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipe 2'
    bl_label = "Ownership Inspector"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline
        scene = context.scene
        if not asset_pipe.is_asset_pipeline_file:
            layout.label(text="Open valid 'Asset Pipeline' file", icon="ERROR")
            return

        if context.collection in list(asset_pipe.asset_collection.children):
            col = context.collection
            row = layout.row()
            row.label(
                text=f"{col.name}: ",
                icon="OUTLINER_COLLECTION",
            )
            draw_task_layer_selection(layout=row, data=col)

        if not context.active_object:
            layout.label(text="Set an Active Object to Inspect", icon="OBJECT_DATA")
            return
        obj = context.active_object
        transfer_data = obj.transfer_data_ownership
        layout = layout.box()
        row = layout.row()
        row.label(text=f"{obj.name}: ", icon="OBJECT_DATA")

        if obj.get("asset_id_surrender"):
            enabled = (
                False
                if obj.asset_id_owner in asset_pipe.get_local_task_layers()
                else True
            )
            row.enabled = enabled
            col = row.column()
            col.operator("assetpipe.update_surrendered_object")

        # New Row inside a column because draw_task_layer_selection() will enable/disable the entire row
        # Only need this to affect itself and the "surrender" property
        col = row.column()
        task_layer_row = col.row()

        draw_task_layer_selection(layout=task_layer_row, data=obj)
        surrender_icon = "ORPHAN_DATA" if obj.get("asset_id_surrender") else "HEART"
        task_layer_row.prop(obj, "asset_id_surrender", text="", icon=surrender_icon)
        draw_transfer_data(transfer_data, layout)


classes = (
    ASSETPIPE_PT_sync,
    ASSETPIPE_PT_sync_advanced,
    ASSETPIPE_PT_sync_tools,
    ASSETPIPE_PT_ownership_inspector,
)


def register():
    for i in classes:
        bpy.utils.register_class(i)


def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
