# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Context

from .. import constants
from ..asset_catalog import get_asset_id
from ..images import save_images
from ..merge import publish


class ASSETPIPE_OT_open_file(bpy.types.Operator):
    bl_idname = "assetpipe.open_file"
    bl_label = "Open File"
    bl_description = """Open an Asset Pipeline File, will not prompt to save current file"""

    filepath: StringProperty(name="Filepath")

    def execute(self, context: Context):
        bpy.ops.wm.open_mainfile(filepath=self.filepath)
        return {'FINISHED'}


def get_publish_type_enum(self, context):
    sync_target = [
        (
            "sync_target",
            "Sync Target",
            "Find the Sync Target File, either Staged or Active",
        ),
    ]
    return sync_target + constants.PUBLISH_TYPES


class ASSETPIPE_OT_open_publish(bpy.types.Operator):
    bl_idname = "assetpipe.open_publish"
    bl_label = "Open Latest Publish"
    bl_description = """Open the current Published File used for Push/Pull/Sync."""

    publish_types: EnumProperty(
        name="Type",
        items=get_publish_type_enum,
    )
    save_file: BoolProperty(
        name="Save Changes before Closing?",
        default=False,
        description="Save the file before opening Published File",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # self.publish_types = "sync_target"
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, "publish_types")
        if bpy.data.is_dirty:
            layout.prop(self, "save_file")

    def execute(self, context: Context):
        if not context.scene.asset_pipeline.is_asset_pipeline_file:
            self.report({'ERROR'}, "Cannot open Publish, current file isn't asset pipeline file")
            return {'CANCELLED'}
        if Path(bpy.data.filepath).parent.name in constants.PUBLISH_KEYS:
            self.report({'ERROR'}, "Cannot open Publish, if current file is published")
            return {'CANCELLED'}

        if self.publish_types == "sync_target":
            published_file = publish.find_sync_target(Path(bpy.data.filepath))
        else:
            published_file = publish.find_latest_publish(
                Path(bpy.data.filepath), self.publish_types
            )

        if not published_file.exists():
            self.report(
                {'ERROR'},
                f"Cannot open {self.publish_types} no published file found at {str(published_file.parent)}",
            )
            return {'CANCELLED'}

        if self.save_file:
            save_images()
            bpy.ops.wm.save_mainfile()

        bpy.ops.wm.open_mainfile(filepath=str(published_file))
        return {'FINISHED'}


class ASSETPIPE_OT_publish_new_version(bpy.types.Operator):
    bl_idname = "assetpipe.publish_new_version"
    bl_label = "Publish New Version"
    bl_description = """Create a new Published Version in the Publish Area"""

    publish_types: EnumProperty(
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
            publish.is_staged_publish(Path(bpy.data.filepath))
            and self.publish_types != constants.SANDBOX_PUBLISH_KEY
        ):
            self.report(
                {'ERROR'},
                f"Only '{constants.SANDBOX_PUBLISH_KEY}' Publish is supported when a version is staged",
            )
            return {'CANCELLED'}
        catalog_id = get_asset_id(context.scene.asset_pipeline.asset_catalog_name)
        new_filepath = publish.create_next_published_file(
            current_file=Path(bpy.data.filepath),
            publish_type=self.publish_types,
            catalog_id=catalog_id,
        )
        self.report({'INFO'}, f"New Publish {self.publish_types} created at: {new_filepath}")
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
        if not publish.is_staged_publish(Path(bpy.data.filepath)):
            cls.poll_message_set("No File is currently staged")
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
        staged_file = publish.find_latest_publish(
            current_file, publish_type=constants.STAGED_PUBLISH_KEY
        )
        # Delete Staged File
        staged_file.unlink()
        catalog_id = get_asset_id(context.scene.asset_pipeline.asset_catalog_name)
        publish.create_next_published_file(current_file=current_file, catalog_id=catalog_id)
        return {'FINISHED'}


registry = [
    ASSETPIPE_OT_publish_new_version,
    ASSETPIPE_OT_publish_staged_as_active,
    ASSETPIPE_OT_open_publish,
    ASSETPIPE_OT_open_file,
]