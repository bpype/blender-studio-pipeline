# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import webbrowser
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import time
import bpy
from bpy.app.handlers import persistent

from .. import bkglobals

from .. import (
    cache,
    util,
    prefs,
    bkglobals,
)
from ..logger import LoggerFactory
from ..types import (
    Shot,
    Task,
    TaskStatus,
    TaskType,
)
from ..playblast.core import (
    playblast_with_scene_settings,
    playblast_with_viewport_settings,
    playblast_with_viewport_preset_settings,
    playblast_vse,
)
from ..context import core as context_core
from ..playblast import opsdata, core

logger = LoggerFactory.getLogger()


class KITSU_OT_playblast_create(bpy.types.Operator):
    bl_idname = "kitsu.playblast_create"
    bl_label = "Create Playblast"
    bl_description = (
        "Creates render either from viewport in which operator was triggered"
        "or renderes with the current scene's render settings"
        "Saves the set version to disk and uploads it to Kitsu with the specified "
        "comment and task type."
        "Opens web browser or VSE after playblast if set in addon preferences"
    )

    comment: bpy.props.StringProperty(
        name="Comment",
        description="Comment that will be appended to this playblast on Kitsu",
        default="",
    )
    confirm: bpy.props.BoolProperty(name="Confirm", default=False)

    task_status: bpy.props.EnumProperty(items=cache.get_all_task_statuses_enum)  # type: ignore

    thumbnail_frame: bpy.props.IntProperty(
        name="Thumbnail Frame",
        description="Frame to use as the thumbnail on Kitsu",
        min=0,
    )
    thumbnail_frame_final: bpy.props.IntProperty(name="Thumbnail Frame Final")

    _entity = None
    _task_status = None
    _task = None
    _task_type = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            cls.poll_message_set("Not logged into Kitsu Server, see Add-On Preferences")
            return False

        if not context.scene.kitsu.playblast_file:
            cls.poll_message_set("Invalid Playblast File/Directory, see Add-On Preferences")
            return False

        if context.space_data.type == "VIEW_3D":
            if not context.scene.camera:
                cls.poll_message_set("No Active Camera in active Scene")
                return False

        if context_core.is_sequence_context():
            if not cache.sequence_active_get():
                cls.poll_message_set("No Active Sequence set in Kitsu Context UI")
                return False

        if context_core.is_shot_context():
            if not cache.shot_active_get():
                cls.poll_message_set("No Active Shot set in Kitsu Context UI")
                return False
        if not cache.task_type_active_get():
            cls.poll_message_set("No Active Task Type set in Kitsu Context UI")
            return False

        return True

    def is_vse(self, context):
        return bool(context.space_data.type == "SEQUENCE_EDITOR")

    def _get_kitsu_task(self, context: bpy.types.Context):
        task_type_name = cache.task_type_active_get().name

        # Get task status 'wip' and task type 'Animation'.
        self._task_status = TaskStatus.by_id(self.task_status)
        self._task_type = TaskType.by_name(task_type_name)

        if not self._task_type:
            raise RuntimeError("Failed to upload playblast. Task type missing on Kitsu Server")

        # Find / get latest task
        self._task = Task.by_name(self._entity, self._task_type)
        if not self._task:
            # An Entity on the server can have 0 tasks even tough task types exist.
            # We have to create a task first before being able to upload a thumbnail.
            try:
                self._task = Task.new_task(
                    self._entity, self._task_type, task_status=self._task_status
                )
            except TypeError:
                raise RuntimeError(
                    f"Failed to upload playblast. Task type {self._task_type.name} not present in {self._entity.type} {self._entity.name}"
                )

    def _get_user_name(self, context: bpy.types.Context) -> str:
        session = prefs.session_get(context)
        if len(self._task.persons) == 1:
            return self._task.persons[0]["full_name"]
        elif len(self._task.persons) >= 1:
            person = ""
            for index, user in enumerate(self._task.persons):
                person += user["full_name"]
                if index < len(self._task.persons) - 1:
                    person += ", "
            return person
        else:
            return session.data.user["full_name"]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        kitsu_scene_props = context.scene.kitsu
        render_mode = kitsu_scene_props.playblast_render_mode

        if not self.task_status:
            self.report({"ERROR"}, "Failed to create playblast. Missing task status")
            return {"CANCELLED"}

        # Playblast file always starts at frame 0, account for this in thumbnail frame selection
        self.thumbnail_frame_final = self.thumbnail_frame - context.scene.frame_start

        # Ensure thumbnail frame is not outside of frame range
        if self.thumbnail_frame_final not in range(
            0, (context.scene.frame_end - context.scene.frame_start) + 1
        ):
            self.report(
                {"ERROR"},
                f"Thumbnail frame '{self.thumbnail_frame}' is outside of frame range ",
            )
            return {"CANCELLED"}

        # entity is either a shot or a sequence
        self._entity = self._get_active_entity(context)

        # get kitsu task info
        self._get_kitsu_task(context)

        # Save playblast task status id for next time.
        kitsu_scene_props.playblast_task_status_id = self.task_status

        logger.info("-START- Creating Playblast")

        context.window_manager.progress_begin(0, 2)
        context.window_manager.progress_update(0)

        playblast_file = kitsu_scene_props.playblast_file

        username = self._get_user_name(context)

        # Render and save playblast
        if self.is_vse(context):
            output_path = playblast_vse(self, context, playblast_file)
        else:
            if render_mode == "VIEWPORT":
                output_path = playblast_with_viewport_settings(
                    self, context, playblast_file, username
                )
            elif render_mode == "VIEWPORT_PRESET":
                output_path = playblast_with_viewport_preset_settings(
                    self, context, playblast_file, username
                )
            else:  #  render_mode == "SCENE":
                output_path = playblast_with_scene_settings(self, context, playblast_file, username)

        context.window_manager.progress_update(1)

        # Upload playblast
        self._upload_playblast(context, output_path)

        if not addon_prefs.version_control:
            basename = context_core.get_versioned_file_basename(Path(bpy.data.filepath).stem)

            version_filename = basename + "-" + kitsu_scene_props.playblast_version + ".blend"
            version_filepath = Path(bpy.data.filepath).parent.joinpath(version_filename).as_posix()
            bpy.ops.wm.save_as_mainfile(filepath=version_filepath, copy=True)

        context.window_manager.progress_update(2)
        context.window_manager.progress_end()

        self.report({"INFO"}, f"Created and uploaded playblast for {self._entity.name}")
        logger.info("-END- Creating Playblast")

        # Redraw UI
        util.ui_redraw()

        # Post playblast

        # Open web browser
        if addon_prefs.pb_open_webbrowser:
            self._open_webbrowser()

        # Open playblast in second scene video sequence editor.
        if addon_prefs.pb_open_vse:
            # Create new scene.
            scene_orig = bpy.context.scene
            try:
                scene_pb = bpy.data.scenes[bkglobals.SCENE_NAME_PLAYBLAST]
            except KeyError:
                # Create scene.
                bpy.ops.scene.new(type="EMPTY")  # changes active scene
                scene_pb = bpy.context.scene
                scene_pb.name = bkglobals.SCENE_NAME_PLAYBLAST

                logger.info(
                    "Created new scene for playblast playback: %s", scene_pb.name
                )
            else:
                logger.info(
                    "Use existing scene for playblast playback: %s", scene_pb.name
                )
                # Change scene.
                context.window.scene = scene_pb

            # Init video sequence editor.
            if not context.scene.sequence_editor:
                context.scene.sequence_editor_create()  # what the hell

            # Setup video sequence editor space.
            if "Video Editing" not in [ws.name for ws in bpy.data.workspaces]:
                scripts_path = bpy.utils.script_paths(use_user=False)[0]
                template_path = (
                    "/startup/bl_app_templates_system/Video_Editing/startup.blend"
                )
                ws_filepath = Path(scripts_path + template_path)
                bpy.ops.workspace.append_activate(
                    idname="Video Editing",
                    filepath=ws_filepath.as_posix(),
                )
            else:
                context.window.workspace = bpy.data.workspaces["Video Editing"]

            # Add movie strip
            # load movie strip file in sequence editor
            # in this case we make use of ops.sequencer.movie_strip_add because
            # it provides handy auto placing,would be hard to achieve with
            # context.scene.sequence_editor.sequences.new_movie().
            override = context.copy()
            for window in bpy.context.window_manager.windows:
                screen = window.screen

                for area in screen.areas:
                    if area.type == "SEQUENCE_EDITOR":
                        override["window"] = window
                        override["screen"] = screen
                        override["area"] = area

            bpy.ops.sequencer.movie_strip_add(
                override,
                filepath=scene_orig.kitsu.playblast_file,
                frame_start=context.scene.frame_start,
            )

            # Playback.
            context.scene.frame_current = context.scene.frame_start
            bpy.ops.screen.animation_play()

        return {"FINISHED"}

    def invoke(self, context, event):
        # Initialize comment and playblast task status variable.
        self.comment = ""

        prev_task_status_id = context.scene.kitsu.playblast_task_status_id

        if context.scene.frame_current not in range(
            context.scene.frame_start, context.scene.frame_end
        ):
            context.scene.frame_current = context.scene.frame_start

        self.thumbnail_frame = context.scene.frame_current

        # Only use prev_task_status_id if it exists in the task statuses enum list
        valid_ids = [status[0] for status in cache.get_all_task_statuses_enum(self, context)]
        if prev_task_status_id in valid_ids:
            self.task_status = prev_task_status_id
        else:
            # Find todo.
            todo_status = TaskStatus.by_name(bkglobals.PLAYBLAST_DEFAULT_STATUS)
            if todo_status:
                self.task_status = todo_status.id

        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "task_status", text="Status")
        layout.prop(self, "comment")
        layout.prop(self, "thumbnail_frame")
        if not self.is_vse(context):
            layout.prop(context.scene.kitsu, "playblast_render_mode", text="Render Mode")

    def _upload_playblast(self, context: bpy.types.Context, filepath: Path) -> None:
        # Create a comment
        comment_text = self._gen_comment_text(context, self._entity)
        comment = self._task.add_comment(
            self._task_status,
            comment=comment_text,
        )

        # Add_preview_to_comment
        self._task.add_preview_to_comment(
            comment,
            filepath.as_posix(),
            self.thumbnail_frame_final,
        )

        logger.info(
            f"Uploaded playblast for shot: {self._entity.name} under: {self._task_type.name}"
        )

    def _gen_comment_text(self, context: bpy.types.Context, shot: Shot) -> str:
        header = f"Playblast {shot.name}: {context.scene.kitsu.playblast_version}"
        if self.comment:
            return header + f"\n\n{self.comment}"
        return header

    def _open_webbrowser(self) -> None:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        # https://staging.kitsu.blender.cloud/productions/7838e728-312b-499a-937b-e22273d097aa/shots?search=010_0010_A

        host_url = addon_prefs.host
        if host_url.endswith("/api"):
            host_url = host_url[:-4]

        if host_url.endswith("/"):
            host_url = host_url[:-1]

        url = f"{host_url}/productions/{cache.project_active_get().id}/shots?search={cache.shot_active_get().name}"
        webbrowser.open(url)

    def _get_active_entity(self, context):
        if context_core.is_sequence_context():
            # Get sequence
            return cache.sequence_active_get()
        elif context_core.is_asset_context():
            return cache.asset_active_get()
        else:
            # Get shot.
            return cache.shot_active_get()


