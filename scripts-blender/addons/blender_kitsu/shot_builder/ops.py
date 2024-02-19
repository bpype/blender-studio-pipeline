import bpy
from .. import bkglobals
from pathlib import Path
from typing import List, Any, Tuple, Set, cast
from .. import prefs, cache
from .core import (
    set_render_engine,
    link_camera_rig,
    create_task_type_output_collection,
    set_shot_scene,
    set_resolution_and_fps,
    set_frame_range,
    link_task_type_output_collections,
    remove_all_data,
    get_shot_builder_hooks_dir,
)
from ..context import core as context_core

from ..edit.core import edit_render_import_latest
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


class KITSU_OT_save_shot_builder_hooks(bpy.types.Operator):
    bl_idname = "kitsu.save_shot_builder_hooks"
    bl_label = "Save Shot Builder Hook File"
    bl_description = "Save hook.py file to `your_project_name/svn/pro/config/shot_builder` directory. Hooks are used to customize shot builder behaviour."

    def execute(self, context: bpy.types.Context):
        addon_prefs = prefs.addon_prefs_get(context)
        project = cache.project_active_get()
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

        config_dir = get_shot_builder_hooks_dir(context)
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        hook_file_path = config_dir.joinpath("hooks.py")
        if hook_file_path.exists():
            self.report(
                {'WARNING'},
                "File already exists, cannot overwrite",
            )
            return {'CANCELLED'}

        config_dir = Path(__file__).parent
        example_hooks_path = config_dir.joinpath("hook_examples/hooks.py")
        if not example_hooks_path.exists():
            self.report(
                {'ERROR'},
                "Cannot find example hook file",
            )
            return {'CANCELLED'}

        with example_hooks_path.open() as source:
            # Read contents
            contents = source.read()

        # Write contents to target file
        with hook_file_path.open('w') as target:
            target.write(contents)
        self.report({'INFO'}, f"Hook File saved to {hook_file_path}")
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

    def cancel(self, context: bpy.types.Context):
        # Restore kitsu context if cancelled
        context.scene.kitsu.category = self._current_kitsu_context

    def execute(self, context: bpy.types.Context):
        # Get Properties
        global active_project
        seq = cache.sequence_active_get()
        shot = cache.shot_active_get()
        task_type = cache.task_type_active_get()

        if seq.id == "" or shot.id == "" or task_type.id == "":
            self.report(
                {'ERROR'}, "Please select a sequence, shot and task type to build a shot file"
            )
            return {'CANCELLED'}

        task_type_short_name = task_type.get_short_name()
        shot_file_path_str = shot.get_filepath(context, task_type_short_name)

        # Open Template File
        replace_workspace_with_template(context, task_type_short_name)

        # Set Up Scene + Naming
        shot_task_name = shot.get_task_name(task_type.get_short_name())
        scene = set_shot_scene(context, shot_task_name)
        remove_all_data()
        set_resolution_and_fps(active_project, scene)
        set_frame_range(shot, scene)

        # Set Render Settings
        if task_type_short_name == 'anim':  # TODO get anim from a constant instead
            set_render_engine(context.scene, 'BLENDER_WORKBENCH')
        else:
            set_render_engine(context.scene)

        # Create Output Collection & Link Camera
        if bkglobals.OUTPUT_COL_CREATE.get(task_type_short_name):
            output_col = create_task_type_output_collection(context.scene, shot, task_type)
        if task_type_short_name == 'anim' or task_type_short_name == 'layout':
            link_camera_rig(context.scene, output_col)

            # Load Assets
            get_shot_assets(scene=scene, output_collection=output_col, shot=shot)

        # Link External Output Collections
        link_task_type_output_collections(shot, task_type)

        if bkglobals.LOAD_EDITORIAL_REF.get(task_type_short_name):
            edit_render_import_latest(context, shot)

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


classes = (KITSU_OT_build_new_shot, KITSU_OT_save_shot_builder_hooks)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
