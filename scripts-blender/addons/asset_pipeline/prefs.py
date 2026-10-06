# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import AddonPreferences, Context

from . import constants
from .logging import get_logger


class ASSET_PIPELINE_addon_preferences(AddonPreferences):
    bl_idname = __package__

    def on_project_root_set(self, _context: Context):
        self.hooks_dir_path = self.assets_dir_path / Path("config/asset_pipeline")

    assets_dir: StringProperty(
        name="Assets",
        description="Optional. Directory containing your assets. Used only to initialize other filepaths.",
        default="/path/to/your_project/",
        subtype="DIR_PATH",
        update=on_project_root_set,
    )
    @property
    def assets_dir_path(self) -> Path:
        return Path(self.assets_dir)
    @assets_dir_path.setter
    def assets_dir_path(self, value: Path):
        self.assets_dir = value.as_posix()

    hooks_dir: StringProperty(
        name="Project Hooks",
        description="Optional. Directory where project-wide hooks are created and loaded. Must be specified in order for production hooks to work. If specified but does not exist, it will be created when creating a production hook.",
        default="",
        subtype="DIR_PATH",
    )
    @property
    def hooks_dir_path(self) -> Path:
        return Path(self.hooks_dir)
    @hooks_dir_path.setter
    def hooks_dir_path(self, value: Path):
        self.hooks_dir = value.as_posix()


    custom_task_layers_dir: StringProperty(
        name="Custom Task Layers",
        description="Specify directory to add additonal Task Layer Presets to use as templates when cerating new assets",
        default="",
        subtype="DIR_PATH",
    )

    def update_logger_level(self, context):
        logger = get_logger()
        logger.handlers.clear()

    logger_level: EnumProperty(
        name="Logging Level",
        description="Changes the level of detail of print statements in blender's console",
        default=1,
        items=constants.LOGGER_LEVEL_ITEMS,
        update=update_logger_level,
    )

    preserve_action: BoolProperty(
        name="Preserve Actions in Workfiles",
        description="Preserve Action Data-Blocks on Armatures in working files during Pull (this data will not be pushed to Sync Target)",
        default=False,
    )

    preserve_indexes: BoolProperty(
        name="Preserve Active Indexes in Workfiles",
        description=(
            "Preserve Active Indexes (Vertex Groups, Shape Keys, UV Maps, Color Attributes, Attributes) "
            "in working files during Pull (this data will not be pushed to Sync Target)"
        ),
        default=False,
    )

    def draw(self, _context: Context):
        layout = self.layout.column()
        layout.use_property_decorate = False
        layout.use_property_split = True

        layout.prop(self, "logger_level")
        layout.prop(self, "preserve_action")
        layout.prop(self, "preserve_indexes")

        header, panel = layout.panel("Asset Pipeline Filepath", default_closed=True)
        header.label(text="File Paths")
        if panel:
            for prop_name in ("assets_dir", "hooks_dir", "custom_task_layers_dir"):
                row = layout.row()
                if not os.path.exists(getattr(self, prop_name)):
                    row.alert = True
                row.prop(self, prop_name)



registry = [
    ASSET_PIPELINE_addon_preferences,
]
