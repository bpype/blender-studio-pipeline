# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Union, List, Dict, Optional, Tuple

import bpy
from bpy.app.handlers import persistent

from . import propsdata, bkglobals, util
from .logger import LoggerFactory
from . import cache
from .types import Sequence

logger = LoggerFactory.getLogger()


class KITSU_sequence_colors(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    color: bpy.props.FloatVectorProperty(
        name="Sequence Color",
        subtype="COLOR",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Sequence color that will be used as line overlay",
    )


class KITSU_property_group_sequence(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """
    def _get_shot_description(self):
        return self.shot_description

    def _get_sequence_entity(self):
        try:
            return Sequence.by_id(self.sequence_id)
        except AttributeError:
            return None

    manual_shot_name: bpy.props.StringProperty(
        name="Shot",
        description="Enter a new Shot name to submit to Kitsu Server",
        default="",
    )  # type: ignore

    ###########
    # Shot
    ###########
    shot_id: bpy.props.StringProperty(  # type: ignore
        name="Shot ID",
        description="ID that refers to the strip's shot on server",
        default="",
    )

    def get_shot_via_name(self):
        return get_safely_string_prop(self, "shot_name")

    def set_shot_via_name(self, input):
        seq = self._get_sequence_entity()
        if seq is None:
            return

        # Attempt to set with matching Kitsu Entry
        kitsu_set = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_shots_enum_for_seq(self, bpy.context, seq),
            name_prop='shot_name',
            id_prop='shot_id',
        )

        # Set manually so users can submit new shots
        if not kitsu_set:
            self['shot_name'] = input
        return

    def get_shot_search_list(self, context, edit_text):
        seq = self._get_sequence_entity()
        if seq is None:
            return []
        return get_enum_item_names(cache.get_shots_enum_for_seq(self, bpy.context, seq))

    shot_name: bpy.props.StringProperty(  # type: ignore
        name="Shot",
        description="Name that refers to the strip's shot on server, Reminder: press ENTER to save shot name after entering",
        default="",
        get=get_shot_via_name,
        set=set_shot_via_name,
        options=set(),
        search=get_shot_search_list,
        search_options={'SORT', 'SUGGESTION'},
    )

    shot_description: bpy.props.StringProperty(name="Description", default="", options={"HIDDEN"})  # type: ignore

    ###########
    # Sequence
    ###########
    sequence_id: bpy.props.StringProperty(  # type: ignore
        name="Seq ID",
        description="ID that refers to the active sequence on server",
        default="",
    )

    def get_sequences_via_name(self):
        return get_safely_string_prop(self, "sequence_name")

    def set_sequences_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_sequences_enum_list(self, bpy.context),
            name_prop='sequence_name',
            id_prop='sequence_id',
        )
        return

    def get_sequence_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_sequences_enum_list(self, bpy.context))

    sequence_name: bpy.props.StringProperty(  # type: ignore
        name="Sequence",
        description="Sequence",
        default="",
        get=get_sequences_via_name,
        set=set_sequences_via_name,
        options=set(),
        search=get_sequence_search_list,
        search_options={'SORT'},
    )

    # Project.
    project_name: bpy.props.StringProperty(name="Project", default="")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID", default="")  # type: ignore

    # Meta.
    initialized: bpy.props.BoolProperty(  # type: ignore
        name="Initialized", default=False, description="Is Kitsu shot"
    )
    linked: bpy.props.BoolProperty(  # type: ignore
        name="Linked", default=False, description="Is linked to an ID on server"
    )

    # Frame range.
    frame_start_offset: bpy.props.IntProperty(name="Frame Start Offset")

    # Media.
    media_outdated: bpy.props.BoolProperty(
        name="Source Media Outdated",
        default=False,
        description="Indicated if there is a newer version of the source media available",
    )

    # Display props.
    shot_description_display: bpy.props.StringProperty(name="Description", get=_get_shot_description)  # type: ignore

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.shot,
            "sequence_name": self.sequence,
            "description": self.description,
        }

    def clear(self):
        self.shot_id = ""
        self.shot_name = ""
        self.shot_description = ""

        self.sequence_id = ""
        self.sequence_name = ""

        self.project_name = ""
        self.project_id = ""

        self.initialized = False
        self.linked = False

        self.frame_start_offset = 0

    def unlink(self):
        self.sequence_id = ""

        self.project_name = ""
        self.project_id = ""

        self.linked = False


def set_kitsu_entity_id_via_enum_name(
    self,
    items: List[Tuple[str, str, str]],
    input_name: str,
    name_prop: str,
    id_prop: str,
) -> str:
    """Set the ID and Name of a Kitsu entity by finding the matching ID for a given name
    and updating both values in their corrisponding String Properties (Kitsu Context Properties)

    Args:
        items (List[Tuple[str, str, str]]): Enum items in the format List[Tuple[id, name, description]]
        input_name (str): Name, used to find matching ID in a tuple
        name_prop (str): Name of String Property where Kitsu Enitity's Name is stored
        id_prop (str): Name of String Property where Kitsu Enitity's ID is stored

    Returns:
        str: ID of Kitsu entity
    """

    if input_name == "":
        self[id_prop] = ""
        self[name_prop] = input_name
        return
    for key, value, _ in items:
        if value == input_name:
            self[id_prop] = key
            self[name_prop] = input_name
            return key


def get_enum_item_names(enum_items: List[Tuple[str, str, str]]) -> List[str]:
    """Return a list of names from a list of enum items used by (Kitsu Context Properties)

    Args:
        enum_items (List[Tuple[str, str, str]]): Enum items in the format List[Tuple[id, name, description]]

    Returns:
       List[str]: List of avaliable names
    """
    return [item[1] for item in enum_items]


def get_safely_string_prop(self, name: str) -> str:
    """Return Value of String Property, and return "" if value isn't set"""
    try:
        return self[name]
    except KeyError:
        return ""


class KITSU_property_group_scene(bpy.types.PropertyGroup):
    """"""

    ################################
    # Kitsu Context Properties
    ################################
    """
    Kitsu Context Properties

    These are properties used to store/manage the current "Context"
    for a Kitsu Entity. Kitsu Entities represents things like Asset,
    Shot and Sequence for a given production.

    Each Entity has an 'ID' Property which is used internally by the add-on
    and a 'Name' Property which is used as part of the user interface. When a user selects
    the 'Name' of a Kitsu Entity a custom Set function on the property will also update
    the Entity's ID.

    NOTE: It would be nice to have searchable enums instead of doing all this work manually.
    """

    asset_col: bpy.props.PointerProperty(type=bpy.types.Collection, name="Collection")

    ###########
    # Sequence
    ###########
    sequence_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
    )

    def get_sequences_via_name(self):
        return get_safely_string_prop(self, "sequence_active_name")

    def set_sequences_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_sequences_enum_list(self, bpy.context),
            name_prop='sequence_active_name',
            id_prop='sequence_active_id',
        )
        if key:
            cache.sequence_active_set_by_id(bpy.context, key)
        else:
            cache.sequence_active_reset_entity()
        return

    def get_sequence_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_sequences_enum_list(self, bpy.context))

    sequence_active_name: bpy.props.StringProperty(
        name="Sequence",
        description="Sequence",
        default="",  # type: ignore
        get=get_sequences_via_name,
        set=set_sequences_via_name,
        options=set(),
        search=get_sequence_search_list,
        search_options={'SORT'},
    )

    ###########
    # Episode
    ###########
    episode_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Episode ID",
        description="ID that refers to the active episode on server",
        default="",
    )

    def get_episode_via_name(self):
        return get_safely_string_prop(self, "episode_active_name")

    def set_episode_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_episodes_enum_list(self, bpy.context),
            name_prop='episode_active_name',
            id_prop='episode_active_id',
        )

        # Clear active shot when sequence changes.
        if cache.episode_active_get().id != key:
            cache.sequence_active_reset(bpy.context)
            cache.asset_type_active_reset(bpy.context)
            cache.shot_active_reset(bpy.context)
            cache.asset_active_reset(bpy.context)

        if key:
            cache.episode_active_set_by_id(bpy.context, key)
        else:
            cache.episode_active_reset_entity()
        return

    def get_episode_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_episodes_enum_list(self, bpy.context))

    episode_active_name: bpy.props.StringProperty(
        name="Episode",
        description="Selet Active Episode",
        default="",  # type: ignore
        get=get_episode_via_name,
        set=set_episode_via_name,
        options=set(),
        search=get_episode_search_list,
        search_options={'SORT'},
    )

    ###########
    # Shot
    ###########
    shot_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Shot ID",
        description="IDthat refers to the active shot on server",
        default="",
        # update=propsdata.on_shot_change,
    )

    def get_shot_via_name(self):
        return get_safely_string_prop(self, "shot_active_name")

    def set_shot_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_shots_enum_for_active_seq(self, bpy.context),
            name_prop='shot_active_name',
            id_prop='shot_active_id',
        )
        if key:
            cache.shot_active_set_by_id(bpy.context, key)
        else:
            cache.shot_active_reset_entity()
        return

    def get_shot_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_shots_enum_for_active_seq(self, bpy.context))

    shot_active_name: bpy.props.StringProperty(
        name="Shot",
        description="Shot",
        default="",  # type: ignore
        get=get_shot_via_name,
        set=set_shot_via_name,
        options=set(),
        search=get_shot_search_list,
        search_options={'SORT'},
    )

    ###########
    # Asset
    ###########
    asset_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset ID",
        description="ID that refers to the active asset on server",
        default="",
    )

    def get_asset_via_name(self):
        return get_safely_string_prop(self, "asset_active_name")

    def set_asset_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_assets_enum_for_active_asset_type(self, bpy.context),
            name_prop='asset_active_name',
            id_prop='asset_active_id',
        )
        if key:
            cache.asset_active_set_by_id(bpy.context, key)  # TODO
        else:
            cache.asset_active_reset_entity()
        return

    def get_asset_type_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_assets_enum_for_active_asset_type(self, bpy.context))

    asset_active_name: bpy.props.StringProperty(
        name="Asset",
        description="Active Asset",
        default="",  # type: ignore
        get=get_asset_via_name,
        set=set_asset_via_name,
        options=set(),
        search=get_asset_type_search_list,
        search_options={'SORT'},
    )

    ############
    # Asset Type
    ############

    asset_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Asset Type ID",
        description="ID that refers to the active asset type on server",
        default="",
    )

    def get_asset_type_via_name(self):
        return get_safely_string_prop(self, "asset_type_active_name")

    def set_asset_type_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_assetypes_enum_list(self, bpy.context),
            name_prop='asset_type_active_name',
            id_prop='asset_type_active_id',
        )
        if key:
            cache.asset_type_active_set_by_id(bpy.context, key)
        else:
            cache.asset_type_active_reset_entity()
        return

    def get_asset_type_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_assetypes_enum_list(self, bpy.context))

    asset_type_active_name: bpy.props.StringProperty(
        name="Asset Type",
        description="Active Asset Type Name",
        default="",  # type: ignore
        get=get_asset_type_via_name,
        set=set_asset_type_via_name,
        options=set(),
        search=get_asset_type_search_list,
        search_options={'SORT'},
    )

    ############
    # Task Type
    ############

    task_type_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Task Type ID",
        description="ID that refers to the active task type on server",
        default="",
    )

    def get_task_type_via_name(self):
        return get_safely_string_prop(self, "task_type_active_name")

    def set_task_type_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_task_types_enum_for_current_context(self, bpy.context),
            name_prop='task_type_active_name',
            id_prop='task_type_active_id',
        )
        if key:
            cache.task_type_active_set_by_id(bpy.context, key)
        else:
            cache.task_type_active_reset_entity()
        return

    def get_task_type_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_task_types_enum_for_current_context(self, bpy.context))

    task_type_active_name: bpy.props.StringProperty(
        name="Task Type",
        description="Active Task Type Name",
        default="",  # type: ignore
        get=get_task_type_via_name,
        set=set_task_type_via_name,
        options=set(),
        search=get_task_type_search_list,
    )

    category: bpy.props.EnumProperty(  # type: ignore
        name="Type",
        description="Kitsu entity type",
        items=(
            ("ASSET", "Asset", "Asset related tasks", 0),
            ("SHOT", "Shot", "Shot related tasks", 1),
            ("SEQ", "Sequence", "Sequence related tasks", 2),
            ("EDIT", "Edit", "Edit related tasks", 3),
        ),
        default="SHOT",
        update=propsdata.reset_all_kitsu_props,
    )

    ############
    # Edit
    ############
    edit_active_id: bpy.props.StringProperty(  # type: ignore
        name="Active Edit ID",
        description="ID that refers to the active edit on server",
        default="",
    )

    def get_edit_via_name(self):
        return get_safely_string_prop(self, "edit_active_name")

    def set_edit_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_all_edits_enum_for_active_project(self, bpy.context),
            name_prop='edit_active_name',
            id_prop='edit_active_id',
        )
        if key:
            cache.edit_active_set_by_id(bpy.context, key)
        else:
            cache.edit_active_reset_entity()
        return

    def get_edit_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_all_edits_enum_for_active_project(self, bpy.context))

    edit_active_name: bpy.props.StringProperty(
        name="Edit",
        description="Active Edit Name",
        default="",  # type: ignore
        get=get_edit_via_name,
        set=set_edit_via_name,
        options=set(),
        search=get_edit_search_list,
        search_options={'SORT'},
    )

    edit_export_version: bpy.props.StringProperty(name="Version", default="v001")

    edit_export_file: bpy.props.StringProperty(  # type: ignore
        name="Edit Export Filepath",
        description="Output filepath of Edit Export",
        default="",
        subtype="FILE_PATH",
        get=propsdata.get_edit_export_file,
    )

    # Thumbnail props.
    task_type_thumbnail_id: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Task Type ID",
        description="ID that refers to the task type on server for which thumbnails will be uploaded",
        default="",
    )

    task_type_thumbnail_name: bpy.props.StringProperty(  # type: ignore
        name="Thumbnail Task Type Name",
        description="Name that refers to the task type on server for which thumbnails will be uploaded",
        default="",
    )

    # Sqe render props.
    task_type_sqe_render_id: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type ID",
        description="ID that refers to the task type on server for which the sqe render will be uploaded",
        default="",
    )

    task_type_sqe_render_name: bpy.props.StringProperty(  # type: ignore
        name="Sqe Render Task Type Name",
        description="Name that refers to the task type on server for which the sqe render will be uploaded",
        default="",
    )

    # Playblast props.

    playblast_version: bpy.props.StringProperty(name="Version", default="v001")

    playblast_dir: bpy.props.StringProperty(  # type: ignore
        name="Playblast Directory",
        description="Directory in which playblasts will be saved",
        default="",
        subtype="DIR_PATH",
        get=propsdata.get_playblast_dir,
    )

    playblast_file: bpy.props.StringProperty(  # type: ignore
        name="Playblast Filepath",
        description="Output filepath of playblast",
        default="",
        subtype="FILE_PATH",
        get=propsdata.get_playblast_file,
    )

    playblast_task_status_id: bpy.props.StringProperty(  # type: ignore
        name="Plablast Task Status ID",
        description="ID that refers to the task status on server which the playblast will set",
        default="",
    )

    playblast_render_mode: bpy.props.EnumProperty(  # type: ignore
        name="Playblast Render Mode",
        description="Choose to either Render Playblast from current Viewport or use scene's render settings",
        items=[
            (
                "SCENE",
                "Scene",
                "Render using the scene's render settings, playblast will match 'Render Animation's' output exactly",
            ),
            (
                "VIEWPORT",
                "Viewport",
                "Render from the current viewport, with viewport shading settings and viewport overlays; what you see is what you get",
            ),
            (
                "VIEWPORT_PRESET",
                "Viewport with Preset Shading",
                "Render from the current viewport with Add-On's default shading settings, and automatically hide all overlays",
            ),
        ],
    )

    # Sequence editor tools.
    pull_edit_channel: bpy.props.IntProperty(
        name="Channel",
        description="On which channel the operator will create the color strips",
        default=1,
        min=1,
        max=32,
    )

    sequence_colors: bpy.props.CollectionProperty(type=KITSU_sequence_colors)