class KITSU_OT_playblast_set_version(bpy.types.Operator):
    bl_idname = "kitsu.anim_set_playblast_version"
    bl_label = "Version"
    bl_property = "versions"
    bl_description = (
        "Sets version of playblast. Warning triangle in ui "
        "indicates that version already exists on disk"
    )

    versions: bpy.props.EnumProperty(
        items=opsdata.get_playblast_versions_enum_list, name="Versions"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(context.scene.kitsu.playblast_dir)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        kitsu_props = context.scene.kitsu
        version = self.versions

        if not version:
            return {"CANCELLED"}

        if kitsu_props.get('playblast_version') == version:
            return {"CANCELLED"}

        # Update global scene cache version prop.
        kitsu_props.playblast_version = version
        logger.info("Set playblast version to %s", version)

        # Redraw ui.
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class KITSU_OT_push_frame_range(bpy.types.Operator):
    bl_idname = "kitsu.push_frame_range"
    bl_label = "Push Frame Start"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Adjusts the start frame of animation file."

    frame_start = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.shot_active_get())

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Set 3d_start using current scene frame start.")
        col.label(text=f"New Frame Start: {self.frame_start}", icon="ERROR")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        core.set_frame_range_in(self.frame_start)
        self.report({"INFO"}, f"Updated frame range offset {self.frame_start}")
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        self.frame_start = context.scene.frame_start
        frame_in, _ = core.get_frame_range()
        if frame_in == self.frame_start:
            self.report(
                {"INFO"},
                f"Sever's 'Frame In' already matches current Scene's 'Frame Start' {self.frame_start}",
            )
            return {"FINISHED"}
        return context.window_manager.invoke_props_dialog(self, width=500)


