# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from pathlib import Path

import bpy
from bpy.props import BoolProperty
from bpy.types import Context, Event, Operator

from .. import config, logging, prefs
from ..asset_catalog import get_asset_id
from ..hooks import Hooks
from ..images import save_images
from ..merge.core import (
    get_invalid_objects,
    merge_task_layer,
    ownership_get,
    ownership_set,
)
from ..merge.preserve import Preserve
from ..merge.publish import find_sync_target
from ..merge.shared_ids import get_shared_id_icon, init_shared_ids
from ..merge.task_layer import draw_task_layer_selection
from ..merge.transfer_data.transfer_ui import draw_transfer_data


class ASSETPIPE_OT_prepare_sync(bpy.types.Operator):
    bl_idname = "assetpipe.prepare_sync"
    bl_label = "Prepare Sync"
    bl_description = (
        "Prepare all Objects for Sync; by updating the Ownership of Objects "
        "and Transferable Data. Also runs Pre-Pull hooks")
    bl_options = {'REGISTER', 'UNDO'}

    _temp_transfer_data = None
    _invalid_objs = []
    _other_ids = []

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        sync_draw(self, context)

    def execute(self, context: bpy.types.Context):
        asset_col = context.scene.asset_pipeline.asset_collection
        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        hooks_instance.execute_hooks(merge_mode="pull",
                                     merge_status='pre',
                                     asset_col=asset_col)

        sync_execute_update_ownership(self, context)
        self.report({'INFO'}, "Ownership Updated")
        return {'FINISHED'}