class KITSU_property_group_error(bpy.types.PropertyGroup):
    """"""

    frame_range: bpy.props.BoolProperty(  # type: ignore
        name="Frame Range Error",
        description="Indicates if the scene frame range does not match the one in Kitsu",
        default=False,
    )


class KITSU_property_group_window_manager(bpy.types.PropertyGroup):
    """"""

    tasks_index: bpy.props.IntProperty(name="Tasks Index", default=0)

    quick_duplicate_amount: bpy.props.IntProperty(
        name="Amount",
        default=1,
        min=1,
        description="Specifies the number of copies that will be created",
    )

    def clear(self):
        pass


def _add_window_manager_props():
    # Multi Edit Properties.
    bpy.types.WindowManager.show_advanced = bpy.props.BoolProperty(
        name="Show Advanced",
        description="Shows advanced options to fine control shot pattern",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_seq = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom sequence name for <Sequence> wildcard",
        default=False,
    )

    bpy.types.WindowManager.var_use_custom_project = bpy.props.BoolProperty(
        name="Use Custom",
        description="Enables to type in custom project name for <Project> wildcard",
        default=False,
    )

    bpy.types.WindowManager.var_sequence_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Sequence Variable",
        description="Value that will be used to insert in <Sequence> wildcard if custom sequence is enabled",
        default="",
    )

    bpy.types.WindowManager.var_project_custom = bpy.props.StringProperty(  # type: ignore
        name="Custom Project Variable",
        description="Value that will be used to insert in <Project> wildcard if custom project is enabled",
        default="",
    )

    bpy.types.WindowManager.shot_counter_start = bpy.props.IntProperty(
        description="Value that defines where the shot counter starts",
        step=10,
        min=0,
    )

    bpy.types.WindowManager.shot_preview = bpy.props.StringProperty(
        name="Shot Pattern",
        description="Preview result of current settings on how a shot will be named",
        get=propsdata._gen_shot_preview,
    )

    bpy.types.WindowManager.var_project_active = bpy.props.StringProperty(
        name="Active Project",
        description="Value that will be inserted in <Project> wildcard",
        get=propsdata._get_project_active,
    )

    ###########
    # Sequence
    ###########
    bpy.types.WindowManager.selected_sequence_id = bpy.props.StringProperty(  # type: ignore
        name="Active Sequence ID",
        description="ID that refers to the active sequence on server",
        default="",
    )

    def get_sequences_via_name(self):
        return get_safely_string_prop(self, "selected_sequence_name")

    def set_sequences_via_name(self, input):
        key = set_kitsu_entity_id_via_enum_name(
            self=self,
            input_name=input,
            items=cache.get_sequences_enum_list(self, bpy.context),
            name_prop='selected_sequence_name',
            id_prop='selected_sequence_id',
        )
        if key:
            cache.sequence_active_set_by_id(bpy.context, key)
        else:
            cache.sequence_active_reset_entity()
        return

    def get_sequence_search_list(self, context, edit_text):
        return get_enum_item_names(cache.get_sequences_enum_list(self, bpy.context))

    bpy.types.WindowManager.selected_sequence_name = bpy.props.StringProperty(
        name="Sequence",
        description="Name of Sequence the generated Shots will be assinged to",
        default="",  # type: ignore
        get=get_sequences_via_name,
        set=set_sequences_via_name,
        options=set(),
        search=get_sequence_search_list,
        search_options={'SORT'},
    )

    # Advanced delete props.
    bpy.types.WindowManager.advanced_delete = bpy.props.BoolProperty(
        name="Advanced Delete",
        description="Checkbox to show advanced shot deletion operations",
        default=False,
    )


