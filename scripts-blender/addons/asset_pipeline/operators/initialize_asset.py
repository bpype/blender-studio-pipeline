# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.types import Context, Operator

from .. import config, constants
from ..merge import publish


class ASSETPIPE_OT_create_new_asset(Operator):
    bl_idname = "assetpipe.create_new_asset"
    bl_label = "Create New Asset"
    bl_description = """Create a new Asset Files and Folders at a given directory"""

    _name = ""
    _prefix = ""
    _json_path = None
    _asset_pipe = None

    create_files: BoolProperty(name="Create Files for Unselected Task Layers",
                               default=True)

    # Only Active/Stage Publish Types are avaliable
    publish_type: EnumProperty(
        name="Publish Type",
        items=constants.PUBLISH_TYPES[:2],
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        asset_pipe = context.scene.asset_pipeline
        if asset_pipe.new_file_mode == "KEEP":
            if not asset_pipe.asset_collection:
                cls.poll_message_set("Missing Top Level Collection")
                return False
        else:
            if asset_pipe.name == "" or asset_pipe.dir == "":
                cls.poll_message_set("Asset Name and Directory must be valid")
                return False
        return True

    def invoke(self, context: Context, event):
        # Dynamically Create Task Layer Bools
        self._asset_pipe = context.scene.asset_pipeline

        config.verify_task_layer_json_data(
            self._asset_pipe.task_layer_config_type)

        all_task_layers = self._asset_pipe.all_task_layers
        all_task_layers.clear()

        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key == "NONE":
                continue
            new_task_layer = all_task_layers.add()
            new_task_layer.name = task_layer_key
        self.publish_type = constants.STAGED_PUBLISH_KEY
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        box = self.layout.box()
        all_task_layers = self._asset_pipe.all_task_layers

        box.label(
            text="Choose Which Task Layers will be local the current file")
        for task_layer_bool in all_task_layers:
            box.prop(task_layer_bool, "is_local", text=task_layer_bool.name)
        self.layout.prop(self, "create_files")
        self.layout.prop(self, "publish_type")

    def _asset_name_set(self, context) -> None:
        if self._asset_pipe.new_file_mode == "KEEP":
            asset_col = self._asset_pipe.asset_collection
            name = (asset_col.name if constants.NAME_DELIMITER
                    not in asset_col.name else asset_col.name.split(
                        constants.NAME_DELIMITER, 1)[1])
            prefix = ("" if constants.NAME_DELIMITER not in asset_col.name else
                      asset_col.name.split(constants.NAME_DELIMITER, 1)[0])

        else:
            name = self._asset_pipe.name
            prefix = self._asset_pipe.prefix

        # Set to easily access these properties
        self._name = name
        self._prefix = prefix

        # Store these in the asset pipeline props group
        self._asset_pipe.name = name
        self._asset_pipe.prefix = prefix

    def _asset_dir_get(self, context) -> str:
        if self._asset_pipe.new_file_mode == "KEEP":
            return Path(bpy.data.filepath).parent.__str__()

        else:
            user_dir = bpy.path.abspath(self._asset_pipe.dir)
            return os.path.join(user_dir, self._name)

    def _load_task_layers(self, context):
        all_task_layers = self._asset_pipe.all_task_layers
        local_tls = []
        for task_layer_bool in all_task_layers:
            if task_layer_bool.is_local:
                local_tls.append(task_layer_bool.name)

        if not any(task_layer_bool.is_local
                   for task_layer_bool in all_task_layers):
            self.report(
                {'ERROR'},
                "Please select at least one task layer to be local to the current file",
            )
            return {'CANCELLED'}
        return local_tls

    def _create_publish_directories(self, context, asset_directory):
        for publish_type in constants.PUBLISH_KEYS:
            new_dir_path = os.path.join(asset_directory, publish_type)
            if os.path.exists(new_dir_path):
                self.report(
                    {'ERROR'},
                    f"Directory for '{publish_type}' already exists",
                )
                return {'CANCELLED'}
            os.mkdir(new_dir_path)

    def _asset_collection_get(self, context, local_tls):
        if self._asset_pipe.new_file_mode == "KEEP":
            asset_col = self._asset_pipe.asset_collection
            for col in asset_col.children:
                col.asset_id_owner = local_tls[0]
        else:
            bpy.data.collections.new(self._name)
            asset_col = bpy.data.collections.get(self._name)
            if asset_col not in list(asset_col.children):
                context.scene.collection.children.link(asset_col)
            self._asset_pipe.asset_collection = asset_col
        return asset_col

    def _remove_collections(self, context):
        # Remove Data From task layer Files except for asset_collection
        for col in bpy.data.collections:
            if not col == self._asset_pipe.asset_collection:
                bpy.data.collections.remove(col)
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)

        bpy.ops.outliner.orphans_purge(do_local_ids=True,
                                       do_linked_ids=False,
                                       do_recursive=True)

    def _task_layer_collections_set(self, context, asset_col, local_tls):
        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key not in local_tls:
                continue
            col_name = (
                f"{self._name}{constants.NAME_DELIMITER}{task_layer_key}"
            ).lower()
            bpy.data.collections.new(col_name)
            task_layer_col = bpy.data.collections.get(col_name)
            task_layer_col.asset_id_owner = task_layer_key
            if task_layer_col not in list(asset_col.children):
                asset_col.children.link(task_layer_col)

    def _first_file_create(self, context, local_tls, asset_directory) -> str:
        self._asset_pipe.is_asset_pipeline_file = True

        asset_col = self._asset_collection_get(context, local_tls)
        self._task_layer_collections_set(context, asset_col, local_tls)

        if bpy.data.filepath != "":
            first_file_name = Path(bpy.data.filepath).name
        else:
            first_file_name = (self._name + constants.FILE_DELIMITER +
                               local_tls[0].lower().replace(" ", "_") +
                               ".blend")

        first_file = os.path.join(asset_directory, first_file_name)

        self._asset_pipe.set_local_task_layers(local_tls)

        bpy.ops.wm.save_as_mainfile(filepath=first_file, copy=True)
        return first_file

    def _task_layer_file_create(self, context, task_layer_key,
                                asset_directory):
        name = (self._name + constants.FILE_DELIMITER +
                task_layer_key.lower().replace(" ", "_") + ".blend")
        self._asset_pipe.set_local_task_layers([task_layer_key])
        self._task_layer_collections_set(context,
                                         self._asset_pipe.asset_collection,
                                         [task_layer_key])

        task_layer_file = os.path.join(asset_directory, name)
        bpy.ops.wm.save_as_mainfile(filepath=task_layer_file, copy=True)

    def execute(self, context: Context):
        self._asset_name_set(context)
        asset_directory = self._asset_dir_get(context)
        local_tls = self._load_task_layers(context)

        if not os.path.exists(asset_directory):
            os.mkdir(asset_directory)

        self._create_publish_directories(context, asset_directory)

        # Save Task Layer Config File
        config.write_json_file(
            asset_path=Path(asset_directory),
            source_file_path=Path(self._asset_pipe.task_layer_config_type),
        )

        if self._asset_pipe.new_file_mode == "BLANK":
            self._remove_collections(context)

        starting_file = self._first_file_create(context, local_tls,
                                                asset_directory)

        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key == "NONE" or task_layer_key in local_tls:
                continue
            self._remove_collections(context)
            self._task_layer_file_create(context, task_layer_key,
                                         asset_directory)

        # Create intial publish based on task layers.
        self._remove_collections(context)
        publish.create_next_published_file(Path(starting_file),
                                           self.publish_type)
        if starting_file:
            bpy.ops.wm.open_mainfile(filepath=starting_file)
        return {'FINISHED'}


registry = [
    ASSETPIPE_OT_create_new_asset,
]
