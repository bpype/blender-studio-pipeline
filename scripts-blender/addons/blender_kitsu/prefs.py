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

import hashlib
import sys
import os
import re

from typing import Optional, Any, Set, Tuple, List
from pathlib import Path

import bpy

from . import cache, bkglobals
from .props import get_safely_string_prop

# TODO: restructure this to not access ops_playblast_data.
from .playblast import opsdata as ops_playblast_data
from .types import Session
from .logger import LoggerFactory
from .auth.ops import (
    KITSU_OT_session_end,
    KITSU_OT_session_start,
)
from .context.ops import KITSU_OT_con_productions_load
from .lookdev.prefs import LOOKDEV_preferences
from .edit.core import edit_export_get_latest


logger = LoggerFactory.getLogger()


def draw_file_path(
    self, layout: bpy.types.UILayout, bool_prop: bool, bool_prop_name: str, path_prop_name: str
) -> None:
    # Draw auto-filled file path with option to override/edit this path
    icon = "MODIFIER_ON" if bool_prop else "MODIFIER_OFF"
    seq_row = layout.row(align=True)
    seq_row.prop(self, path_prop_name)
    seq_row.prop(self, bool_prop_name, icon=icon, text="")


class KITSU_task(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    id: bpy.props.StringProperty(name="Task ID", default="")
    entity_id: bpy.props.StringProperty(name="Entity ID", default="")
    entity_name: bpy.props.StringProperty(name="Entity Name", default="")
    task_type_id: bpy.props.StringProperty(name="Task Type ID", default="")
    task_type_name: bpy.props.StringProperty(name="Task Type Name", default="")


class KITSU_media_update_search_paths(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    filepath: bpy.props.StringProperty(
        name="Media Update Search Path",
        default="",
        subtype="DIR_PATH",
        description="Top level directory path in which to search for media updates",
    )


class KITSU_OT_prefs_media_search_path_add(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.prefs_media_search_path_add"
    bl_label = "Add Path"
    bl_description = "Adds new entry to media update search paths list"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)
        media_update_search_paths = addon_prefs.media_update_search_paths

        item = media_update_search_paths.add()

        return {"FINISHED"}


class KITSU_OT_prefs_media_search_path_remove(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.prefs_media_search_path_remove"
    bl_label = "Removes Path"
    bl_description = "Removes Path from media udpate search paths list"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(
        name="Index",
        description="Refers to index that will be removed from collection property",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)
        media_update_search_paths = addon_prefs.media_update_search_paths

        media_update_search_paths.remove(self.index)

        return {"FINISHED"}


class KITSU_addon_preferences(bpy.types.AddonPreferences):
    """
    Addon preferences to kitsu. Holds variables that are important for authentication and configuring
    how some of the operators work.
    """

    def get_metadatastrip_file(self) -> str:
        res_dir = bkglobals.RES_DIR_PATH
        return res_dir.joinpath("metastrip.mp4").as_posix()

    metadatastrip_file: bpy.props.StringProperty(  # type: ignore
        name="Metadata Strip File",
        description=(
            "Filepath to black .mp4 file that will be used as metastrip for shots in the sequence editor"
        ),
        default="",
        subtype="FILE_PATH",
        get=get_metadatastrip_file,
    )

    def get_datadir(self) -> Path:
        """Returns a Path where persistent application data can be stored.

        # linux: ~/.local/share
        # macOS: ~/Library/Application Support
        # windows: C:/Users/<USER>/AppData/Roaming
        """
        # This function is copied from the edit_breakdown addon by Inês Almeida and Francesco Siddi.

        home = Path.home()

        if sys.platform == "win32":
            return home / "AppData/Roaming"
        elif sys.platform == "linux":
            return home / ".local/share"
        elif sys.platform == "darwin":
            return home / "Library/Application Support"

    def get_thumbnails_dir(self) -> str:
        """Generate a path based on get_datadir and the current file name.

        The path is constructed by combining the OS application data dir,
        "blender_kitsu" and a hashed version of the filepath.
        """
        # This function is copied and modified from the edit_breakdown addon by Inês Almeida and Francesco Siddi.

        hashed_filepath = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = self.get_datadir() / "blender_kitsu" / "thumbnails" / hashed_filepath
        return storage_dir.as_posix()

    def get_sqe_render_dir(self) -> str:
        hashed_filepath = hashlib.md5(bpy.data.filepath.encode()).hexdigest()
        storage_dir = self.get_datadir() / "blender_kitsu" / "sqe_render" / hashed_filepath
        return storage_dir.absolute().as_posix()

    def get_config_dir(self) -> str:
        if not self.is_project_root_valid:
            return ""
        return self.project_root_path.joinpath("pipeline/blender_kitsu").as_posix()

    def init_playblast_file_model(self, context: bpy.types.Context) -> None:
        ops_playblast_data.init_playblast_file_model(context)

    bl_idname = __package__

    host: bpy.props.StringProperty(  # type: ignore
        name="Host",
        default="",
    )

    email: bpy.props.StringProperty(  # type: ignore
        name="Email",
        default="",
    )

    passwd: bpy.props.StringProperty(  # type: ignore
        name="Password", default="", options={"HIDDEN", "SKIP_SAVE"}, subtype="PASSWORD"
    )

    thumbnail_dir: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Directory",
        description="Directory in which thumbnails will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_thumbnails_dir,
    )

    sqe_render_dir: bpy.props.StringProperty(  # type: ignore
        name="Sequence Editor Render Directory",
        description="Directory in which sequence renders will be saved",
        default="",
        subtype="DIR_PATH",
        get=get_sqe_render_dir,
    )

    lookdev: bpy.props.PointerProperty(  # type: ignore
        name="Lookdev Preferences",
        type=LOOKDEV_preferences,
        description="Metadata that is required for lookdev",
    )

    def get_shot_playblast_root_dir(self) -> str:
        frames_dir = self.project_root_path.joinpath("shared/editorial/footage/pro/")
        if frames_dir.exists():
            return frames_dir.as_posix()
        return ""

    def set_shot_playblast_root_dir(self, input):
        self['shot_playblast_root_dir'] = input
        return

    def get_shot_playblast_root_dir(
        self,
    ) -> str:
        if get_safely_string_prop(self, 'shot_playblast_root_dir') == "" and self.project_root_path:
            dir = self.project_root_path.joinpath("shared/editorial/footage/pro/")
            if dir.exists():
                return dir.as_posix()
        return get_safely_string_prop(self, 'shot_playblast_root_dir')

    shot_playblast_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Shot Playblasts",
        description="Directory path to shot playblast root folder. Should point to: {project}/editorial/footage/pro",
        default="",
        subtype="DIR_PATH",
        update=init_playblast_file_model,
        get=get_shot_playblast_root_dir,
        set=set_shot_playblast_root_dir,
    )

    def set_seq_playblast_root_dir(self, input):
        self['seq_playblast_root_dir'] = input
        return

    def get_seq_playblast_root_dir(
        self,
    ) -> str:
        if get_safely_string_prop(self, 'seq_playblast_root_dir') == "" and self.project_root_path:
            dir = self.project_root_path.joinpath("shared/editorial/footage/pre/")
            if dir.exists():
                return dir.as_posix()
        return get_safely_string_prop(self, 'seq_playblast_root_dir')

    seq_playblast_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Sequence Playblasts",
        description="Directory path to sequence playblast root folder. Should point to: {project}/editorial/footage/pre",
        default="",
        subtype="DIR_PATH",
        get=get_seq_playblast_root_dir,
        set=set_seq_playblast_root_dir,
        options=set(),
    )

    def set_frames_root_dir(self, input):
        self['frames_root_dir'] = input
        return

    def get_frames_root_dir(
        self,
    ) -> str:
        if get_safely_string_prop(self, 'frames_root_dir') == "" and self.project_root_path:
            dir = self.project_root_path.joinpath("shared/editorial/footage/post/")
            if dir.exists():
                return dir.as_posix()
        return get_safely_string_prop(self, 'frames_root_dir')

    frames_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Rendered Frames",
        description="Directory path to rendered frames root folder. Should point to: {project}/editorial/footage/post",
        default="",
        subtype="DIR_PATH",
        get=get_frames_root_dir,
        set=set_frames_root_dir,
    )

    project_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Project Root Directory",
        description=(
            "Directory path to the root of the project"
            "In this directory blender kitsu searches for the svn/ & shared/ directories"
            "Directory should follow `you_project_name/` format without any subdirectories"
        ),
        default="/data/gold/",
        subtype="DIR_PATH",
    )
    config_dir: bpy.props.StringProperty(  # type: ignore
        name="Config Directory",
        description=(
            "Configuration directory of blender_kitsu"
            "See readme.md how you can configurate the addon on a per project basis"
        ),
        default="",
        subtype="DIR_PATH",
        get=get_config_dir,
    )

    project_active_id: bpy.props.StringProperty(  # type: ignore
        name="Project Active ID",
        description="Server Id that refers to the last active project",
        default="",
    )

    enable_debug: bpy.props.BoolProperty(  # type: ignore
        name="Enable Debug Operators",
        description="Enables Operatots that provide debug functionality",
    )
    show_advanced: bpy.props.BoolProperty(  # type: ignore
        name="Show Advanced Settings",
        description="Show advanced settings that should already have good defaults",
    )
    shot_builder_show_advanced: bpy.props.BoolProperty(  # type: ignore
        name="Show Advanced Settings",
        description="Show advanced settings that should already have good defaults",
    )

    def set_shot_pattern(self, input):
        self['shot_pattern'] = input
        return

    def get_shot_pattern(
        self,
    ) -> str:
        active_project = cache.project_active_get()
        if get_safely_string_prop(self, 'shot_pattern') == "":
            if active_project.production_type == bkglobals.KITSU_TV_PROJECT:
                return "<Episode>_<Sequence>_<Counter>"
            return "<Sequence>_<Counter>"
        return get_safely_string_prop(self, 'shot_pattern')

    shot_pattern: bpy.props.StringProperty(  # type: ignore
        name="Shot Pattern",
        description="Pattern to define how Bulk Init will name the shots. Supported wildcards: <Project>, <Episode>, <Sequence>, <Counter>",
        default="<Sequence>_<Counter>",
        get=get_shot_pattern,
        set=set_shot_pattern,
    )

    shot_counter_digits: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Digits",
        description="How many digits the counter should contain",
        default=4,
        min=0,
    )
    shot_counter_increment: bpy.props.IntProperty(  # type: ignore
        name="Shot Counter Increment",
        description="By which Increment counter should be increased",
        default=10,
        step=5,
        min=0,
    )
    pb_open_webbrowser: bpy.props.BoolProperty(  # type: ignore
        name="Open Webbrowser after Playblast",
        description="Toggle if the default webbrowser should be opened to kitsu after playblast creation",
        default=False,
    )

    pb_open_vse: bpy.props.BoolProperty(  # type: ignore
        name="Open Sequence Editor after Playblast",
        description="Toggle if the movie clip should be loaded in the seqeuence editor in a seperate scene after playblast creation",
        default=False,
    )

    pb_manual_burn_in: bpy.props.BoolProperty(  # type: ignore
        name="Manual Playblast Burn-Ins",
        description=(
            "Blender Kitsu will override all Shot/Sequence playblasts with it's own metadata burn in. "
            "This includes frame, lens, Shot name & Animator name at font size of 24. "
            "To use a file's metadata burn in settings during playblast enable this option"
        ),
        default=False,
    )

    media_update_search_paths: bpy.props.CollectionProperty(type=KITSU_media_update_search_paths)

    production_path: bpy.props.StringProperty(  # type: ignore
        name="Production Root",
        description="The location to load configuration files from when "
        "they couldn't be found in any parent folder of the current "
        "file. Folder must contain a sub-folder named `shot-builder` "
        "that holds the configuration files",
        subtype='DIR_PATH',
    )

    def set_edit_export_dir(self, input):
        self['edit_export_dir'] = input
        return

    def get_edit_export_dir(
        self,
    ) -> str:
        if get_safely_string_prop(self, 'edit_export_dir') == "" and self.project_root_path:
            dir = self.project_root_path.joinpath("shared/editorial/export/")
            if dir.exists():
                return dir.as_posix()
        return get_safely_string_prop(self, 'edit_export_dir')

    edit_export_dir: bpy.props.StringProperty(  # type: ignore
        name="Edit Export Directory",
        options={"HIDDEN", "SKIP_SAVE"},
        description="Directory path to editorial's export folder containing storyboard/animatic renders. Path should be similar to '{project}/shared/editorial/export/'",
        subtype="DIR_PATH",
        get=get_edit_export_dir,
        set=set_edit_export_dir,
    )

    def set_edit_export_file_pattern(self, input):
        self['edit_export_file_pattern'] = input
        return

    def get_edit_export_file_pattern(
        self,
    ) -> str:
        active_project = cache.project_active_get()
        if get_safely_string_prop(self, 'edit_export_file_pattern') == "" and active_project:
            proj_name = active_project.name.replace(' ', bkglobals.SPACE_REPLACER).lower()
            # HACK for Project Gold at Blender Studio
            if proj_name == "project_gold":
                return f"gold-edit-v###.mp4"
            return f"{proj_name}-edit-v###.mp4"
        return get_safely_string_prop(self, 'edit_export_file_pattern')

    edit_export_file_pattern: bpy.props.StringProperty(  # type: ignore
        name="Edit Export File Pattern",
        options={"HIDDEN", "SKIP_SAVE"},
        description=(
            "File pattern for latest editorial export file. "
            "Typically '{proj_name}-edit-v###.mp4' where # represents a number. "
            "Pattern must contain exactly v### representing the version, pattern must end in .mp4"
        ),
        default="",
        get=get_edit_export_file_pattern,
        set=set_edit_export_file_pattern,
    )

    edit_export_frame_offset: bpy.props.IntProperty(  # type: ignore
        name="Edit Export Offset",
        description="Shift Editorial Export by this frame-range after import",
        default=-101,
    )

    shot_builder_frame_offset: bpy.props.IntProperty(  # type: ignore
        name="Start Frame Offset",
        description="All Shots built by 'Shot_builder' should begin at this frame",
        default=101,
    )

    session: Session = Session()

    tasks: bpy.props.CollectionProperty(type=KITSU_task)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=True, align=False
        )
        col = flow.column()
        project_active = cache.project_active_get()

        # Login.
        box = col.box()
        box.label(text="Login and Host Settings", icon="URL")
        if not self.session.is_auth():
            box.row().prop(self, "host")
            box.row().prop(self, "email")
            box.row().prop(self, "passwd")
            box.row().operator(KITSU_OT_session_start.bl_idname, text="Login", icon="PLAY")
        else:
            row = box.row()
            row.prop(self, "host")
            row.enabled = False
            box.row().label(text=f"Logged in: {self.session.email}")
            box.row().operator(KITSU_OT_session_end.bl_idname, text="Logout", icon="PANEL_CLOSE")

        # Project
        box = col.box()
        box.label(text="Project", icon="FILEBROWSER")
        row = box.row(align=True)

        if not project_active:
            prod_load_text = "Select Project"
        else:
            prod_load_text = project_active.name

        row.operator(
            KITSU_OT_con_productions_load.bl_idname,
            text=prod_load_text,
            icon="DOWNARROW_HLT",
        )
        box.row().prop(self, "project_root_dir")

        # Previews
        box = col.box()
        box.label(text="Previews", icon="RENDER_ANIMATION")
        box.row().prop(self, "shot_playblast_root_dir")
        box.row().prop(self, "seq_playblast_root_dir")
        box.row().prop(self, "frames_root_dir")
        box.row().prop(self, "pb_open_webbrowser")
        box.row().prop(self, "pb_open_vse")
        box.row().prop(self, "pb_manual_burn_in")

        # Editorial Settings
        box = col.box()
        box.label(text="Editorial", icon="SEQ_SEQUENCER")
        box.row().prop(self, "edit_export_dir", text="Export Directory")
        file_pattern_row = box.row(align=True)
        file_pattern_row.alert = not self.is_edit_export_pattern_valid
        file_pattern_row.prop(self, "edit_export_file_pattern", text="Export File Pattern")
        box.row().prop(self, "edit_export_frame_offset")

        # Lookdev tools settings.
        self.lookdev.draw(context, col)

        # Sequence editor include paths.
        box = col.box()
        box.label(text="Media Update Search Paths", icon="SEQUENCE")
        box.label(
            text="Only the movie strips that have their source media coming from one of these folders (recursive) will be checked for media updates"
        )

        for i, item in enumerate(self.media_update_search_paths):
            row = box.row()
            row.prop(item, "filepath", text="")
            row.operator(
                KITSU_OT_prefs_media_search_path_remove.bl_idname,
                text="",
                icon="X",
                emboss=False,
            ).index = i
        row = box.row()
        row.alignment = "LEFT"
        row.operator(
            KITSU_OT_prefs_media_search_path_add.bl_idname,
            text="",
            icon="ADD",
            emboss=False,
        )

        # Shot_Builder settings.
        box = col.box()
        box.label(text="Shot Builder", icon="MOD_BUILD")
        box.prop(self, "shot_builder_frame_offset")
        row = box.row(align=True)
        # Avoids circular import error
        from .shot_builder.ops import (
            KITSU_OT_build_config_save_settings,
            KITSU_OT_build_config_save_hooks,
            KITSU_OT_build_config_save_templates,
        )
        box.row().operator(KITSU_OT_build_config_save_hooks.bl_idname, icon='FILE_SCRIPT')
        box.row().operator(KITSU_OT_build_config_save_settings.bl_idname, icon="TEXT")
        box.row().operator(KITSU_OT_build_config_save_templates.bl_idname, icon="FILE_BLEND")

        # Misc settings.
        box = col.box()
        box.label(text="Miscellaneous", icon="MODIFIER")
        box.row().prop(self, "thumbnail_dir")
        box.row().prop(self, "sqe_render_dir")
        box.row().prop(self, "enable_debug")
        box.row().prop(self, "show_advanced")

        if self.show_advanced:
            box.row().prop(self, "shot_pattern")
            box.row().prop(self, "shot_counter_digits")
            box.row().prop(self, "shot_counter_increment")

    @property
    def shot_playblast_root_path(self) -> Optional[Path]:
        if not self.is_playblast_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.shot_playblast_root_dir)))

    @property
    def seq_playblast_root_path(self) -> Optional[Path]:
        if not self.is_playblast_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.seq_playblast_root_dir)))

    @property
    def is_playblast_root_valid(self) -> bool:
        if not self.shot_playblast_root_dir:
            return False

        if not bpy.data.filepath and self.shot_playblast_root_dir.startswith("//"):
            return False

        return True

    @property
    def is_edit_export_root_valid(self) -> bool:
        if self.edit_export_dir.strip() == "":
            return False
        if not Path(self.edit_export_dir).exists():
            return False
        return True

    @property
    def is_edit_export_pattern_valid(self) -> bool:
        if not self.edit_export_file_pattern.endswith(".mp4"):
            return False
        if not "###" in self.edit_export_file_pattern:
            return False
        return True

    @property
    def project_root_path(self) -> Optional[Path]:
        if not self.project_root_dir:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.project_root_dir)))

    @property
    def is_project_root_valid(self) -> bool:
        if not self.project_root_dir:
            return False

        if not bpy.data.filepath and self.project_root_dir.startswith("//"):
            return False

        return True

    @property
    def is_config_dir_valid(self) -> bool:
        if not self.config_dir:
            return False

        if not bpy.data.filepath and self.config_dir.startswith("//"):
            return False

        return True


def session_get(context: bpy.types.Context) -> Session:
    """
    Shortcut to get session from blender_kitsu addon preferences
    """
    prefs = context.preferences.addons[__package__].preferences
    return prefs.session  # type: ignore


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    Shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons[__package__].preferences


def project_root_dir_get(context: bpy.types.Context):
    addon_prefs = addon_prefs_get(context)
    return Path(addon_prefs.project_root_dir).joinpath('svn').resolve()


def session_auth(context: bpy.types.Context) -> bool:
    """
    Shortcut to check if zession is authorized
    """
    return session_get(context).is_auth()


# ---------REGISTER ----------.

classes = [
    KITSU_OT_prefs_media_search_path_remove,
    KITSU_OT_prefs_media_search_path_add,
    KITSU_task,
    KITSU_media_update_search_paths,
    KITSU_addon_preferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Log user out.
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if addon_prefs.session.is_auth():
        addon_prefs.session.end()

    # Unregister classes.
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
