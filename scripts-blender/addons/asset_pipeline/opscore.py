# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time
from pathlib import Path
from .merge.publish import find_sync_target
from .merge.shared_ids import init_shared_ids
from .merge.core import (
    ownership_get,
    ownership_set,
    get_invalid_objects,
    merge_task_layer,
)
from .merge.transfer_data.transfer_ui import draw_transfer_data
from .merge.shared_ids import get_shared_id_icon
from .merge.preserve import Perserve
from . import config, logging
from .hooks import Hooks
from .merge.task_layer import draw_task_layer_selection
from .asset_catalog import get_asset_id
from . import prefs


def sync_poll(cls, context):
    if any([img.is_dirty for img in bpy.data.images]):
        cls.poll_message_set("Please save unsaved Images")
        return False
    if bpy.data.is_dirty:
        cls.poll_message_set("Please save current .blend file")
        return False
    return True


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
            col.label(text="An object is considered invalid if it's not linked")
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


def create_temp_file_backup(self, context):
    temp_file = self._temp_dir.joinpath(
        self._current_file.name.replace(".blend", "") + "_Asset_Pipe_Backup.blend"
    )
    context.scene.asset_pipeline.temp_file = temp_file.__str__()
    return temp_file.__str__()


def update_temp_file_paths(self, context, temp_file_path):
    asset_pipe = context.scene.asset_pipeline
    asset_pipe.temp_file = temp_file_path
    asset_pipe.source_file = self._current_file.__str__()


def sync_execute_pull(self, context):
    start_time = time.time()
    profiler = logging.get_profiler()
    logger = logging.get_logger()
    logger.info("Pulling Asset")
    temp_file_path = create_temp_file_backup(self, context)
    update_temp_file_paths(self, context, temp_file_path)
    bpy.ops.wm.save_as_mainfile(filepath=temp_file_path, copy=True)
    logger.debug(f"Creating Backup File at {temp_file_path}")

    preserve_map = Perserve(context.scene.asset_pipeline.asset_collection)

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
        task_layer
        for task_layer in config.TASK_LAYER_TYPES
        if task_layer not in self._task_layer_keys
    ]

    preserve_map = Perserve(context.scene.asset_pipeline.asset_collection)
    error_msg = merge_task_layer(
        context,
        local_tls=local_tls,
        external_file=self._current_file,
    )
    if error_msg:
        context.scene.asset_pipeline.sync_error = True
        self.report({'ERROR'}, error_msg)
        return {'CANCELLED'}

    preserve_map.unassign_actions()

    if asset_col.asset_data:
        if _catalog_id:
            asset_col.asset_data.catalog_id = _catalog_id

    hooks_instance.execute_hooks(
        merge_mode="push", merge_status='post', asset_col=asset_pipe.asset_collection
    )

    bpy.ops.wm.save_as_mainfile(filepath=file_path)
    bpy.ops.wm.open_mainfile(filepath=self._current_file.__str__())
    profiler.add(time.time() - start_time, "TOTAL")
