# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from addon_utils import check as check_addon

from pathlib import Path
from .merge.transfer_data.transfer_ui import draw_transfer_data
from .merge.task_layer import draw_task_layer_selection
from .config import verify_task_layer_json_data
from .prefs import get_addon_prefs
from . import constants
from .merge.publish import is_staged_publish
from bpy.types import UILayout, Context, Panel


class ASSETPIPE_PT_sync(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assset Pipeline'
    bl_label = "Asset Management"

    def draw_collection_selection(self, layout: UILayout, context: Context) -> None:
        layout.prop_search(
            context.scene.asset_pipeline, 'asset_collection_name', bpy.data, 'collections'
        )

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
                layout.prop_search(asset_pipe, 'asset_collection_name', bpy.data, 'collections')
            layout.operator("assetpipe.create_new_asset")
            return

        if not Path(bpy.data.filepath).exists:
            layout.label(text="File is not saved", icon="ERROR")
            return

        if asset_pipe.asset_collection is not None and (
            asset_pipe.sync_error
            or asset_pipe.asset_collection.name.endswith(constants.LOCAL_SUFFIX)
        ):
            layout.alert = True
            row = layout.row()
            row.label(text="Merge Process has Failed", icon='ERROR')
            row.operator("assetpipe.revert_file", text="Revert", icon="FILE_TICK")
            return

        # TODO Move this call out of the UI because we keep re-loading this file every draw
        if not verify_task_layer_json_data() and not asset_pipe.is_published:
            layout.label(text="Task Layer Config is invalid", icon="ERROR")
            return
        if asset_pipe.is_published:
            layout.label(text="Current File is Published")
            col = layout.column()
            col.active = False
            self.draw_collection_selection(col, context)
            return

        layout.label(text="Local Task Layers:")
        box = layout.box()
        row = box.row(align=True)
        for task_layer in asset_pipe.local_task_layers:
            row.label(text=task_layer.name)

        self.draw_collection_selection(layout, context)

        staged = is_staged_publish(Path(bpy.data.filepath))
        sync_target_name = "Staged" if staged else "Active"
        layout.operator(
            "assetpipe.sync_pull",
            text=f"Pull from {sync_target_name}",
            icon="TRIA_DOWN",
        )
        sync_text = f"Sync from {sync_target_name}"
        push_text = f"Force Push to {sync_target_name}"
        if check_addon('blender_log')[1]:
            log_count = len(list(context.scene.blender_log.all_logs))
            if log_count > 0:
                issues_text = f" ({log_count} issues)"
                sync_text += issues_text
                push_text += issues_text
        layout.operator("assetpipe.sync_push", text=sync_text, icon="FILE_REFRESH").pull = True
        layout.operator("assetpipe.sync_push", text=push_text, icon="TRIA_UP").pull = False


class ASSETPIPE_PT_publish(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assset Pipeline'
    bl_label = "Publish"
    bl_parent_id = "ASSETPIPE_PT_sync"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(not context.scene.asset_pipeline.is_published)

    def draw(self, context: bpy.types.Context) -> None:
        staged = is_staged_publish(Path(bpy.data.filepath))
        layout = self.layout
        if staged:
            layout.operator("assetpipe.publish_staged_as_active", icon="LOOP_FORWARDS")
        layout.operator("assetpipe.publish_new_version", icon="PLUS")
        layout.operator("assetpipe.open_publish", icon="FILE")


class ASSETPIPE_PT_working_files(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assset Pipeline'
    bl_label = "Working Files"
    bl_parent_id = "ASSETPIPE_PT_sync"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.asset_pipeline.is_published

    def draw(self, context: bpy.types.Context) -> None:
        for file in Path(bpy.data.filepath).parent.parent.glob("*.blend"):
            name = f"Open {file.name.strip('.blend')}"
            self.layout.operator("assetpipe.open_file", text=name).filepath = str(file)


class ASSETPIPE_PT_sync_tools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assset Pipeline'
    bl_label = "Tools"
    bl_parent_id = "ASSETPIPE_PT_sync"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(not context.scene.asset_pipeline.is_published)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        cat_row = layout.row(align=True)
        cat_row.prop(context.scene.asset_pipeline, 'asset_catalog_name')
        cat_row.operator("assetpipe.refresh_asset_cat", icon='FILE_REFRESH', text="")
        layout.operator("assetpipe.batch_ownership_change")
        layout.operator("assetpipe.revert_file", icon="FILE_TICK")
        layout.separator()
        col = layout.column(align=True)
        col.operator("assetpipe.save_production_hook", text="Create Production Hook").mode = 'PROD'
        col.operator("assetpipe.save_production_hook", text="Create Asset Hook").mode = 'ASSET'


class ASSETPIPE_PT_sync_advanced(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assset Pipeline'
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
        box.operator("assetpipe.prepare_sync")
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
    bl_category = 'Assset Pipeline'
    bl_label = "Ownership Inspector"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline
        scene = context.scene
        if not asset_pipe.is_asset_pipeline_file:
            layout.label(text="Open valid 'Asset Pipeline' file", icon="ERROR")
            return

        if asset_pipe.asset_collection is not None and context.collection in list(
            asset_pipe.asset_collection.children
        ):
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
            enabled = False if obj.asset_id_owner in asset_pipe.get_local_task_layers() else True
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
    ASSETPIPE_PT_working_files,
    ASSETPIPE_PT_sync_tools,
    ASSETPIPE_PT_publish,
    ASSETPIPE_PT_ownership_inspector,
)


def register():
    for i in classes:
        bpy.utils.register_class(i)


def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
