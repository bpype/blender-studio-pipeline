# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import shutil
from .. import bkglobals
from pathlib import Path
from typing import List, Any, Tuple, Set, cast
from .. import prefs, cache
from . import core, config
from ..context import core as context_core

from ..edit.core import edit_export_import_latest
from .file_save import save_shot_builder_file
from .template import replace_workspace_with_template
from .assets import get_shot_assets
from .hooks import Hooks

active_project = None


def get_shots_for_seq(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    if self.seq_id != '':
        seq = active_project.get_sequence(self.seq_id)
        shot_enum = cache.get_shots_enum_for_seq(self, context, seq)
        if shot_enum != []:
            return shot_enum
    return [('NONE', "No Shots Found", '')]


def get_tasks_for_shot(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    global active_project
    if not (self.shot_id == '' or self.shot_id == 'NONE'):
        shot = active_project.get_shot(self.shot_id)
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


class KITSU_OT_build_new_shot(bpy.types.Operator):
    bl_idname = "kitsu.build_new_shot"
    bl_label = "Build New Shot"
    bl_description = "Build a New Shot file, based on infromation from KITSU Server"
    bl_options = {"REGISTER"}

    _timer = None
    _built_shot = False
    _add_vse_area = False
    _file_path = ''
    _current_kitsu_context = ""
    production_name: bpy.props.StringProperty(  # type: ignore
        name="Production",
        description="Name of the production to create a shot file for",
        options=set(),
    )

    save_file: bpy.props.BoolProperty(
        name="Save after building.",
        description="Automatically save build file after 'Shot Builder' is complete.",
        default=True,
    )

    def draw(self, context: bpy.types.Context) -> None:
        global active_project
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
        if active_project.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, col)
        context_core.draw_sequence_selector(context, col)
        context_core.draw_shot_selector(context, col)
        context_core.draw_task_type_selector(context, col)
        col.prop(self, "save_file")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        global active_project

        # Temporarily change kitsu context to shit
        self._current_kitsu_context = context.scene.kitsu.category
        context.scene.kitsu.category = "SHOT"

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        project = cache.project_active_get()
        active_project = project

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
                "Operator is not able to determine the project root directory. \nCheck project root directiory is configured in 'Blender Kitsu' addon preferences.",
            )
            return {'CANCELLED'}

        self.production_name = project.name

        return cast(Set[str], context.window_manager.invoke_props_dialog(self, width=400))

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

    def cancel(self, context: bpy.types.Context):
        # Restore kitsu context if cancelled
        context.scene.kitsu.category = self._current_kitsu_context

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
            self.report({'ERROR'}, F"Shot {shot.name} is missing frame range data on Kitsu Server")
            return {'CANCELLED'}

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
            get_shot_assets(scene=scene, output_collection=output_col, shot=shot)

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
                return {"FINISHED"}

        self.report({"INFO"}, f"Successfully Built Shot:`{shot.name}` Task: `{task_type.name}`")
        return {"FINISHED"}


classes = [
    KITSU_OT_build_new_shot,
    KITSU_OT_build_config_save_hooks,
    KITSU_OT_build_config_save_settings,
    KITSU_OT_build_config_save_templates,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
