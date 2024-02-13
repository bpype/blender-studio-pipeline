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
# (c) 2021, Blender Foundation

from typing import Any, List, Tuple
from pathlib import Path
from .. import prefs
import bpy

from ..models import FileListModel
from ..logger import LoggerFactory

EDIT_RENDER_FILE_MODEL = FileListModel()
_edit_render_enum_list: List[Tuple[str, str, str]] = []
_edit_render_file_model_init: bool = False

logger = LoggerFactory.getLogger()

# TODO Compare to Playblast opsdata, maybe centralize some repeated code


def init_edit_render_file_model(
    context: bpy.types.Context,
) -> None:
    global EDIT_RENDER_FILE_MODEL
    global _edit_render_file_model_init

    addon_prefs = prefs.addon_prefs_get(context)
    kitsu_props = context.scene.kitsu
    edit_export_dir = Path(addon_prefs.edit_export_dir)

    # Is None if invalid.
    if addon_prefs.edit_export_dir == "" or not edit_export_dir.exists():
        logger.error(
            "Failed to initialize edit render file model. Invalid path. Check addon preferences"
        )
        return

    EDIT_RENDER_FILE_MODEL.reset()
    EDIT_RENDER_FILE_MODEL.root_path = edit_export_dir

    if not EDIT_RENDER_FILE_MODEL.versions:
        EDIT_RENDER_FILE_MODEL.append_item("v001")
        # Update edit_render_version prop.
        kitsu_props.edit_render_Version = "v001"

    else:
        # Update edit_render_version prop.
        kitsu_props.edit_render_version = EDIT_RENDER_FILE_MODEL.versions[0]

    _edit_render_file_model_init = True


def add_edit_render_version_increment(context: bpy.types.Context) -> str:
    # Init model if it did not happen.
    if not _edit_render_file_model_init:
        init_edit_render_file_model(context)

    # Should be already sorted.
    versions = EDIT_RENDER_FILE_MODEL.versions

    if len(versions) > 0:
        latest_version = versions[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    EDIT_RENDER_FILE_MODEL.append_item(increment)
    return increment


def get_edit_render_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:
    global _edit_render_enum_list
    global EDIT_RENDER_FILE_MODEL
    global init_edit_render_file_model
    global _edit_render_file_model_init

    # Init model if it did not happen.
    if not _edit_render_file_model_init:
        init_edit_render_file_model(context)

    # Clear all versions in enum list.
    _edit_render_enum_list.clear()
    _edit_render_enum_list.extend(EDIT_RENDER_FILE_MODEL.versions_as_enum_list)

    return _edit_render_enum_list


def add_version_custom(custom_version: str) -> None:
    global _edit_render_enum_list
    global EDIT_RENDER_FILE_MODEL

    EDIT_RENDER_FILE_MODEL.append_item(custom_version)