def _clear_window_manager_props():
    del bpy.types.WindowManager.show_advanced
    del bpy.types.WindowManager.var_use_custom_seq
    del bpy.types.WindowManager.var_use_custom_project
    del bpy.types.WindowManager.var_sequence_custom
    del bpy.types.WindowManager.var_project_custom
    del bpy.types.WindowManager.shot_counter_start
    del bpy.types.WindowManager.shot_preview
    del bpy.types.WindowManager.var_project_active
    del bpy.types.WindowManager.selected_sequence_id
    del bpy.types.WindowManager.selected_sequence_name


def _calc_kitsu_3d_start(self):
    """
    Calculates strip.kitsu_3d_start, little hack because it seems like we cant access the strip from a property group
    But we need acess to seqeuence properties.
    """

    prefs = util.addon_prefs_get(bpy.context)
    return int(self.frame_final_start - self.frame_start + prefs.shot_builder_frame_offset)


def _calc_kitsu_frame_end(self):
    """
    Calculates strip.kitsu_frame_end, little hack because it seems like we cant access the strip from a property group
    But we need acess to seqeuence properties.
    """
    frame_start = _calc_kitsu_3d_start(self)
    frame_end_final = frame_start + (self.frame_final_duration - 1)
    return int(frame_end_final)


def _get_frame_final_duration(self):
    return self.frame_final_duration


