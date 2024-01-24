from typing import Set
import bpy
import os
from pathlib import Path

from . import constants, config
from .hooks import Hooks, get_production_hook_dir, get_asset_hook_dir
from .prefs import get_addon_prefs
from .merge.naming import task_layer_prefix_transfer_data_update
from .merge.task_layer import draw_task_layer_selection, get_transfer_data_owner
from .merge.publish import (
    get_next_published_file,
    find_all_published,
    find_latest_publish,
    is_staged_publish,
    create_next_published_file,
)
from .images import save_images
from .sync import (
    sync_invoke,
    sync_draw,
    sync_execute_update_ownership,
    sync_execute_prepare_sync,
    sync_execute_pull,
    sync_execute_push,
)

from .asset_catalog import get_asset_cat_enum_items


class ASSETPIPE_OT_create_new_asset(bpy.types.Operator):
    bl_idname = "assetpipe.create_new_asset"
    bl_label = "Create New Asset"
    bl_description = """Create a new Asset Files and Folders at a given directory"""

    _name = ""
    _prefix = ""
    _json_path = None
    _asset_pipe = None

    create_files: bpy.props.BoolProperty(
        name="Create Files for Unselected Task Layers", default=True
    )

    # Only Active/Stage Publish Types are avaliable
    publish_type: bpy.props.EnumProperty(
        name="Publish Type",
        items=constants.PUBLISH_TYPES[:2],
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
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

    def invoke(self, context: bpy.types.Context, event):
        # Dynamically Create Task Layer Bools
        self._asset_pipe = context.scene.asset_pipeline

        config.verify_json_data(Path(self._asset_pipe.task_layer_config_type))

        all_task_layers = self._asset_pipe.all_task_layers
        all_task_layers.clear()

        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key == "NONE":
                continue
            new_task_layer = all_task_layers.add()
            new_task_layer.name = task_layer_key
        self.publish_type = constants.STAGED_PUBLISH_KEY
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        box = self.layout.box()
        all_task_layers = self._asset_pipe.all_task_layers

        box.label(text="Choose Which Task Layers will be local the current file")
        for task_layer_bool in all_task_layers:
            box.prop(task_layer_bool, "is_local", text=task_layer_bool.name)
        self.layout.prop(self, "create_files")
        self.layout.prop(self, "publish_type")

    def _asset_name_set(self, context) -> None:
        if self._asset_pipe.new_file_mode == "KEEP":
            asset_col = self._asset_pipe.asset_collection
            name = (
                asset_col.name
                if constants.NAME_DELIMITER not in asset_col.name
                else asset_col.name.split(constants.NAME_DELIMITER, 1)[1]
            )
            prefix = (
                ""
                if constants.NAME_DELIMITER not in asset_col.name
                else asset_col.name.split(constants.NAME_DELIMITER, 1)[0]
            )

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

        if not any(task_layer_bool.is_local for task_layer_bool in all_task_layers):
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

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)

    def _task_layer_collections_set(self, context, asset_col, local_tls):
        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key not in local_tls:
                continue
            col_name = (f"{self._name}{constants.NAME_DELIMITER}{task_layer_key}").lower()
            bpy.data.collections.new(col_name)
            task_layer_col = bpy.data.collections.get(col_name)
            task_layer_col.asset_id_owner = task_layer_key
            asset_col.children.link(task_layer_col)

    def _first_file_create(self, context, local_tls, asset_directory) -> str:
        self._asset_pipe.is_asset_pipeline_file = True

        asset_col = self._asset_collection_get(context, local_tls)
        self._task_layer_collections_set(context, asset_col, local_tls)

        if bpy.data.filepath != "":
            first_file_name = Path(bpy.data.filepath).name
        else:
            first_file_name = (
                self._name + constants.FILE_DELIMITER + local_tls[0].lower() + ".blend"
            )

        first_file = os.path.join(asset_directory, first_file_name)

        self._asset_pipe.set_local_task_layers(local_tls)

        bpy.ops.wm.save_as_mainfile(filepath=first_file, copy=True)
        return first_file

    def _task_layer_file_create(self, context, task_layer_key, asset_directory):
        name = self._name + constants.FILE_DELIMITER + task_layer_key.lower() + ".blend"
        self._asset_pipe.set_local_task_layers([task_layer_key])
        self._task_layer_collections_set(
            context, self._asset_pipe.asset_collection, [task_layer_key]
        )

        task_layer_file = os.path.join(asset_directory, name)
        bpy.ops.wm.save_as_mainfile(filepath=task_layer_file, copy=True)

    def execute(self, context: bpy.types.Context):
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

        starting_file = self._first_file_create(context, local_tls, asset_directory)

        for task_layer_key in config.TASK_LAYER_TYPES:
            if task_layer_key == "NONE" or task_layer_key in local_tls:
                continue
            self._remove_collections(context)
            self._task_layer_file_create(context, task_layer_key, asset_directory)

        # Create intial publish based on task layers.
        self._remove_collections(context)
        create_next_published_file(Path(starting_file), self.publish_type)
        if starting_file:
            bpy.ops.wm.open_mainfile(filepath=starting_file)
        return {'FINISHED'}