class KITSU_OT_pull_frame_range(bpy.types.Operator):
    bl_idname = "kitsu.pull_frame_range"
    bl_label = "Pull Frame Range"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Pulls frame range of active shot from the server "
        "and set the current scene's frame range to it"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        frame_in, frame_out = core.get_frame_range()

        # Check if current frame range matches the one for active shot.
        if core.check_frame_range(context):
            self.report({"INFO"}, f"Frame range already up to date")
            return {"FINISHED"}

        # Update scene frame range.
        context.scene.frame_start = frame_in
        context.scene.frame_end = frame_out

        if not core.check_frame_range(context):
            self.report(
                {"ERROR"}, f"Failed to update frame range to {frame_in} - {frame_out}"
            )
            return {"CANCELLED"}
        # Log.
        self.report({"INFO"}, f"Updated frame range {frame_in} - {frame_out}")
        return {"FINISHED"}


class KITSU_OT_check_frame_range(bpy.types.Operator):
    bl_idname = "kitsu.check_frame_range"
    bl_label = "Check Frame Range"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Checks frame range of active shot from the server matches current file"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.shot_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if core.check_frame_range(context):
            self.report({"INFO"}, f"Frame Range is accurate")
            return {"FINISHED"}
        self.report({"ERROR"}, f"Failed: Frame Range Check")
        return {"CANCELLED"}