def _get_strip_filepath(self):
    return self.filepath


@persistent
def update_sequence_colors_coll_prop(dummy: Any) -> None:
    sqe = bpy.context.scene.sequence_editor
    if not sqe:
        return
    strips = sqe.strips_all
    strip_colors = bpy.context.scene.kitsu.sequence_colors
    existing_strip_ids: List[str] = []

    # Append missing sequences to scene.kitsu.seqeuence_colors.
    for seq in strips:
        if not seq.kitsu.sequence_id:
            continue

        if seq.kitsu.sequence_id not in strip_colors.keys():
            logger.info("Added %s to scene.kitsu.seqeuence_colors", seq.kitsu.sequence_name)
            item = strip_colors.add()
            item.name = seq.kitsu.sequence_id

        existing_strip_ids.append(seq.kitsu.sequence_id)

    # Delete sequence colors that are not in edit anymore.
    existing_strip_ids = set(existing_strip_ids)

    to_be_removed = [strip_id for strip_id in strip_colors.keys() if strip_id not in existing_strip_ids]

    for seq_id in to_be_removed:
        idx = strip_colors.find(seq_id)
        if idx == -1:
            continue

        strip_colors.remove(idx)
        logger.info(
            "Removed %s from scene.kitsu.seqeuence_colors. Is not used in the sequence editor anymore",
            seq_id,
        )


