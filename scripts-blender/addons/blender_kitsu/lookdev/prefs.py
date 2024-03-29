# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import os
from typing import Optional
from pathlib import Path
from .. import prefs
from ..props import get_safely_string_prop
import bpy

from . import opsdata


class LOOKDEV_preferences(bpy.types.PropertyGroup):

    """
    Addon preferences for lookdev module.
    """

    def update_rd_preset_file_model(self, context: bpy.types.Context) -> None:
        opsdata.init_rd_preset_file_model(context)

    def set_look_dev_dir(self, input):
        self['presets_dir'] = input
        return

    def get_look_dev_dir(self) -> str:
        proj_root = prefs.project_root_dir_get(bpy.context)
        if get_safely_string_prop(self, 'presets_dir') == "" and proj_root:
            frames_dir = proj_root.joinpath("pro/assets/scripts/render_presets/")
            if frames_dir.exists():
                return frames_dir.as_posix()
        return get_safely_string_prop(self, 'presets_dir')

    presets_dir: bpy.props.StringProperty(  # type: ignore
        name="Render Presets Directory",
        description="Directory path to folder in which render settings python files are stored",
        default="",
        subtype="DIR_PATH",
        update=update_rd_preset_file_model,
        get=get_look_dev_dir,
        set=set_look_dev_dir,
    )

    @property
    def is_presets_dir_valid(self) -> bool:
        # Check if file is saved.
        if not self.presets_dir:
            return False

        if not bpy.data.filepath and self.presets_dir.startswith("//"):
            return False

        return True

    @property
    def presets_dir_path(self) -> Optional[Path]:
        if not self.presets_dir:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.presets_dir)))

    def draw(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
    ) -> None:
        # Render preset.
        box = layout.box()
        box.label(text="Lookdev Tools", icon="RESTRICT_RENDER_OFF")
        box.row().prop(self, "presets_dir")


# ---------REGISTER ----------.

classes = [LOOKDEV_preferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Unregister classes.
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
