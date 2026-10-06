# SPDX-FileCopyrightText: 2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.props import EnumProperty
from bpy.types import Context, Event, Operator, OperatorProperties, Text

from ..hooks import get_asset_hooks_path, get_production_hooks_path
from ..utils import get_addon_prefs


class HookOpMixin:
    hook_type: EnumProperty(
        name="Hook Type",
        description=
        "Choose to either save production level or asset level hooks",
        items=[
            ('PROD', 'Production', 'Save project-level hook, which runs for all assets'),
            ('ASSET', 'Asset', 'Save Asset Level Hooks'),
        ],
    )

    def get_hook_path(self) -> Path:
        if self.hook_type == 'PROD':
            return get_production_hooks_path()
        return get_asset_hooks_path()

    def get_text_datablock(self) -> Text | None:
        hook_path = self.get_hook_path()
        return next(
            (t for t in bpy.data.texts if t.filepath and Path(bpy.path.abspath(t.filepath)) == hook_path),
            None,
        )


class ASSETPIPE_OT_save_hook(HookOpMixin, Operator):
    bl_idname = "assetpipe.save_hook"
    bl_label = "Save Hook"
    bl_description = "Save Asset/Production Hook"

    @classmethod
    def description(cls, _context: Context, properties: OperatorProperties):
        if properties.hook_type == 'PROD':
            return "Initialize project-wide hook.py file, where you can implement custom push/pull behaviours that will apply to all assets in the project"
        return "Initialize hook.py file for this asset, where you can implement custom push/pull behaviour for this specific asset"

    def execute(self, context: Context):
        prefs = get_addon_prefs(context)
        hooks_path = self.get_hook_path()
        if self.hook_type == 'PROD':
            example_hooks_dir = Path(__file__).parent.parent / Path("hook_examples/prod_hooks.py")
            if not prefs.hooks_dir:
                self.report({'ERROR'}, "Hooks directory must be specified in the add-on preferences.")
                return {'CANCELLED'}
            hooks_path.parent.mkdir(parents=True, exist_ok=True)
        elif self.hook_type == 'ASSET':
            example_hooks_dir = Path(__file__).parent.parent / Path("hook_examples/asset_hooks.py")
        else:
            self.report({'ERROR'}, f"Unknown hook type: {self.hook_type}")
            return {'CANCELLED'}

        if not example_hooks_dir.exists():
            self.report({'ERROR'}, "Cannot find example hook file: {path}".format(path=example_hooks_dir))
            return {'CANCELLED'}

        if hooks_path.exists():
            self.report(
                {'ERROR'},
                f"Hook file already exists: '{hooks_path.__str__()}'",
            )
            return {'CANCELLED'}

        with example_hooks_dir.open() as source:
            contents = source.read()

        # Write contents to target file
        with hooks_path.open('w') as target:
            target.write(contents)

        self.report({'INFO'}, f"Hook File saved to {hooks_path.__str__()}")
        return {'FINISHED'}


class ASSETPIPE_OT_edit_hook(HookOpMixin, Operator):
    bl_idname = "assetpipe.edit_hook"
    bl_label = "Edit Hook"
    bl_description = "Open Hook in Text Editor"

    @classmethod
    def description(cls, _context: Context, properties: OperatorProperties):
        if properties.hook_type == 'PROD':
            return "Load the project-wide hooks.py file into the text editor"
        return "Load the hooks.py file for this asset into the text editor"

    def execute(self, context: Context):
        hook_path = self.get_hook_path()

        if not hook_path.exists():
            self.report({'ERROR'}, f"Hook file not found: '{hook_path.__str__()}'")
            return {'CANCELLED'}

        # Load hook_path into Blender's text editor, and if there is a text editor on screen, set it as the active text datablock.
        text = self.get_text_datablock()
        if not text:
            text = bpy.data.texts.load(hook_path.__str__())

        for area in context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR':
                        space.text = text

        return {'FINISHED'}


class ASSETPIPE_OT_delete_hook(HookOpMixin, Operator):
    bl_idname = "assetpipe.delete_hook"
    bl_label = "Delete Hook"
    bl_description = "Delete Asset/Production Hook"

    @classmethod
    def description(cls, _context: Context, properties: OperatorProperties):
        if properties.hook_type == 'PROD':
            return "Delete the project-wide hooks.py file"
        return "Delete the hooks.py file for this asset"

    def invoke(self, context: Context, _event: Event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, _context: Context):
        self.layout.alert = True
        self.layout.label(text=f"Delete this file from disk?")
        self.layout.label(text=f"{self.get_hook_path().as_posix()}", icon='TEXT')

    def execute(self, context: Context):
        hook_path = self.get_hook_path()

        if not hook_path.exists():
            self.report({'ERROR'}, f"Hook file not found: '{hook_path.__str__()}'")
            return {'CANCELLED'}

        text = self.get_text_datablock()
        if text:
            bpy.data.texts.remove(text)

        hook_path.unlink()
        self.report({'INFO'}, f"Deleted Hook File: {hook_path.__str__()}")
        return {'FINISHED'}


def draw_hook_ops(layout):
    col = layout.column(align=True)

    if get_production_hooks_path().exists():
        row = col.row(align=True)
        row.operator("assetpipe.edit_hook", text="Edit Production Hook", icon='GREASEPENCIL').hook_type = 'PROD'
        row.operator("assetpipe.delete_hook", text="", icon='TRASH').hook_type = 'PROD'
    else:
        col.operator("assetpipe.save_hook", text="Create Production Hook", icon='HOOK').hook_type = 'PROD'

    if get_asset_hooks_path().exists():
        row = col.row(align=True)
        row.operator("assetpipe.edit_hook", text="Edit Asset Hook", icon='GREASEPENCIL').hook_type = 'ASSET'
        row.operator("assetpipe.delete_hook", text="", icon='TRASH').hook_type = 'ASSET'
    else:
        col.operator("assetpipe.save_hook", text="Create Asset Hook", icon='HOOK').hook_type = 'ASSET'


registry = [
    ASSETPIPE_OT_save_hook,
    ASSETPIPE_OT_edit_hook,
    ASSETPIPE_OT_delete_hook,
]