# ----------------REGISTER--------------.

classes = [
    KITSU_sequence_colors,
    KITSU_property_group_sequence,
    KITSU_property_group_scene,
    KITSU_property_group_error,
    KITSU_property_group_window_manager,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # FRAME RANGE PROPERTIES
    # because we cant acess strip properties from a sequence group we need to create this properties
    # directly on the strip, as we need strip properties to calculate
    bpy.types.Strip.kitsu_3d_start = bpy.props.IntProperty(
        name="3D In",
        get=_calc_kitsu_3d_start,
    )

    bpy.types.Strip.kitsu_frame_end = bpy.props.IntProperty(
        name="3D Out",
        get=_calc_kitsu_frame_end,
    )
    bpy.types.Strip.kitsu_frame_duration = bpy.props.IntProperty(
        name="Duration",
        get=_get_frame_final_duration,
    )

    # Used in general tools panel next to sqe_change_strip_source operator.
    bpy.types.MovieStrip.filepath_display = bpy.props.StringProperty(
        name="Filepath Display", get=_get_strip_filepath
    )

    # Sequence Properties.
    bpy.types.Strip.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_sequence,
        description="Metadata that is required for blender_kitsu",
    )

    # Scene Properties.
    bpy.types.Scene.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_scene,
        description="Metadata that is required for blender_kitsu",
    )
    # Window Manager.
    bpy.types.WindowManager.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_window_manager,
        description="Metadata that is required for blender_kitsu",
    )

    # Error Properties.
    bpy.types.Scene.kitsu_error = bpy.props.PointerProperty(
        name="Kitsu Error",
        type=KITSU_property_group_error,
        description="Error property group",
    )

    # Window Manager Properties.
    _add_window_manager_props()

    # Handlers.
    bpy.app.handlers.load_post.append(update_sequence_colors_coll_prop)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Clear properties.
    _clear_window_manager_props()

    # Handlers.
    bpy.app.handlers.load_post.remove(update_sequence_colors_coll_prop)
