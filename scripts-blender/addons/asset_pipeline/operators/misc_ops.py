# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..props import AssetTransferData

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Context, Event, Operator

from .. import constants
from ..asset_catalog import get_asset_catalog_items
from ..config import verify_task_layer_json_data
from ..hooks import get_asset_hook_dir, get_production_hook_dir
from ..merge import naming, task_layer
from ..prefs import get_addon_prefs


class ASSETPIPE_OT_reset_ownership(Operator):
    bl_idname = "assetpipe.reset_ownership"
    bl_label = "Reset Ownership"
    bl_description = """Reset the Object owner and Transferable Data on selected object(s)"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        if len(context.selected_objects) == 0:
            cls.poll_message_set("No Objects Selected")
            return False
        return True

    def execute(self, context: Context):
        objs = context.selected_objects
        for obj in objs:
            obj.asset_id_owner = "NONE"
            obj.transfer_data_ownership.clear()
            self.report(
                {'INFO'},
                f"'{obj.name}' ownership data cleared ",
            )
        return {'FINISHED'}


class ASSETPIPE_OT_update_local_task_layers(Operator):
    bl_idname = "assetpipe.update_local_task_layers"
    bl_label = "Update Local Task Layers"
    bl_description = """Change the Task Layers that are Local to your file"""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        asset_pipe = context.scene.asset_pipeline
        new_local_tl = [
            tl.name for tl in asset_pipe.all_task_layers if tl.is_local
        ]
        local_tl = [tl.name for tl in asset_pipe.local_task_layers]
        if new_local_tl == local_tl:
            cls.poll_message_set(
                "Local Task Layers already match current selection")
            return False
        return True

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        layout = self.layout
        layout.alert = True
        layout.label(
            text="Caution, this only affects current file.",
            icon="ERROR",
        )
        layout.label(
            text="Two files owning the same task layer can break merge process."
        )

    def execute(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        all_task_layers = asset_pipe.all_task_layers
        local_tl = [tl.name for tl in all_task_layers if tl.is_local]
        asset_pipe.set_local_task_layers(local_tl)
        return {'FINISHED'}


class ASSETPIPE_OT_revert_file(Operator):
    bl_idname = "assetpipe.revert_file"
    bl_label = "Revert File"
    bl_description = """Revert File to Pre-Sync State. Revert will not affect Published files"""

    _temp_file = ""
    _source_file = ""

    def execute(self, context: Context):
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


class ASSETPIPE_OT_fix_prefixes(Operator):
    bl_idname = "assetpipe.fix_prefixes"
    bl_label = "Fix Modifier Prefixes"
    bl_description = (
        """Fix Prefixes for Modifiers so they match Transferable Data Owner on selected object(s)"""
    )
    bl_options = {'REGISTER', 'UNDO'}

    _updated_prefix = False

    @classmethod
    def poll(cls, context: Context) -> bool:
        if len(context.selected_objects) == 0:
            cls.poll_message_set("No Objects Selected")
            return False
        return True

    def execute(self, context: Context):
        objs = context.selected_objects
        asset_pipe = context.scene.asset_pipeline
        for obj in objs:
            transfer_data_items = obj.transfer_data_ownership
            for transfer_data_item in transfer_data_items:
                if transfer_data_item.type != 'MODIFIER':
                    continue
                modifier = obj.modifiers.get(transfer_data_item.name)
                if not modifier:
                    continue
                owner = task_layer.get_transfer_data_owner(
                    asset_pipe, transfer_data_item.type)
                if not owner:
                    continue
                prefixed = naming.task_layer_prefix_name_get(
                    modifier.name, owner[0])
                if prefixed == modifier.name:
                    continue
                transfer_data_item.name = modifier.name = prefixed
                self.report(
                    {'INFO'},
                    f"Renamed {transfer_data_item.name} on '{obj.name}'",
                )
                self._updated_prefix = True

        if not self._updated_prefix:
            self.report({'WARNING'}, "No Prefixes found to update")

        return {'FINISHED'}


class ASSETPIPE_OT_batch_ownership_change(Operator):
    # TODO Update Operator Documentation
    bl_idname = "assetpipe.batch_ownership_change"
    bl_label = "Batch Set Ownership"
    bl_description = """Re-Assign Ownership in a batch operation"""
    bl_options = {'REGISTER', 'UNDO'}

    name_filter: StringProperty(
        name="Filter by Name",
        description="Filter Object or Transferable Data items by name",
        default="",
    )

    data_source: EnumProperty(
        name="Objects",
        items=(
            ('SELECT', "Selected", "Update Selected Objects Only"),
            ('ALL', "All", "Update All Objects"),
        ),
    )

    data_type: EnumProperty(
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

    filter_owners: EnumProperty(
        name="Owner Filter",
        items=(
            ('LOCAL', "If Locally Owned", "Only data that is owned locally"),
            ('OWNED', "If Owned By Any",
             "Only data that already have assignment"),
            ('ALL', "No Filter",
             "Set Ownership on any data, even without an owner"),
        ),
    )

    avaliable_owners: EnumProperty(
        name="Avaliable Owners",
        items=(
            ('LOCAL', "Local Task Layers",
             "Only show local task layers as options"),
            (
                'ALL',
                "All Task Layers",
                "Show all task layers as options",
            ),
        ),
    )
    transfer_data_type: EnumProperty(
        name="Type Filter", items=constants.TRANSFER_DATA_TYPES_ENUM_ITEMS)
    owner_selection: StringProperty(name="Set Owner")

    def update_set_surrender(self, context):
        if self.set_surrender:
            self.claim_surrender = False

    set_surrender: BoolProperty(name="Set Surrender",
                                default=False,
                                update=update_set_surrender)

    def update_claim_surrender(self, context):
        if self.claim_surrender:
            self.set_surrender = False

    claim_surrender: BoolProperty(name="Claim Surrender",
                                  default=False,
                                  update=update_claim_surrender)

    def _filter_by_name(self,
                        context,
                        unfiltered_list: list[AssetTransferData] = []):
        if self.name_filter == "":
            return unfiltered_list
        return [
            item for item in unfiltered_list if self.name_filter in item.name
        ]

    def _get_transfer_data_to_update(self, context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        transfer_data_items_to_update = []
        if self.data_type == "TRANSFER_DATA":
            for obj in objs:
                filtered_transfer_data = self._filter_by_name(
                    context, obj.transfer_data_ownership)
                for transfer_data_item in filtered_transfer_data:
                    if self.transfer_data_type != "NONE":
                        if transfer_data_item.type == self.transfer_data_type:
                            transfer_data_items_to_update.append(
                                transfer_data_item)
                    else:
                        transfer_data_items_to_update.append(
                            transfer_data_item)

        if self.claim_surrender:
            return [
                item for item in transfer_data_items_to_update
                if item.surrender
                and item.owner not in asset_pipe.get_local_task_layers()
            ]

        if self.filter_owners == "LOCAL":
            transfer_data_items_to_update = [
                item for item in transfer_data_items_to_update
                if item.owner in asset_pipe.get_local_task_layers()
            ]
        if self.set_surrender:
            return [
                item for item in transfer_data_items_to_update
                if not item.surrender
            ]

        return transfer_data_items_to_update

    def _get_objects(self, context):
        asset_objs = context.scene.asset_pipeline.asset_collection.all_objects
        selected_asset_objs = [
            obj for obj in asset_objs if obj in context.selected_objects
        ]
        return asset_objs if self.data_source == "ALL" else selected_asset_objs

    def _get_filtered_objects(self, context):
        asset_pipe = context.scene.asset_pipeline
        objs = self._get_objects(context)
        filtered_objs = self._filter_by_name(context, objs)
        if self.filter_owners == "LOCAL" and self.data_type == "OBJECT":
            filtered_objs = [
                item for item in filtered_objs
                if item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        if self.filter_owners == "OWNED" and self.data_type == "OBJECT":
            filtered_objs = [
                item for item in filtered_objs if item.asset_id_owner != "NONE"
            ]

        if self.claim_surrender:
            claim_objs = self._get_objects(context)
            claim_filtered_objs = self._filter_by_name(context, claim_objs)
            return [
                item for item in claim_filtered_objs
                if item.asset_id_surrender and item.asset_id_owner not in
                asset_pipe.get_local_task_layers()
            ]

        if self.set_surrender:
            return [
                item for item in filtered_objs if not item.asset_id_surrender
                and item.asset_id_owner in asset_pipe.get_local_task_layers()
            ]
        return filtered_objs

    def _get_message(self, context) -> str:
        objs = self._get_filtered_objects(context)
        if self.data_type == "OBJECT":
            data_type_name = "Object(s)"
            length = len(objs) if objs else 0
        else:
            transfer_data_items_to_update = self._get_transfer_data_to_update(
                context)
            data_type_name = "Transferable Data Item(s)"

            length = len(transfer_data_items_to_update
                         ) if transfer_data_items_to_update else 0
        if self.claim_surrender:
            action = "Claim Surrendered on"
        if self.set_surrender:
            action = "Set Surrender on"
        if not (self.claim_surrender or self.set_surrender):
            action = "Change Ownership on"
        return f"{action} {length} {data_type_name}"

    def invoke(self, context: Context, event: Event):
        if not get_addon_prefs().is_advanced_mode:
            self.filter_owners = 'LOCAL'
            self.avaliable_owners = 'LOCAL'
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: Context):
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
        layout.separator()

        owner_row = layout.row(align=True)
        owner_row.enabled = grey_out

        task_layer.draw_task_layer_selection(
            context,
            layout=owner_row,
            data=self,
            data_owner_name='owner_selection',
            current_data_owner=self.owner_selection,
            show_all_task_layers=self.avaliable_owners == 'ALL',
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

    def execute(self, context: Context):
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
            transfer_data_items_to_update = self._get_transfer_data_to_update(
                context)

            for transfer_data_item_to_update in transfer_data_items_to_update:
                if self.claim_surrender:
                    transfer_data_item_to_update.surrender = False
                if self.set_surrender:
                    transfer_data_item_to_update.surrender = True
                    continue

                transfer_data_item_to_update.owner = self.owner_selection
                task_layer.get_transfer_data_owner(
                    asset_pipe, transfer_data_item_to_update.type)

        self.report({'INFO'}, message)
        return {'FINISHED'}


class ASSETPIPE_OT_refresh_asset_cat(Operator):
    bl_idname = "assetpipe.refresh_asset_cat"
    bl_label = "Refresh Asset Catalogs"
    bl_description = """Refresh Asset Catalogs"""

    def execute(self, context: Context):
        get_asset_catalog_items(reload=True)
        verify_task_layer_json_data()
        self.report({'INFO'}, "Asset Catalogs Refreshed!")
        return {'FINISHED'}


class ASSETPIPE_OT_save_asset_hook(Operator):
    bl_idname = "assetpipe.save_production_hook"
    bl_label = "Save Production Hook"
    bl_description = """Save new hook file based on example file. Production hooks are used across all assets. Asset hooks are only used in the current asset.
    - Production hooks: 'svn/pro/config' directory.
    - Asset hooks are stored at the root of the asset's directory'"""
    mode: EnumProperty(
        name="Hooks Mode",
        description=
        "Choose to either save production level or asset level hooks",
        items=[
            ('PROD', 'Production', 'Save Prododuction Level Hooks'),
            ('ASSET', 'Asset', 'Save Asset Level Hooks'),
        ],
    )

    def execute(self, context: Context):
        if self.mode == 'PROD':
            example_hooks_dir = (Path(__file__).parent.joinpath(
                "hook_examples").joinpath('prod_hooks.py'))
            hook_dir = get_production_hook_dir()
            if not hook_dir:
                self.report({
                    'ERROR'
                }, "Production directory must be specified in the add-on preferences."
                            )
                return {'CANCELLED'}
            save_hook_path = get_production_hook_dir().joinpath(
                'hooks.py').resolve()
        else:  # if self.mode == 'ASSET'
            example_hooks_dir = (Path(__file__).parent.joinpath(
                "hook_examples").joinpath('asset_hooks.py'))
            save_hook_path = get_asset_hook_dir().joinpath(
                'hooks.py').resolve()

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


registry = [
    ASSETPIPE_OT_reset_ownership,
    ASSETPIPE_OT_update_local_task_layers,
    ASSETPIPE_OT_revert_file,
    ASSETPIPE_OT_fix_prefixes,
    ASSETPIPE_OT_batch_ownership_change,
    ASSETPIPE_OT_refresh_asset_cat,
    ASSETPIPE_OT_save_asset_hook,
]
