import bpy
import os
from typing import List
from . import constants
from . import config
from pathlib import Path
from .prefs import get_addon_prefs
from .asset_catalog import get_asset_catalog_items, get_asset_name, get_asset_id
import json

""" NOTE Items in these properties groups should be generated by a function that finds the 
avaliable task layers from the task_layer.json file that needs to be created.
"""


def get_safely_string_prop(self, name: str) -> str:
    """Return Value of String Property, and return "" if value isn't set"""
    try:
        return self[name]
    except KeyError:
        return ""


def get_task_layer_presets(self, context):
    prefs = get_addon_prefs()
    user_tls = Path(prefs.custom_task_layers_dir)

    presets_dir = config.get_task_layer_presets_path()
    items = []

    for file in presets_dir.glob('*.json'):
        items.append((file.__str__(), file.name.replace(".json", ""), file.name))
    if user_tls.exists() and user_tls.is_dir():
        for file in user_tls.glob('*.json'):
            items.append((file.__str__(), file.name.replace(".json", ""), file.name))
    return items


class AssetTransferData(bpy.types.PropertyGroup):
    """Properties to track transferable data on an object"""

    owner: bpy.props.StringProperty(name="Owner", default="NONE")
    type: bpy.props.EnumProperty(
        name="Transferable Data Type",
        items=constants.TRANSFER_DATA_TYPES_ENUM_ITEMS,
    )
    surrender: bpy.props.BoolProperty(name="Surrender Ownership", default=False)


class AssetTransferDataTemp(bpy.types.PropertyGroup):
    """Class used when finding new ownership data so it can be drawn
    with the same method as the existing ownership data from ASSET_TRANSFER_DATA"""

    owner: bpy.props.StringProperty(name="OwneAr", default="NONE")
    type: bpy.props.EnumProperty(
        name="Transferable Data Type",
        items=constants.TRANSFER_DATA_TYPES_ENUM_ITEMS,
    )
    surrender: bpy.props.BoolProperty(name="Surrender Ownership", default=False)
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class TaskLayerSettings(bpy.types.PropertyGroup):
    is_local: bpy.props.BoolProperty(name="Task Layer is Local", default=False)


