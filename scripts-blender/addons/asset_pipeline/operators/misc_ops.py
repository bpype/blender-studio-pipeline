# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import BoolVectorProperty, EnumProperty
from bpy.types import Context, Event, Operator

from ..asset_catalog import get_asset_catalog_items
from ..config import verify_task_layer_json_data
from ..hooks import get_asset_hook_dir, get_production_hook_dir
from ..merge import naming, task_layer


class ASSETPIPE_OT_update_local_task_layers(Operator):
    bl_idname = "assetpipe.update_local_task_layers"
    bl_label = "Update Local Task Layers"
    bl_description = """Change the Task Layers that are Local to your file"""
    bl_options = {'REGISTER', 'UNDO'}

    task_layer_selection: BoolVectorProperty(size=32, options={'SKIP_SAVE'})

    def invoke(self, context: Context, event: Event):
        asset_pipe = context.scene.asset_pipeline
        for i, tasklay in enumerate(asset_pipe.all_task_layers):
            self.task_layer_selection[i] = tasklay.name in asset_pipe.local_task_layers
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: Context):
        layout = self.layout

        asset_pipe = context.scene.asset_pipeline
        for i, tasklay in enumerate(asset_pipe.all_task_layers):
            layout.prop(self, 'task_layer_selection', index=i, text=tasklay.name)

        col = layout.column()
        col.alert = True
        col.label(text="Caution, this only affects current file.", icon="ERROR")
        col.label(text="Two files owning the same task layer can lead to errors.")

    def execute(self, context: Context):
        asset_pipe = context.scene.asset_pipeline
        all_task_layers = asset_pipe.all_task_layers
        new_local_task_layers = [tl.name for i, tl in enumerate(all_task_layers) if self.task_layer_selection[i]]
        asset_pipe.set_local_task_layers(new_local_task_layers)
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
    ASSETPIPE_OT_update_local_task_layers,
    ASSETPIPE_OT_revert_file,
    ASSETPIPE_OT_fix_prefixes,
    ASSETPIPE_OT_refresh_asset_cat,
    ASSETPIPE_OT_save_asset_hook,
]