class ASSETPIPE_OT_update_ownership(bpy.types.Operator):
    bl_idname = "assetpipe.update_ownership"
    bl_label = "Update Ownership"
    bl_description = """Update the Ownership of Objects and Transferable Data"""

    _temp_transfer_data = None
    _invalid_objs = []
    _other_ids = []

    expand: bpy.props.BoolProperty(
        name="Show New Transferable Data",
        default=False,
        description="Show New Transferable Data",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        sync_draw(self, context)

    def execute(self, context: bpy.types.Context):
        sync_execute_update_ownership(self, context)
        return {'FINISHED'}


class ASSETPIPE_OT_sync_pull(bpy.types.Operator):
    bl_idname = "assetpipe.sync_pull"
    bl_label = "Pull Asset"
    bl_description = """Pull Task Layers from the published sync target"""

    _temp_transfer_data = None
    _invalid_objs = []
    _other_ids = []
    _temp_dir: Path = None
    _current_file: Path = None
    _task_layer_key: str = ""
    _sync_target: Path = None

    expand: bpy.props.BoolProperty(
        name="Show New Transferable Data",
        default=False,
        description="Show New Transferable Data",
    )
    save: bpy.props.BoolProperty(
        name="Save File & Images",
        default=True,
        description="Save Current File and Images before Push",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode == 'OBJECT':
            return True
        cls.poll_message_set("Pull is only avaliable in Object Mode")
        return False

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        self.layout.prop(self, "save")
        sync_draw(self, context)

    def execute(self, context: bpy.types.Context):
        asset_col = context.scene.asset_pipeline.asset_collection
        if self.save:
            save_images()
            bpy.ops.wm.save_mainfile()

        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        hooks_instance.execute_hooks(merge_mode="pull", merge_status='pre', asset_col=asset_col)
        # Find current task Layer
        sync_execute_update_ownership(self, context)
        sync_execute_prepare_sync(self, context)
        sync_execute_pull(self, context)

        hooks_instance.execute_hooks(merge_mode="pull", merge_status='post', asset_col=asset_col)
        return {'FINISHED'}


class ASSETPIPE_OT_sync_push(bpy.types.Operator):
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

    expand: bpy.props.BoolProperty(
        name="Show New Transferable Data",
        default=False,
        description="Show New Transferable Data",
    )
    pull: bpy.props.BoolProperty(
        name="Pull before Pushing",
        default=True,
        description="Pull in any new data from the Published file before Pushing",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode == 'OBJECT':
            return True
        cls.poll_message_set("Push is only avaliable in Object Mode")
        return False

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        sync_invoke(self, context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        if not self.pull:
            col = self.layout.column()
            col.label(text="Force Pushing without pulling can cause data loss", icon="ERROR")
            col.separator()
        sync_draw(self, context)

    def execute(self, context: bpy.types.Context):
        asset_col = context.scene.asset_pipeline.asset_collection
        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        hooks_instance.execute_hooks(merge_mode="push", merge_status='pre', asset_col=asset_col)
        save_images()
        bpy.ops.wm.save_mainfile()

        # Find current task Layer
        sync_execute_update_ownership(self, context)
        sync_execute_prepare_sync(self, context)

        if self.pull:
            hooks_instance.execute_hooks(merge_mode="pull", merge_status='pre', asset_col=asset_col)
            sync_execute_pull(self, context)
            hooks_instance.execute_hooks(
                merge_mode="pull", merge_status='post', asset_col=asset_col
            )
        bpy.ops.wm.save_mainfile(filepath=self._current_file.__str__())

        sync_execute_push(self, context)
        asset_col = context.scene.asset_pipeline.asset_collection
        hooks_instance.execute_hooks(merge_mode="push", merge_status='post', asset_col=asset_col)
        return {'FINISHED'}


class ASSETPIPE_OT_publish_new_version(bpy.types.Operator):
    bl_idname = "assetpipe.publish_new_version"
    bl_label = "Publish New Version"
    bl_description = """Create a new Published Version in the Publish Area"""

    publish_types: bpy.props.EnumProperty(
        name="Type",
        items=constants.PUBLISH_TYPES,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if bpy.data.is_dirty:
            cls.poll_message_set(
                "Save the current file and/or Pull from last publish before creating new Publish"
            )
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, "publish_types")

    def execute(self, context: bpy.types.Context):
        if (
            is_staged_publish(Path(bpy.data.filepath))
            and self.publish_types != constants.REVIEW_PUBLISH_KEY
        ):
            self.report(
                {'ERROR'},
                f"Only '{constants.REVIEW_PUBLISH_KEY}' Publish is supported when a version is staged",
            )
            return {'CANCELLED'}
        catalog_id = context.scene.asset_pipeline.asset_catalog_id
        create_next_published_file(
            current_file=Path(bpy.data.filepath),
            publish_type=self.publish_types,
            catalog_id=catalog_id,
        )
        return {'FINISHED'}


class ASSETPIPE_OT_publish_staged_as_active(bpy.types.Operator):
    bl_idname = "assetpipe.publish_staged_as_active"
    bl_label = "Publish Staged to Active"
    bl_description = """Create a new Published Version in the Publish Area"""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if bpy.data.is_dirty:
            cls.poll_message_set(
                "Save the current file and/or Pull from last publish before creating new Publish"
            )
            return False
        if not is_staged_publish(Path(bpy.data.filepath)):
            cls.poll_message_set.report("No File is currently staged")
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.alert = True
        layout.label(
            text="Delete the current staged file and replace with an active publish.",
            icon="ERROR",
        )

    def execute(self, context: bpy.types.Context):
        current_file = Path(bpy.data.filepath)
        staged_file = find_latest_publish(current_file, publish_type=constants.STAGED_PUBLISH_KEY)
        # Delete Staged File
        staged_file.unlink()
        catalog_id = context.scene.asset_pipeline.asset_catalog_id
        create_next_published_file(current_file=current_file, catalog_id=catalog_id)
        return {'FINISHED'}


class ASSETPIPE_OT_reset_ownership(bpy.types.Operator):
    bl_idname = "assetpipe.reset_ownership"
    bl_label = "Reset Ownership"
    bl_description = """Reset the Object owner and Transferable Data on selected object(s)"""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if len(context.selected_objects) == 0:
            cls.poll_message_set("No Objects Selected")
            return False
        return True

    def execute(self, context: bpy.types.Context):
        objs = context.selected_objects
        for obj in objs:
            obj.asset_id_owner = "NONE"
            obj.transfer_data_ownership.clear()
            self.report(
                {'INFO'},
                f"'{obj.name}' ownership data cleared ",
            )
        return {'FINISHED'}


class ASSETPIPE_OT_update_local_task_layers(bpy.types.Operator):
    bl_idname = "assetpipe.update_local_task_layers"
    bl_label = "Update Local Task Layers"
    bl_description = """Change the Task Layers that are Local to your file"""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_pipe = context.scene.asset_pipeline
        new_local_tl = [tl.name for tl in asset_pipe.all_task_layers if tl.is_local == True]
        local_tl = [tl.name for tl in asset_pipe.local_task_layers]
        if new_local_tl == local_tl:
            cls.poll_message_set("Local Task Layers already match current selection")
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.alert = True
        layout.label(
            text="Caution, this only affects current file.",
            icon="ERROR",
        )
        layout.label(text="Two files owning the same task layer can break merge process.")

    def execute(self, context: bpy.types.Context):
        asset_pipe = context.scene.asset_pipeline
        all_task_layers = asset_pipe.all_task_layers
        local_tl = [tl.name for tl in all_task_layers if tl.is_local == True]
        asset_pipe.set_local_task_layers(local_tl)
        return {'FINISHED'}


class ASSETPIPE_OT_revert_file(bpy.types.Operator):
    bl_idname = "assetpipe.revert_file"
    bl_label = "Revert File"
    bl_description = """Revert File to Pre-Sync State. Revert will not affect Published files"""

    _temp_file = ""
    _source_file = ""

    def execute(self, context: bpy.types.Context):
        asset_pipe = context.scene.asset_pipeline
        self._temp_file = asset_pipe.temp_file
        self._source_file = asset_pipe.source_file

        if not Path(self._temp_file).exists():
            self.report(
                {'ERROR'},
                "Revert failed; no file found",
            )
            return {'CANCELLED'}

        bpy.ops.wm.open_mainfile(filepath=self._temp_file)
        bpy.ops.wm.save_as_mainfile(filepath=self._source_file)
        return {'FINISHED'}


class ASSETPIPE_OT_fix_prefixes(bpy.types.Operator):
    bl_idname = "assetpipe.fix_prefixes"
    bl_label = "Fix Prefixes"
    bl_description = """Fix Prefixes for Modifiers and Constraints so they match Transferable Data Owner on selected object(s)"""

    _updated_prefix = False

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if len(context.selected_objects) == 0:
            cls.poll_message_set("No Objects Selected")
            return False
        return True

    def execute(self, context: bpy.types.Context):
        objs = context.selected_objects
        for obj in objs:
            transfer_data_items = obj.transfer_data_ownership
            for transfer_data_item in transfer_data_items:
                if task_layer_prefix_transfer_data_update(transfer_data_item):
                    self.report(
                        {'INFO'},
                        f"Renamed {transfer_data_item.type} on '{obj.name}'",
                    )
                    self._updated_prefix = True

        if not self._updated_prefix:
            self.report(
                {'WARNING'},
                f"No Prefixes found to update",
            )

        return {'FINISHED'}


class ASSETPIPE_OT_update_surrendered_object(bpy.types.Operator):
    bl_idname = "assetpipe.update_surrendered_object"
    bl_label = "Claim Surrendered"
    bl_description = """Claim Surrended Object Owner"""

    _obj = None
    _old_onwer = ""

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self._obj = context.active_object
        self._old_onwer = self._obj.asset_id_owner
        # Set Asset ID Owner to a local ID
        self._obj.asset_id_owner = context.scene.asset_pipeline.get_local_task_layers()[0]
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()

        draw_task_layer_selection(
            layout=row,
            data=self._obj,
            show_all_task_layers=False,
            show_local_task_layers=True,
        )

    def execute(self, context: bpy.types.Context):
        if self._obj.asset_id_owner == self._old_onwer:
            self.report(
                {'ERROR'},
                f"Object Owner was not updated",
            )
            return {'CANCELLED'}
        self._obj.asset_id_surrender = False
        return {'FINISHED'}


class ASSETPIPE_OT_update_surrendered_transfer_data(bpy.types.Operator):
    bl_idname = "assetpipe.update_surrendered_transfer_data"
    bl_label = "Claim Surrendered"
    bl_description = """Claim Surrended Transferable Data Owner"""

    transfer_data_item_name: bpy.props.StringProperty(name="Transferable Data Item Name")

    _surrendered_transfer_data = None
    _old_onwer = ""

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        obj = context.active_object
        for transfer_data_item in obj.transfer_data_ownership:
            if transfer_data_item.name == self.transfer_data_item_name:
                self._surrendered_transfer_data = transfer_data_item
                self._old_onwer = self._surrendered_transfer_data.owner
        # Set Default Owner
        asset_pipe = context.scene.asset_pipeline
        owner, _ = get_transfer_data_owner(
            asset_pipe, self._surrendered_transfer_data.type, self._surrendered_transfer_data.name
        )
        self._surrendered_transfer_data.owner = owner
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row()

        draw_task_layer_selection(
            layout=row,
            data=self._surrendered_transfer_data,
            show_local_task_layers=True,
        )

    def execute(self, context: bpy.types.Context):
        if self._surrendered_transfer_data.owner == self._old_onwer:
            self.report(
                {'ERROR'},
                f"Transferable Data Owner was not updated",
            )
            return {'CANCELLED'}
        self._surrendered_transfer_data.surrender = False
        task_layer_prefix_transfer_data_update(self._surrendered_transfer_data)
        return {'FINISHED'}


class ASSETPIPE_OT_batch_ownership_change(bpy.types.Operator):
    # TODO Update Operator Documentation
    bl_idname = "assetpipe.batch_ownership_change"
    bl_label = "Batch Set Ownership"
    bl_description = """Re-Assign Ownership in a batch operation"""

    name_filter: bpy.props.StringProperty(
        name="Filter by Name",
        description="Filter Object or Transferable Data items by name",
        default="",
    )

    data_source: bpy.props.EnumProperty(
        name="Objects",
        items=(
            ('SELECT', "Selected", "Update Selected Objects Only"),
            ('ALL', "All", "Update All Objects"),
        ),
    )

    data_type: bpy.props.EnumProperty(
        name="Ownership Type",
        items=(
            (
                'OBJECT',
                "Object",
                "Update Owner of Objects",
            ),
            (
                'TRANSFER_DATA',
                "Transferable Data",
                "Update Owner of Transferable Data within Objects",
            ),
        ),
    )

    filter_owners: bpy.props.EnumProperty(
        name="Owner Filter",
        items=(
            ('LOCAL', "If Locally Owned", "Only data that is owned locally"),
            ('OWNED', "If Owned By Any", "Only data that already have assignment"),
            ('ALL', "No Filter", "Set Ownership on any data, even without an owner"),
        ),
    )

    avaliable_owners: bpy.props.EnumProperty(
        name="Avaliable Owners",
        items=(
            ('LOCAL', "Local Task Layers", "Only show local task layers as options"),
            (
                'ALL',
                "All Task Layers",
                "Show all task layers as options",
            ),
        ),
    )
    transfer_data_type: bpy.props.EnumProperty(
        name="Type Filter", items=constants.TRANSFER_DATA_TYPES_ENUM_ITEMS
    )
    owner_selection: bpy.props.StringProperty(name="Set Owner")

    def update_set_surrender(self, context):
        if self.set_surrender:
            self.claim_surrender = False

    set_surrender: bpy.props.BoolProperty(
        name="Set Surrender", default=False, update=update_set_surrender
    )

    def update_claim_surrender(self, context):
        if self.claim_surrender:
            self.set_surrender = False

    claim_surrender: bpy.props.BoolProperty(
        name="Claim Surrender", default=False, update=update_claim_surrender
    )

    def _filter_by_name(self, context, unfiltered_list: []):
        if self.name_filter == "":
            return unfiltered_list
        return [item for item in unfiltered_list if self.name_filter in item.name]

    def _get_transfer_data_to_update(self, context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        transfer_data_items_to_update = []
        if self.data_type == "TRANSFER_DATA":
            for obj in objs:
                filtered_transfer_data = self._filter_by_name(context, obj.transfer_data_ownership)
                for transfer_data_item in filtered_transfer_data:
                    if self.transfer_data_type != "NONE":
                        if transfer_data_item.type == self.transfer_data_type:
                            transfer_data_items_to_update.append(transfer_data_item)
                    else:
                        transfer_data_items_to_update.append(transfer_data_item)

        if self.claim_surrender:
            return [
                item
                for item in transfer_data_items_to_update
                if item.surrender and item.owner not in asset_pipe.get_local_task_layers()
            ]

        if self.filter_owners == "LOCAL":
            transfer_data_items_to_update = [
                item
                for item in transfer_data_items_to_update
                if item.owner in asset_pipe.get_local_task_layers()
            ]
        if self.set_surrender:
            return [item for item in transfer_data_items_to_update if not item.surrender]

        return transfer_data_items_to_update

    def _get_objects(self, context):
        asset_objs = context.scene.asset_pipeline.asset_collection.all_objects
        selected_asset_objs = [obj for obj in asset_objs if obj in context.selected_objects]
        return asset_objs if self.data_source == "ALL" else selected_asset_objs

    def _get_filtered_objects(self, context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        filtered_objs = self._filter_by_name(context, objs)
        if self.filter_owners == "LOCAL" and self.data_type == "OBJECT":
            filtered_objs = [
                item
                for item in filtered_objs
                if item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        if self.filter_owners == "OWNED" and self.data_type == "OBJECT":
            filtered_objs = [item for item in filtered_objs if item.asset_id_owner != "NONE"]

        if self.claim_surrender:
            claim_objs = self._get_objects(context)
            claim_filtered_objs = self._filter_by_name(context, claim_objs)
            return [
                item
                for item in claim_filtered_objs
                if item.asset_id_surrender
                and item.asset_id_owner not in asset_pipe.get_local_task_layers()
            ]

        if self.set_surrender:
            return [
                item
                for item in filtered_objs
                if not item.asset_id_surrender
                and item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        return filtered_objs

    def _get_message(self, context) -> str:
        objs = self._get_filtered_objects(context)
        if self.data_type == "OBJECT":
            data_type_name = "Object(s)"
            length = len(objs) if objs else 0
        else:
            transfer_data_items_to_update = self._get_transfer_data_to_update(context)
            data_type_name = "Transferable Data Item(s)"

            length = len(transfer_data_items_to_update) if transfer_data_items_to_update else 0
        if self.claim_surrender:
            action = "Claim Surrendered on"
        if self.set_surrender:
            action = "Set Surrender on"
        if not (self.claim_surrender or self.set_surrender):
            action = "Change Ownership on"
        return f"{action} {length} {data_type_name}"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if not get_addon_prefs().is_advanced_mode:
            self.filter_owners = 'LOCAL'
            self.avaliable_owners = 'LOCAL'
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context):
        prefs = get_addon_prefs()
        advanced_mode = prefs.is_advanced_mode
        grey_out = True

        if self.set_surrender:
            grey_out = False
            self.filter_owners = "LOCAL"

        layout = self.layout
        layout.use_property_split = True
        layout.row(align=True).prop(self, "data_source", expand=True)

        layout.prop(self, "data_type", expand=True)
        filter_owner_row = layout.row()
        filter_owner_row.enabled = grey_out
        if advanced_mode:
            filter_owner_row.prop(self, "filter_owners")

        if self.data_type == "TRANSFER_DATA":
            layout.prop(self, "transfer_data_type")
        layout.prop(self, "name_filter", text="Name Filter")

        if self.avaliable_owners == "LOCAL":
            show_local = True
            show_all_task_layers = False
        else:
            show_local = False
            show_all_task_layers = True

        layout.separator()

        owner_row = layout.row(align=True)
        owner_row.enabled = grey_out

        draw_task_layer_selection(
            layout=owner_row,
            data=self,
            data_owner_name='owner_selection',
            current_data_owner=self.owner_selection,
            show_all_task_layers=show_all_task_layers,
            show_local_task_layers=show_local,
            text="Set To",
        )

        if advanced_mode:
            owner_row.prop(self, "avaliable_owners", text="")

        row = layout.row(align=True)
        row.prop(self, 'set_surrender', toggle=True)
        row.prop(self, 'claim_surrender', toggle=True)

        bottom_label = layout.row()
        bottom_label_split = bottom_label.split(factor=0.4)
        bottom_label_split.row()
        bottom_label_split.label(text=self._get_message(context))

    def execute(self, context: bpy.types.Context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_filtered_objects(context)
        message = self._get_message(context)

        # Only check for owner selection not surrendering data.
        if not self.set_surrender:
            if self.owner_selection == "":
                self.report(
                    {'ERROR'},
                    "Ownership 'Set To' must be set to a task layer",
                )
                return {'CANCELLED'}

        if self.data_type == "OBJECT":
            for obj in objs:
                if self.claim_surrender:
                    obj.asset_id_surrender = False
                if self.set_surrender:
                    obj.asset_id_surrender = True
                    continue
                obj.asset_id_owner = self.owner_selection
        else:
            transfer_data_items_to_update = self._get_transfer_data_to_update(context)

            for transfer_data_item_to_update in transfer_data_items_to_update:
                if self.claim_surrender:
                    transfer_data_item_to_update.surrender = False
                if self.set_surrender:
                    transfer_data_item_to_update.surrender = True
                    continue

                transfer_data_item_to_update.owner = self.owner_selection
                task_layer_prefix_transfer_data_update(transfer_data_item_to_update)

        self.report({'INFO'}, message)
        return {'FINISHED'}


class ASSETPIPE_OT_refresh_asset_cat(bpy.types.Operator):
    bl_idname = "assetpipe.refresh_asset_cat"
    bl_label = "Refresh Asset Catalogs"
    bl_description = """Refresh Asset Catalogs"""

    def execute(self, context: bpy.types.Context):
        get_asset_cat_enum_items()
        self.report({'INFO'}, "Asset Catalogs Refreshed!")
        return {'FINISHED'}


class ASSETPIPE_OT_save_asset_hook(bpy.types.Operator):
    bl_idname = "assetpipe.save_production_hook"
    bl_label = "Save Production Hook"
    bl_description = """Save new hook file based on example file. Production hooks are used across all assets. Asset hooks are only used in the current asset.
    - Production hooks: 'assets/scripts' directory.
    - Asset hooks are stored at the root of the asset's directory'"""
    mode: bpy.props.EnumProperty(
        name="Hooks Mode",
        description="Choose to either save production level or asset level hooks",
        items=[
            ('PROD', 'Production', 'Save Prododuction Level Hooks'),
            ('ASSET', 'Asset', 'Save Asset Level Hooks'),
        ],
    )

    def execute(self, context: bpy.types.Context):
        if self.mode == 'PROD':
            example_hooks_dir = (
                Path(__file__).parent.joinpath("hook_examples").joinpath('prod_hooks.py')
            )
            save_hook_path = get_production_hook_dir().joinpath('hooks.py').resolve()
        else:  # if self.mode == 'ASSET'
            example_hooks_dir = (
                Path(__file__).parent.joinpath("hook_examples").joinpath('asset_hooks.py')
            )
            save_hook_path = get_asset_hook_dir().joinpath('hooks.py').resolve()

        if not example_hooks_dir.exists():
            self.report(
                {'ERROR'},
                "Cannot find example hook file",
            )
            return {'CANCELLED'}

        if save_hook_path.exists():
            self.report(
                {'ERROR'},
                f"Cannot overwrite existing hook file at  '{save_hook_path.__str__()}'",
            )
            return {'CANCELLED'}

        with example_hooks_dir.open() as source:
            contents = source.read()

        # Write contents to target file
        with save_hook_path.open('w') as target:
            target.write(contents)
        self.report({'INFO'}, f"Hook File saved to {save_hook_path.__str__()}")
        return {'FINISHED'}


classes = (
    ASSETPIPE_OT_update_ownership,
    ASSETPIPE_OT_sync_push,
    ASSETPIPE_OT_sync_pull,
    ASSETPIPE_OT_publish_new_version,
    ASSETPIPE_OT_publish_staged_as_active,
    ASSETPIPE_OT_create_new_asset,
    ASSETPIPE_OT_reset_ownership,
    ASSETPIPE_OT_update_local_task_layers,
    ASSETPIPE_OT_revert_file,
    ASSETPIPE_OT_fix_prefixes,
    ASSETPIPE_OT_update_surrendered_object,
    ASSETPIPE_OT_update_surrendered_transfer_data,
    ASSETPIPE_OT_batch_ownership_change,
    ASSETPIPE_OT_refresh_asset_cat,
    ASSETPIPE_OT_save_asset_hook,
)


def register():
    for i in classes:
        bpy.utils.register_class(i)


def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