class ASSETPIPE_OT_sync_pull(Operator):
    bl_idname = "assetpipe.sync_pull"
    bl_label = "Pull Asset"
    bl_description = """Pull Task Layers from the published sync target"""
    bl_options = {'REGISTER', 'UNDO'}

    _temp_transfer_data = None
    _invalid_objs = []
    _other_ids = []
    _temp_dir: Path = None
    _current_file: Path = None
    _task_layer_key: str = ""
    _sync_target: Path = None

    save: BoolProperty(
        name="Save File & Images",
        default=True,
        description="Save Current File and Images before Push",
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if context.mode == 'OBJECT':
            return True
        cls.poll_message_set("Pull is only avaliable in Object Mode")
        return False

    def invoke(self, context: Context, event: Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        self.layout.prop(self, "save")
        sync_draw(self, context)

    def execute(self, context: Context):
        profiler = logging.get_profiler()
        profiler.reset()
        asset_col = context.scene.asset_pipeline.asset_collection
        if self.save:
            save_images()
            bpy.ops.wm.save_mainfile()

        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        hooks_instance.execute_hooks(merge_mode="pull",
                                     merge_status='pre',
                                     asset_col=asset_col)
        # Find current task Layer
        sync_execute_update_ownership(self, context)
        sync_execute_prepare_sync(self, context)
        sync_execute_pull(self, context)

        hooks_instance.execute_hooks(merge_mode="pull",
                                     merge_status='post',
                                     asset_col=asset_col)
        self.report({'INFO'}, "Asset Pull Complete")
        profiler.log_all()
        return {'FINISHED'}


class ASSETPIPE_OT_sync_push(Operator):
    bl_idname = "assetpipe.sync_push"
    bl_label = "Sync Asset"
    bl_description = """Sync the current Task Layer to the published sync target. File will be saved as part of the Push process"""

    _temp_transfer_data = None
    _invalid_objs = []
    _other_ids = []
    _temp_dir: Path = None
    _current_file: Path = None
    _task_layer_key: str = ""
    _sync_target: Path = None

    pull: BoolProperty(
        name="Pull before Pushing",
        default=True,
        description=
        "Pull in any new data from the Published file before Pushing",
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if context.mode == 'OBJECT':
            return True
        cls.poll_message_set("Push is only avaliable in Object Mode")
        return False

    def invoke(self, context: Context, event: Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        if not self.pull:
            col = self.layout.column()
            col.label(text="Force Pushing without pulling can cause data loss",
                      icon="ERROR")
            col.separator()
        sync_draw(self, context)

    def execute(self, context: Context):
        profiler = logging.get_profiler()
        profiler.reset()
        asset_col = context.scene.asset_pipeline.asset_collection
        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        save_images()
        bpy.ops.wm.save_mainfile()

        # Seperate if statement so hook can execute before updating ownership/prep sync
        if self.pull:
            hooks_instance.execute_hooks(merge_mode="pull",
                                         merge_status='pre',
                                         asset_col=asset_col)
        # Find current task Layer
        sync_execute_update_ownership(self, context)
        sync_execute_prepare_sync(self, context)

        if self.pull:
            sync_execute_pull(self, context)
            hooks_instance.execute_hooks(merge_mode="pull",
                                         merge_status='post',
                                         asset_col=asset_col)

        profiler.set_push()
        hooks_instance.execute_hooks(merge_mode="push",
                                     merge_status='pre',
                                     asset_col=asset_col)
        bpy.ops.wm.save_mainfile(filepath=self._current_file.__str__())

        sync_execute_push(self, context)
        if self.pull:
            self.report({'INFO'}, "Asset Sync Complete")
        else:
            self.report({'INFO'}, "Asset Force Push Complete")
        profiler.log_all()
        return {'FINISHED'}


def sync_invoke(self, context):
    logger = logging.get_logger()
    logger.info("Loading Transfer Data")
    self._temp_transfer_data = context.scene.asset_pipeline.temp_transfer_data
    self._temp_transfer_data.clear()
    self._invalid_objs.clear()

    asset_pipe = context.scene.asset_pipeline
    local_col = asset_pipe.asset_collection
    if not local_col:
        self.report({'ERROR'}, "Top level collection could not be found")
        return {'CANCELLED'}

    ownership_get(local_col, context.scene)

    self._invalid_objs = get_invalid_objects(asset_pipe, local_col)
    self._shared_ids = init_shared_ids(context.scene)


def sync_draw(self, context):
    layout = self.layout
    row = layout.row()

    if len(self._invalid_objs) != 0:
        main_col = layout.column(align=True)
        main_col.alert = True
        header, panel = main_col.panel("Invalid Objects")
        header.label(text="Sync will delete Invalid Objects", icon='TRASH')
        if panel:
            col = panel.column(align=True)
            col.label(
                text="An object is considered invalid if it's not linked")
            col.label(text="to the collection of its owning task layer.")
            col.separator()
            for obj in self._invalid_objs:
                panel.label(text=obj.name, icon="OBJECT_DATA")

    if len(self._shared_ids) != 0:
        header, panel = layout.panel("Shared IDs")
        header.label(text="New Shared IDs", icon='COLLAPSEMENU')
        if panel:
            for id in self._shared_ids:
                row = panel.row()
                row.label(text=id.name, icon=get_shared_id_icon(id))
                draw_task_layer_selection(
                    context,
                    layout=row,
                    data=id,
                )

    if len(self._temp_transfer_data) == 0:
        layout.label(text="No new local Transferable Data found")
        return
    else:
        header, panel = layout.panel("New Data")
        header.label(text="New Data To Push", icon='COLLAPSEMENU')
        if not panel:
            return

    objs = [
        bpy.data.objects.get(transfer_data_item.obj_name)
        for transfer_data_item in self._temp_transfer_data
    ]

    for obj in sorted(set(objs), key=lambda o: o.name):
        obj_ownership = [
            transfer_data_item
            for transfer_data_item in self._temp_transfer_data
            if bpy.data.objects.get(transfer_data_item.obj_name) == obj
        ]
        box = layout.box()
        header, panel = box.panel(obj.name, default_closed=True)
        header.label(text=obj.name, icon='OBJECT_DATA')
        if panel:
            draw_transfer_data(context, obj_ownership, panel)


def sync_execute_update_ownership(self, context):
    logger = logging.get_logger()
    logger.info("Updating Ownership")
    temp_transfer_data = context.scene.asset_pipeline.temp_transfer_data
    ownership_set(temp_transfer_data)


def sync_execute_prepare_sync(self, context):
    asset_pipe = context.scene.asset_pipeline
    self._current_file = Path(bpy.data.filepath)
    self._temp_dir = Path(bpy.app.tempdir).parent
    self._task_layer_keys = asset_pipe.get_local_task_layers()

    self._sync_target = find_sync_target(self._current_file)
    if not self._sync_target.exists():
        self.report({'ERROR'}, "Sync Target could not be determined")
        return {'CANCELLED'}

    for obj in self._invalid_objs:
        bpy.data.objects.remove(obj)


def sync_execute_pull(self, context):
    start_time = time.time()
    profiler = logging.get_profiler()
    logger = logging.get_logger()
    logger.info("Pulling Asset")
    temp_file_path = create_temp_file_backup(self, context)
    update_temp_file_paths(self, context, temp_file_path)
    bpy.ops.wm.save_as_mainfile(filepath=temp_file_path, copy=True)
    logger.debug(f"Creating Backup File at {temp_file_path}")

    preserve_map = Preserve(context.scene.asset_pipeline.asset_collection)

    error_msg = merge_task_layer(
        context,
        local_tls=self._task_layer_keys,
        external_file=self._sync_target,
    )

    addon_prefs = prefs.get_addon_prefs()
    if addon_prefs.preserve_action:
        preserve_map.set_action_map()

    if addon_prefs.preserve_indexes:
        preserve_map.set_active_index_map()

    if error_msg:
        context.scene.asset_pipeline.sync_error = True
        self.report({'ERROR'}, error_msg)
        return {'CANCELLED'}
    profiler.add(time.time() - start_time, "TOTAL")


def create_temp_file_backup(self, context):
    temp_file = self._temp_dir.joinpath(
        self._current_file.name.replace(".blend", "") +
        "_Asset_Pipe_Backup.blend")
    context.scene.asset_pipeline.temp_file = temp_file.__str__()
    return temp_file.__str__()


def update_temp_file_paths(self, context, temp_file_path):
    asset_pipe = context.scene.asset_pipeline
    asset_pipe.temp_file = temp_file_path
    asset_pipe.source_file = self._current_file.__str__()


def sync_execute_push(self, context):
    start_time = time.time()
    profiler = logging.get_profiler()
    logger = logging.get_logger()
    logger.info("Pushing Asset")
    _catalog_id = None
    hooks_instance = Hooks()
    hooks_instance.load_hooks(context)
    temp_file_path = create_temp_file_backup(self, context)
    _catalog_id = get_asset_id(context.scene.asset_pipeline.asset_catalog_name)

    file_path = self._sync_target.__str__()
    bpy.ops.wm.open_mainfile(filepath=file_path)
    asset_pipe = context.scene.asset_pipeline
    asset_col = asset_pipe.asset_collection
    update_temp_file_paths(self, context, temp_file_path)

    local_tls = [
        task_layer for task_layer in config.TASK_LAYER_TYPES
        if task_layer not in self._task_layer_keys
    ]

    error_msg = merge_task_layer(
        context,
        local_tls=local_tls,
        external_file=self._current_file,
    )
    if error_msg:
        context.scene.asset_pipeline.sync_error = True
        self.report({'ERROR'}, error_msg)
        return {'CANCELLED'}

    if asset_col.asset_data:
        if _catalog_id:
            asset_col.asset_data.catalog_id = _catalog_id

    hooks_instance.execute_hooks(merge_mode="push",
                                 merge_status='post',
                                 asset_col=asset_pipe.asset_collection)

    bpy.ops.wm.save_as_mainfile(filepath=file_path)
    bpy.ops.wm.open_mainfile(filepath=self._current_file.__str__())
    profiler.add(time.time() - start_time, "TOTAL")


registry = [
    ASSETPIPE_OT_prepare_sync,
    ASSETPIPE_OT_sync_pull,
    ASSETPIPE_OT_sync_push,
]
