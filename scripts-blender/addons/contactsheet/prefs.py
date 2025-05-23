# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import bpy
from pathlib import Path
from typing import Optional

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    Shortcut to get addon preferences.
    """
    if not context:
        context = bpy.context
    from . import __package__ as base_package
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


class CS_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    contactsheet_dir: bpy.props.StringProperty(  # type: ignore
        name="Contactsheet Output Directory",
        description="The contactsheet scene will use this directory to compose the output filepath",
        default="",
        subtype="DIR_PATH",
    )

    contactsheet_scale_factor: bpy.props.FloatProperty(
        name="Contactsheet Scale Factor",
        description="This value controls how much space there is between the individual cells of the contactsheet",
        min=0.1,
        max=1.0,
        step=5,
        default=0.9,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # Contactsheet settings.
        box.row().prop(self, "contactsheet_dir")
        box.row().prop(self, "contactsheet_scale_factor")

    @property
    def contactsheet_dir_path(self) -> Optional[Path]:
        if not self.is_contactsheet_dir_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.contactsheet_dir)))

    @property
    def is_contactsheet_dir_valid(self) -> bool:

        # Check if file is saved.
        if not self.contactsheet_dir:
            return False

        if not bpy.data.filepath and self.contactsheet_dir.startswith("//"):
            return False

        return True


# ---------REGISTER ----------.

classes = [CS_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
