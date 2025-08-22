# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import shutil
from .. import bkglobals, prefs, cache
from pathlib import Path
from typing import List, Any, Tuple, Set, cast
from . import core, config
from ..context import core as context_core

from ..edit.core import edit_export_import_latest
from .file_save import save_shot_builder_file
from .template import replace_workspace_with_template
from .assets import get_shot_assets
from .hooks import Hooks

ACTIVE_PROJECT = None


def get_shots_for_seq(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    if self.seq_id != '':
        seq = ACTIVE_PROJECT.get_sequence(self.seq_id)
        shot_enum = cache.get_shots_enum_for_seq(self, context, seq)
        if shot_enum != []:
            return shot_enum
    return [('NONE', "No Shots Found", '')]


def get_tasks_for_shot(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global ACTIVE_PROJECT
    if not (self.shot_id == '' or self.shot_id == 'NONE'):
        shot = ACTIVE_PROJECT.get_shot(self.shot_id)
        task_enum = cache.get_shot_task_types_enum_for_shot(self, context, shot)
        if task_enum != []:
            return task_enum
    return [('NONE', "No Tasks Found", '')]


class KITSU_OT_build_config_base_class(bpy.types.Operator):
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        if not prefs.session_auth(context):
            cls.poll_message_set("Login to a Kitsu Server")
        if not cache.project_active_get():
            cls.poll_message_set("Select an active project")
            return False
        if not addon_prefs.is_project_root_valid:
            cls.poll_message_set(
                "Check project root directory is configured in 'Blender Kitsu' addon preferences."
            )
            return False
        return True


class KITSU_OT_build_config_save_hooks(KITSU_OT_build_config_base_class):
    bl_idname = "kitsu.build_config_save_hooks"
    bl_label = "Save Shot Builder Hook File"
    bl_description = "Save hook.py file to `your_project_name/svn/pro/config/shot_builder` directory. Hooks are used to customize shot builder behaviour."

    def execute(self, context: bpy.types.Context):
        hooks_target_filepath = config.filepath_get(bkglobals.BUILD_HOOKS_FILENAME)
        if hooks_target_filepath.exists():
            self.report(
                {'WARNING'},
                f"{hooks_target_filepath.name} already exists, cannot overwrite",
            )
            return {'CANCELLED'}

        hooks_example = config.example_filepath_get(bkglobals.BUILD_HOOKS_FILENAME)
        if not hooks_example.exists():
            self.report(
                {'ERROR'},
                f"Cannot find {hooks_target_filepath.name} example file",
            )
            return {'CANCELLED'}

        config.copy_json_file(hooks_example, hooks_target_filepath)
        self.report({'INFO'}, f"Hook File saved to {str(hooks_target_filepath)}")
        return {'FINISHED'}


class KITSU_OT_build_config_save_settings(KITSU_OT_build_config_base_class):
    bl_idname = "kitsu.build_config_save_settings"
    bl_label = "Save Shot Builder Settings File"
    bl_description = "Save settings.json file to `your_project_name/svn/pro/config/shot_builder` Config are used to customize shot builder behaviour."

    def execute(self, context: bpy.types.Context):
        settings_target_filepath = config.filepath_get(bkglobals.BUILD_SETTINGS_FILENAME)
        if settings_target_filepath.exists():
            self.report(
                {'WARNING'},
                f"{settings_target_filepath.name} already exists, cannot overwrite",
            )
            return {'CANCELLED'}

        settings_example = config.example_filepath_get(bkglobals.BUILD_SETTINGS_FILENAME)
        if not settings_example.exists():
            self.report(
                {'ERROR'},
                "Cannot find example settings file",
            )
            return {'CANCELLED'}

        config.copy_json_file(settings_example, settings_target_filepath)
        self.report({'INFO'}, f"Settings File saved to {str(settings_target_filepath)}")
        return {'FINISHED'}


class KITSU_OT_build_config_save_templates(KITSU_OT_build_config_base_class):
    bl_idname = "kitsu.build_config_save_templates"
    bl_label = "Create Shot Builder Template Files"
    bl_description = (
        "Save template files for shot builder in config directory."
        "Templates are used to customize the workspaces for each per task type"
        "Template names match each task type found on Kitsu Server"
    )

    def execute(self, context: bpy.types.Context):
        source_dir = config.template_example_dir_get()
        target_dir = config.template_dir_get()

        # Ensure Target Directory Exists
        target_dir.mkdir(parents=True, exist_ok=True)

        source_files = list(source_dir.glob('*.blend')) + list(source_dir.glob('*.md'))
        for source_file in source_files:
            target_file = target_dir.joinpath(source_file.name)
            if target_file.exists():
                print(f"Cannot overwrite file {str(target_file)}")
                continue
            shutil.copy2(source_file, target_dir.joinpath(source_file.name))

        self.report({'INFO'}, f"Saved template files to {str(target_dir)}")
        return {'FINISHED'}


class KITSU_OT_build_new_file_baseclass(bpy.types.Operator):
    bl_idname = "kitsu.build_new_file"
    bl_label = "Build New File"
    bl_description = "Build a new file based on the current context and save it"
    bl_options = {"REGISTER"}

    _kitsu_context_type = ""  # Default context for this operator
    _current_kitsu_context = ""

    production_name: bpy.props.StringProperty(  # type: ignore
        name="Production",
        description="Name of the production to create a shot file for",
        options=set(),
    )

    save_file: bpy.props.BoolProperty(  # type:ignore
        name="Save after building.",
        description="Automatically save build file after 'Shot Builder' is complete.",
        default=True,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        global ACTIVE_PROJECT

        # Temporarily change kitsu context to asset
        self._current_kitsu_context = context.scene.kitsu.category
        context.scene.kitsu.category = self._kitsu_context_type

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        project = cache.project_active_get()
        ACTIVE_PROJECT = project

        if addon_prefs.session.is_auth() is False:
            self.report(
                {'ERROR'},
                "Must be logged into Kitsu to continue. \nCheck login status in 'Blender Kitsu' addon preferences.",
            )
            return {'CANCELLED'}

        if project.id == "":
            self.report(
                {'ERROR'},
                "Operator is not able to determine the Kitsu production's name. \nCheck project is selected in 'Blender Kitsu' addon preferences.",
            )
            return {'CANCELLED'}

        if not addon_prefs.is_project_root_valid:
            self.report(
                {'ERROR'},
                "Operator is not able to determine the project root directory. \nCheck project root directory is configured in 'Blender Kitsu' addon preferences.",
            )
            return {'CANCELLED'}

        self.production_name = project.name

        return cast(Set[str], context.window_manager.invoke_props_dialog(self, width=400))

    def cancel(self, context: bpy.types.Context):
        # Restore kitsu context if cancelled
        context.scene.kitsu.category = self._current_kitsu_context


class KITSU_OT_build_new_asset(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.build_new_asset"
    bl_label = "Build New Asset"
    bl_description = "Build a New Asset file, based on project data from Kitsu Server"
    bl_options = {"REGISTER"}

    _kitsu_context_type = "ASSET"  # Default context for this operator

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        row = col.row()
        row.enabled = False
        row.prop(self, "production_name")

        context_core.draw_asset_type_selector(context, col)
        context_core.draw_asset_selector(context, col)
        col.prop(self, "save_file")

    def execute(self, context: bpy.types.Context):
        # Get Properties
        scene = context.scene
        asset_type = cache.asset_type_active_get()
        asset = cache.asset_active_get()

        if asset_type.id == "" or asset.id == "":
            self.report({'ERROR'}, "Please select a asset type and asset to build a shot file")
            return {'CANCELLED'}

        asset_file_path_str = asset.get_filepath(context)

        replace_workspace_with_template(context, "Asset")

        # Remove All Collections from Scene
        for collection in context.scene.collection.children:
            context.scene.collection.children.unlink(collection)
            bpy.data.collections.remove(collection)

        # Remove All Objects from Scene
        for object in context.scene.objects:
            context.scene.objects.unlink(object)
            bpy.data.objects.remove(object)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        asset_collection = bpy.data.collections.new(asset.get_collection_name())
        context.scene.collection.children.link(asset_collection)

        # Set Kitsu Context
        scene.kitsu.category = "ASSET"
        scene.kitsu.asset_type_active_name = asset_type.name
        scene.kitsu.asset_active_name = asset.name
        scene.kitsu.asset_col = asset_collection

        relative_path = Path(asset_file_path_str).relative_to(prefs.project_root_dir_get(context))
        asset.set_asset_path(str(relative_path), asset_collection.name)

        # Save File
        if self.save_file:
            if not save_shot_builder_file(file_path=asset_file_path_str):
                self.report(
                    {"WARNING"},
                    f"Failed to save file at path `{asset_file_path_str}`",
                )
                return {"FINISHED"}

        self.report({"INFO"}, f"Successfully Built Shot:`{asset.name}`")
        return {"FINISHED"}


class KITSU_OT_open_asset_file(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.open_asset_file"
    bl_label = "Open Asset File"
    bl_description = "Open an Asset File from the current project"

    _kitsu_context_type = "ASSET"

    save_current: bpy.props.BoolProperty(  # type: ignore
        name="Save Current File",
        description="Automatically save the current file before opening a new one.",
        default=True,
    )

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        row = col.row()
        row.enabled = False
        row.prop(self, "production_name")
        context_core.draw_asset_type_selector(context, col)
        context_core.draw_asset_selector(context, col)

        if bpy.data.is_dirty:
            col.prop(self, "save_current")

    def execute(self, context: bpy.types.Context):
        asset = cache.asset_active_get()
        asset_file_path_str = asset.get_filepath(context)
        if not Path(asset_file_path_str).exists():
            self.report({'ERROR'}, f"Asset file does not exist: {asset_file_path_str}")
            return {'CANCELLED'}

        if bpy.data.is_dirty and self.save_current:
            error_msg = core.save_current_file()

            if error_msg:
                self.report({'ERROR'}, error_msg)
                return {"CANCELLED"}

        bpy.ops.wm.open_mainfile(filepath=asset_file_path_str)
        return {'FINISHED'}


class KITSU_OT_build_new_shot(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.build_new_shot"
    bl_label = "Build New Shot"
    bl_description = "Build a New Shot file, based on project information found on Kitsu Server"
    bl_options = {"REGISTER"}

    _kitsu_context_type = "SHOT"

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        row = col.row()
        row.enabled = False
        row.prop(self, "production_name")
        if ACTIVE_PROJECT.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, col)
        context_core.draw_sequence_selector(context, col)
        context_core.draw_shot_selector(context, col)
        context_core.draw_task_type_selector(context, col)
        col.prop(self, "save_file")

    def _get_task_type_for_shot(self, context, shot):
        for task_type in shot.get_all_task_types():
            if task_type.id == self.task_type:
                return task_type

    def _frame_range_invalid(self, context, shot) -> bool:
        if not (getattr(shot, "data") or getattr(shot, "nb_frames")):
            return True

        try:
            shot.data.get("frame_in")
        except AttributeError:
            return True

    def execute(self, context: bpy.types.Context):
        # Get Properties
        active_project = cache.project_active_get()
        seq = cache.sequence_active_get()
        shot = cache.shot_active_get()
        task_type = cache.task_type_active_get()
        config.settings_load()

        if seq.id == "" or shot.id == "" or task_type.id == "":
            self.report(
                {'ERROR'}, "Please select a sequence, shot and task type to build a shot file"
            )
            return {'CANCELLED'}

        if self._frame_range_invalid(context, shot):
            self.report(
                {'WARNING'}, F"Shot {shot.name} is missing frame range data on Kitsu Server"
            )

        task_type_short_name = task_type.get_short_name()
        shot_file_path_str = shot.get_filepath(context, task_type_short_name)

        # Open Template File
        replace_workspace_with_template(context, task_type.name)

        # Set Up Scene + Naming
        shot_task_name = shot.get_task_name(task_type.get_short_name())
        scene = core.set_shot_scene(context, shot_task_name)
        core.remove_all_data()
        core.set_resolution_and_fps(active_project, scene)
        core.set_frame_range(shot, scene)

        # Set Render Settings
        if task_type_short_name == 'anim':  # TODO get anim from a constant instead
            core.set_render_engine(context.scene, 'BLENDER_WORKBENCH')
        else:
            core.set_render_engine(context.scene)

        # Create Output Collection & Link Camera
        if config.OUTPUT_COL_CREATE.get(task_type_short_name):
            output_col = core.create_task_type_output_collection(context.scene, shot, task_type)
        if task_type_short_name == 'anim' or task_type_short_name == 'layout':
            core.link_camera_rig(context.scene, output_col)

            # Load Assets
            _, fail_links = get_shot_assets(scene=scene, output_collection=output_col, shot=shot)

        # Link External Output Collections
        core.link_task_type_output_collections(shot, task_type)

        if config.LOAD_EDITORIAL_REF.get(task_type_short_name):
            edit_export_import_latest(context, shot)

        # Run Hooks
        hooks_instance = Hooks()
        hooks_instance.load_hooks(context)
        hooks_instance.execute_hooks(
            match_task_type=task_type_short_name,
            scene=context.scene,
            shot=shot,
            prod_path=prefs.project_root_dir_get(context),
            shot_path=shot_file_path_str,
        )

        # Set Kitsu Context
        scene.kitsu.category = "SHOT"
        scene.kitsu.sequence_active_name = seq.name
        scene.kitsu.shot_active_name = shot.name
        scene.kitsu.task_type_active_name = task_type.name

        # Save File
        if self.save_file:
            if not save_shot_builder_file(file_path=shot_file_path_str):
                self.report(
                    {"WARNING"},
                    f"Failed to save file at path `{shot_file_path_str}`",
                )

        if len(fail_links) > 0:
            msg = ""
            for fail_msg in fail_links:
                msg += fail_msg + "\n"

            self.report({"WARNING"}, msg)
            self.report({"WARNING"}, f"Failed to link '{len(fail_links)}' Assets")
        else:
            self.report({"INFO"}, f"Successfully Built Shot:`{shot.name}` Task: `{task_type.name}`")
        return {"FINISHED"}


class KITSU_OT_open_shot_file(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.open_shot_file"
    bl_label = "Open Shot File"
    bl_description = "Open a Shot File from the current project"

    _kitsu_context_type = "SHOT"

    save_current: bpy.props.BoolProperty(  # type: ignore
        name="Save Current File",
        description="Automatically save the current file before opening a new one.",
        default=True,
    )

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        row = col.row()
        row.enabled = False
        row.prop(self, "production_name")
        if ACTIVE_PROJECT.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, col)
        context_core.draw_sequence_selector(context, col)
        context_core.draw_shot_selector(context, col)
        context_core.draw_task_type_selector(context, col)

        if bpy.data.is_dirty:
            col.prop(self, "save_current")

    def execute(self, context: bpy.types.Context):
        shot = cache.shot_active_get()
        task_type = cache.task_type_active_get()

        task_type_short_name = task_type.get_short_name()
        shot_file_path_str = shot.get_filepath(context, task_type_short_name)
        if not Path(shot_file_path_str).exists():
            self.report({'ERROR'}, f"Shot file does not exist: {shot_file_path_str}")
            return {'CANCELLED'}

        if bpy.data.is_dirty and self.save_current:
            error_msg = core.save_current_file()

            if error_msg:
                self.report({'ERROR'}, error_msg)
                return {"CANCELLED"}

        bpy.ops.wm.open_mainfile(filepath=shot_file_path_str)
        return {'FINISHED'}


class KITSU_OT_create_edit_file(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.create_edit_file"
    bl_label = "Create Edit File"
    bl_description = "Create a new .blend file for editing using Blender's Video Editing template"

    _edit_entity = None
    _production_name = None
    _kitsu_context_type = "EDIT"

    create_kitsu_edit: bpy.props.BoolProperty(  # type: ignore
        name="Create Kitsu Edit if none exists.",
        description="Automatically create a Kitsu edit for the edit.",
        default=True,
    )

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        if ACTIVE_PROJECT.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, layout)
        layout.prop(self, "create_kitsu_edit")
        layout.prop(self, "save_file")

    def execute(self, context):
        scene = context.scene
        active_project = cache.project_active_get()
        self._edit_entity = cache.edit_default_get(
            create=self.create_kitsu_edit, episode_id=context.scene.kitsu.episode_active_id
        )
        self._edit_entity.set_edit_task()
        task_type = self._edit_entity.get_task_type()

        if not self._edit_entity:
            self.report({'ERROR'}, "Failed to create Kitsu edit entity.")
            return {'CANCELLED'}

        edit_file_path_str = self._edit_entity.get_filepath(context)

        # Create a new file using the Video Editing template
        replace_workspace_with_template(context, task_type.name)
        core.set_resolution_and_fps(active_project, scene)

        cache.reset_all_edits_enum_for_active_project()

        scene.kitsu.category = "EDIT"
        scene.kitsu.edit_active_name = context_core.get_versioned_file_basename(
            Path(edit_file_path_str).stem
        )
        scene.kitsu.task_type_active_name = bkglobals.EDIT_TASK_TYPE

        # Save File
        if self.save_file:
            if not save_shot_builder_file(file_path=edit_file_path_str):
                self.report(
                    {"WARNING"},
                    f"Failed to save file at path `{edit_file_path_str}`",
                )
                return {"FINISHED"}

        self.report({'INFO'}, f"Created edit file at {edit_file_path_str}")

        return {'FINISHED'}


class KITSU_OT_open_edit_file(KITSU_OT_build_new_file_baseclass):
    bl_idname = "kitsu.open_edit_file"
    bl_label = "Open Edit File"
    bl_description = "Open Latest Edit File from the current project"

    _kitsu_context_type = "EDIT"

    save_current: bpy.props.BoolProperty(  # type: ignore
        name="Save Current File",
        description="Automatically save the current file before opening a new one.",
        default=True,
    )

    def draw(self, context: bpy.types.Context) -> None:
        global ACTIVE_PROJECT
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        row = col.row()
        row.enabled = False
        row.prop(self, "production_name")
        if ACTIVE_PROJECT.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, col)
        context_core.draw_edit_selector(context, col)

        if bpy.data.is_dirty:
            col.prop(self, "save_current")

    def execute(self, context: bpy.types.Context):
        edit_entity = cache.edit_default_get(episode_id=context.scene.kitsu.episode_active_id)
        if not edit_entity:
            self.report({'ERROR'}, "No edit task found on Kitsu Server.")
            return {'CANCELLED'}

        edit_file_path_str = edit_entity.get_filepath(context)
        if not Path(edit_file_path_str).exists():
            self.report({'ERROR'}, f"Edit file does not exist: {edit_file_path_str}")
            return {'CANCELLED'}

        if bpy.data.is_dirty and self.save_current:
            error_msg = core.save_current_file()

            if error_msg:
                self.report({'ERROR'}, error_msg)
                return {"CANCELLED"}

        bpy.ops.wm.open_mainfile(filepath=edit_file_path_str)
        return {'FINISHED'}


classes = [
    KITSU_OT_build_new_shot,
    KITSU_OT_build_new_asset,
    KITSU_OT_build_config_save_hooks,
    KITSU_OT_build_config_save_settings,
    KITSU_OT_build_config_save_templates,
    KITSU_OT_create_edit_file,
    KITSU_OT_open_edit_file,
    KITSU_OT_open_shot_file,
    KITSU_OT_open_asset_file,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