class KITSU_OT_playblast_increment_playblast_version(bpy.types.Operator):
    bl_idname = "kitsu.anim_increment_playblast_version"
    bl_label = "Add Version Increment"
    bl_description = "Increment the playblast version by one"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Incremenet version.
        version = opsdata.add_playblast_version_increment(context)

        # Update cache_version prop.
        context.scene.kitsu.playblast_version = version

        # Report.
        self.report({"INFO"}, f"Add playblast version {version}")

        util.ui_redraw()
        return {"FINISHED"}


@persistent
def load_post_handler_init_version_model(dummy: Any) -> None:
    opsdata.init_playblast_file_model(bpy.context)


def draw_frame_range_warning(self, context):
    active_shot = cache.shot_active_get()
    layout = self.layout
    layout.alert = True
    layout.label(
        text="Frame Range on server does not match the active shot. Please 'pull' the correct frame range from the server"
    )
    layout.label(text=f"   File Frame Range: {context.scene.frame_start}-{context.scene.frame_end}")
    if active_shot:
        kitsu_3d_start = active_shot.get_3d_start()
        layout.label(
            text=f'Server Frame Range: {kitsu_3d_start}-{kitsu_3d_start + int(active_shot.nb_frames) - 1}'
        )
    else:
        layout.label(text=f'   Server Frame Range: not found')

    layout.operator("kitsu.pull_frame_range", icon='TRIA_DOWN')


