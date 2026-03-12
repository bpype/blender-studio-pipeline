# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import bpy
from addon_utils import check as check_addon
from bpy.types import Context, Panel, UILayout

from . import constants
from .config import verify_task_layer_json_data
from .merge.publish import is_staged_publish


class ASSETPIPE_PT_initialize_asset(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Initialize Asset"

    @classmethod
    def poll(cls, context):
        asset_pipe = context.scene.asset_pipeline
        return not (asset_pipe.is_asset_pipeline_file or context.scene.asset_pipeline.is_published)

    def draw(self, context: Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline
        layout.prop(asset_pipe, "new_file_mode", expand=True)
        layout.prop(asset_pipe, "task_layer_config_type")
        if asset_pipe.new_file_mode == "BLANK":
            layout.prop(asset_pipe, "name")
            layout.prop(asset_pipe, "prefix")
            layout.prop(asset_pipe, "dir")
        else:
            layout.prop_search(asset_pipe, 'asset_collection_name', bpy.data, 'collections')
        layout.operator("assetpipe.create_new_asset")


class ASSETPIPE_PT_working_files(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Working Files"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return context.scene.asset_pipeline.is_published

    def draw(self, context: Context) -> None:
        for file in Path(bpy.data.filepath).parent.parent.glob("*.blend"):
            name = f"Open {file.name.strip('.blend')}"
            self.layout.operator("assetpipe.open_file", text=name).filepath = str(file)


class ASSETPIPE_PT_configure(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Configure"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not (ASSETPIPE_PT_initialize_asset.poll(context) or ASSETPIPE_PT_working_files.poll(context))

    def draw(self, context: Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Local Task Layers:")
        row.operator("assetpipe.update_local_task_layers", text="", icon='SETTINGS')
        row = box.row(align=True)
        for task_layer in asset_pipe.local_task_layers:
            row.label(text=task_layer.name)

        self.draw_collection_selection(layout, context)

        cat_row = layout.row(align=True)
        cat_row.prop(context.scene.asset_pipeline, 'asset_catalog_name')
        cat_row.operator("assetpipe.refresh_asset_cat", icon='FILE_REFRESH', text="")

    def draw_collection_selection(self, layout: UILayout, context: Context) -> None:
        layout.prop_search(
            context.scene.asset_pipeline, 'asset_collection_name', bpy.data, 'collections'
        )


def poll_valid_workfile(context) -> bool:
    if ASSETPIPE_PT_initialize_asset.poll(context):
        return False
    if ASSETPIPE_PT_working_files.poll(context):
        return False
    if not context.scene.asset_pipeline.asset_collection:
        return False
    return True


class ASSETPIPE_PT_sync(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Sync"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return poll_valid_workfile(context)

    def draw(self, context: Context) -> None:
        layout = self.layout
        asset_pipe = context.scene.asset_pipeline

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

        staged = is_staged_publish(Path(bpy.data.filepath))
        sync_target_name = "Staged" if staged else "Active"
        sync_text = f"Sync with {sync_target_name}"
        push_text = f"Push to {sync_target_name}"
        if check_addon('blender_log')[1]:
            log_count = len(list(context.scene.blender_log.all_logs))
            if log_count > 0:
                issues_text = f" ({log_count} issues)"
                sync_text += issues_text
                push_text += issues_text
        layout.operator("assetpipe.sync_push", text=sync_text, icon="FILE_REFRESH").pull = True

        header, panel = layout.panel("Asset Pipeline Sync Steps")
        header.label(text="Steps")
        if panel:
            panel.separator()
            panel.operator("assetpipe.prepare_sync")

            panel.operator(
                "assetpipe.sync_pull",
                text=f"Pull from {sync_target_name}",
                icon="TRIA_DOWN",
            )
            panel.operator("assetpipe.sync_push", text=push_text, icon="TRIA_UP").pull = False


class ASSETPIPE_PT_publish(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Publish"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return poll_valid_workfile(context)

    def draw(self, context: Context) -> None:
        staged = is_staged_publish(Path(bpy.data.filepath))
        layout = self.layout
        if staged:
            layout.operator("assetpipe.publish_staged_as_active", icon="LOOP_FORWARDS")
        layout.operator("assetpipe.publish_new_version", icon="FILE_NEW")
        layout.operator("assetpipe.open_publish", icon="FILE")


class ASSETPIPE_PT_sync_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Asset Pipeline'
    bl_label = "Tools"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return poll_valid_workfile(context)

    def draw(self, context: Context) -> None:
        layout = self.layout
        layout.operator("assetpipe.revert_file", icon="LOOP_BACK")

        col = layout.column(align=True)
        col.operator("assetpipe.save_production_hook", text="Create Production Hook", icon='HOOK').mode = 'PROD'
        col.operator("assetpipe.save_production_hook", text="Create Asset Hook", icon='HOOK').mode = 'ASSET'
        layout.operator("assetpipe.fix_prefixes", icon="MODIFIER")


registry = [
    ASSETPIPE_PT_initialize_asset,
    ASSETPIPE_PT_configure,
    ASSETPIPE_PT_sync,
    ASSETPIPE_PT_publish,
    ASSETPIPE_PT_sync_tools,
    ASSETPIPE_PT_working_files,
]