class AssetPipeline(bpy.types.PropertyGroup):
    """Properties to manage the status of asset pipeline files"""

    is_asset_pipeline_file: bpy.props.BoolProperty(
        name="Asset Pipeline File",
        description="Asset Pipeline Files are used in the asset pipeline, if file is not asset pipeline file user will be prompted to create a new asset",
        default=False,
    )
    is_depreciated: bpy.props.BoolProperty(
        name="Depreciated",
        description="Depreciated files do not recieve any updates when syncing from a task layer",
        default=False,
    )

    def get_is_published(self):
        return bool(Path(bpy.data.filepath).parent.name in constants.PUBLISH_KEYS)

    is_published: bpy.props.BoolProperty(
        name="Is Published",
        description="File is Published",
        get=lambda self: Path(bpy.data.filepath).parent.name in constants.PUBLISH_KEYS,
    )

    @property
    def asset_collection(self):
        return bpy.data.collections.get(self.asset_collection_name) or bpy.data.collections.get(
            self.asset_collection_name + "." + constants.LOCAL_SUFFIX
        )

    @asset_collection.setter
    def asset_collection(self, coll):
        self.asset_collection_name = coll.name

    asset_collection_name: bpy.props.StringProperty(
        name="Asset",
        default="",
        description="Top Level Collection of the Asset, all other collections of the asset will be children of this collection",
    )

    # Commented out - Let's use a weak ref for now because this causes the collection to evaluate even when hidden, causing performance nightmares
    # asset_collection: bpy.props.PointerProperty(
    #     type=bpy.types.Collection,
    #     name="Asset",
    #     description="Top Level Collection of the Asset, all other collections of the
    # asset will be children of this collection",
    # )

    temp_transfer_data: bpy.props.CollectionProperty(type=AssetTransferDataTemp)

    def add_temp_transfer_data(self, name, owner, type, obj, surrender):
        new_transfer_data = self.temp_transfer_data
        transfer_data_item = new_transfer_data.add()
        transfer_data_item.name = name
        transfer_data_item.owner = owner
        transfer_data_item.type = type
        transfer_data_item.obj = obj
        transfer_data_item.surrender = surrender

    ## NEW FILE

    new_file_mode: bpy.props.EnumProperty(
        name="New File Mode",
        items=(
            ('KEEP', "Current File", "Setup the Existing File/Directory as an Asset"),
            ('BLANK', "Blank File", "Create a New Blank Asset in a New Directory"),
        ),
    )

    dir: bpy.props.StringProperty(
        name="Directory",
        description="Target Path for new asset files",
        subtype="DIR_PATH",
    )
    name: bpy.props.StringProperty(name="Name", description="Name for new Asset")

    prefix: bpy.props.StringProperty(name="Prefix", description="Prefix for new Asset", default="")

    task_layer_config_type: bpy.props.EnumProperty(
        name="Task Layer Preset",
        items=get_task_layer_presets,
    )  # type: ignore

    temp_file: bpy.props.StringProperty(name="Pre-Sync Backup")
    source_file: bpy.props.StringProperty(name="File that started Sync")
    sync_error: bpy.props.BoolProperty(name="Sync Error", default=False)

    all_task_layers: bpy.props.CollectionProperty(type=TaskLayerSettings)
    local_task_layers: bpy.props.CollectionProperty(type=TaskLayerSettings)

    def set_local_task_layers(self, task_layer_keys: List[str]):
        # Update Local Task Layers for New File
        self.local_task_layers.clear()
        for task_layer in self.all_task_layers:
            if task_layer.name in task_layer_keys:
                new_local_task_layer = self.local_task_layers.add()
                new_local_task_layer.name = task_layer.name

    def get_local_task_layers(self):
        return [task_layer.name for task_layer in self.local_task_layers]

    # UI BOOLS: used to show/hide Transferable Data elements
    # The names are also hard coded in constants.py under TRANSFER_DATA_TYPES
    # any changes will need to be reflected both here and in that enum
    group_vertex_ui_bool: bpy.props.BoolProperty(name="Show/Hide Vertex Groups", default=False)
    modifier_ui_bool: bpy.props.BoolProperty(name="Show/Hide Modifiers", default=False)
    constraint_ui_bool: bpy.props.BoolProperty(name="Show/Hide Constraints", default=False)
    material_ui_bool: bpy.props.BoolProperty(name="Show/Hide Materials", default=False)
    shapekey_ui_bool: bpy.props.BoolProperty(name="Show/Hide Shape Keys", default=False)
    attribute_ui_bool: bpy.props.BoolProperty(name="Show/Hide Attributes", default=False)
    file_parent_ui_bool: bpy.props.BoolProperty(name="Show/Hide Parent", default=False)

    def set_asset_catalog_name(self, input):
        task_layer_dict = config.get_task_layer_dict()
        task_layer_dict["ASSET_CATALOG_ID"] = get_asset_id(input)
        config.update_task_layer_json_data(task_layer_dict)
        self['asset_catalog_name'] = input

    def get_asset_catalog_name(self):
        if config.ASSET_CATALOG_ID != "":
            asset_name = get_asset_name(config.ASSET_CATALOG_ID)
            if asset_name is None:
                return ""
            return asset_name
        return get_safely_string_prop(self, 'asset_catalog_name')

    def get_asset_catalogs_search(self, context, edit_text: str):
        return get_asset_catalog_items()

    asset_catalog_name: bpy.props.StringProperty(
        name="Catalog",
        get=get_asset_catalog_name,
        set=set_asset_catalog_name,
        search=get_asset_catalogs_search,
        search_options={'SORT'},
        description="Select Asset Library Catalog for the current Asset, this value will be updated each time you Push to an 'Active' Publish",
    )  # type: ignore

@bpy.app.handlers.persistent
def set_asset_collection_name_post_file_load(_):
    # Version the PointerProperty to the StringProperty, and the left-over pointer.
    for scene in bpy.data.scenes:
        if 'asset_collection' not in scene.asset_pipeline:
            continue
        coll = scene.asset_pipeline['asset_collection']
        if coll:
            scene.asset_pipeline.asset_collection_name = coll.name
            del scene.asset_pipeline['asset_collection']


@bpy.app.handlers.persistent
def refresh_asset_catalog(_):
    get_asset_catalog_items()
    config.verify_task_layer_json_data()


classes = (
    AssetTransferData,
    AssetTransferDataTemp,
    TaskLayerSettings,
    AssetPipeline,
)


def register():
    for i in classes:
        bpy.utils.register_class(i)
    bpy.types.Object.transfer_data_ownership = bpy.props.CollectionProperty(type=AssetTransferData)
    bpy.types.Scene.asset_pipeline = bpy.props.PointerProperty(type=AssetPipeline)
    bpy.types.ID.asset_id_owner = bpy.props.StringProperty(name="Owner", default="NONE")
    bpy.types.ID.asset_id_surrender = bpy.props.BoolProperty(
        name="Surrender Ownership", default=False
    )
    bpy.app.handlers.load_post.append(set_asset_collection_name_post_file_load)
    bpy.app.handlers.load_post.append(refresh_asset_catalog)


def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
    del bpy.types.Object.transfer_data_ownership
    del bpy.types.Scene.asset_pipeline
    del bpy.types.ID.asset_id_owner
    bpy.app.handlers.load_post.remove(set_asset_collection_name_post_file_load)
    bpy.app.handlers.load_post.remove(refresh_asset_catalog)