def draw_kitsu_context_warning(self, context):
    layout = self.layout
    layout.alert = True
    layout.label(
        text="Frame Range couldn't be found because current Shot wasn't found, please select an active Shot from Kitsu Context Menu"
    )


@persistent
def detect_kitsu_context(dummy: Any) -> None:
    # TODO Move this handler should not be part of playblast
    # Leaving this here so it can be set in order along with frame range detection

    # Skip not logged into Kitsu
    if not prefs.session_auth(bpy.context):
        return

    # Skip project not set
    if not cache.project_active_get():
        return

    # Skip if project root dir is not in file path
    project_root_dir = prefs.project_root_dir_get(bpy.context)
    if not project_root_dir in Path(bpy.data.filepath).parents:
        return

    # Skip if Unsaved File
    if not bpy.data.is_saved:
        return

    try:
        bpy.ops.kitsu.con_detect_context()
    except RuntimeError:
        bpy.context.window_manager.popup_menu(
            draw_kitsu_context_warning,
            title="Warning: Kitsu Context Auto-Detection Failed.",
            icon='WARNING',
        )
        pass


@persistent
def load_post_handler_check_frame_range(dummy: Any) -> None:
    # Only show if kitsu context is detected
    cat = bpy.context.scene.kitsu.category
    project_root_dir = prefs.project_root_dir_get(bpy.context)
    shots_dir = project_root_dir.joinpath("pro/shots/")

    # Skip if Unsaved File
    if not bpy.data.is_saved:
        return

    # Skip if File Outside of Shots Directory
    if not shots_dir in Path(bpy.data.filepath).parents:
        return

    # Skip if category is not SHOT
    if not cat == "SHOT":
        return

    if not core.check_frame_range(bpy.context):
        bpy.context.window_manager.popup_menu(
            draw_frame_range_warning,
            title="Warning: Frame Range Error.",
            icon='ERROR',
        )


@persistent
def save_pre_handler_clean_overrides(dummy: Any) -> None:
    """
    Removes some Library Override properties that could be accidentally
    created and cause problems.
    """
    for o in bpy.data.objects:
        if not o.override_library:
            continue
        if o.library:
            continue
        override = o.override_library
        props = override.properties
        for prop in props[:]:
            rna_path = prop.rna_path
            if rna_path in ["active_material_index", "active_material"]:
                props.remove(prop)
                linked_value = getattr(override.reference, rna_path)
                setattr(o, rna_path, linked_value)
                o.property_unset(rna_path)


# ---------REGISTER ----------.

classes = [
    KITSU_OT_playblast_create,
    KITSU_OT_playblast_set_version,
    KITSU_OT_playblast_increment_playblast_version,
    KITSU_OT_pull_frame_range,
    KITSU_OT_push_frame_range,
    KITSU_OT_check_frame_range,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # init_playblast_file_model(bpy.context) not working because of restricted context.

    # Handlers.
    bpy.app.handlers.load_post.append(load_post_handler_init_version_model)
    bpy.app.handlers.load_post.append(detect_kitsu_context)
    bpy.app.handlers.load_post.append(load_post_handler_check_frame_range)

    bpy.app.handlers.save_pre.append(save_pre_handler_clean_overrides)


def unregister():
    # Clear handlers.
    bpy.app.handlers.load_post.remove(load_post_handler_check_frame_range)
    bpy.app.handlers.load_post.remove(load_post_handler_init_version_model)
    bpy.app.handlers.load_post.remove(detect_kitsu_context)

    bpy.app.handlers.save_pre.remove(save_pre_handler_clean_overrides)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
