import bpy
from bpy.types import Sequence, Context
import os
from typing import Set, List
from pathlib import Path
from .. import cache, prefs, util
from ..types import Task, TaskStatus
from ..playblast.core import override_render_path, override_render_format
from . import opsdata
from ..logger import LoggerFactory
from .core import edit_export_import_latest, edit_export_get_all, edit_export_get_latest

logger = LoggerFactory.getLogger()


class KITSU_OT_edit_export_publish(bpy.types.Operator):
    bl_idname = "kitsu.edit_export_publish"
    bl_label = "Export & Publish"
    bl_description = (
        "Renders current VSE Edit as .mp4"
        "Saves the set version to disk and uploads it to Kitsu with the specified "
        "comment and task type. Overrides some render settings during render. "
    )

    task_status: bpy.props.EnumProperty(name="Task Status", items=cache.get_all_task_statuses_enum)
    comment: bpy.props.StringProperty(name="Comment")
    use_frame_start: bpy.props.BoolProperty(name="Submit update to 'frame_start'.", default=False)
    frame_start: bpy.props.IntProperty(
        name="Frame Start",
        description="Send an integer for the 'frame_start' value of the current Kitsu Edit. \nThis is used by Watchtower to pad the edit in the timeline.",
        default=0,
    )
    thumbnail_frame: bpy.props.IntProperty(
        name="Thumbnail Frame",
        description="Frame to use as the thumbnail on Kitsu",
        min=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        kitsu_props = context.scene.kitsu
        addon_prefs = prefs.addon_prefs_get(context)
        if not prefs.session_auth(context):
            cls.poll_message_set("Login to a Kitsu Server")
        if not cache.project_active_get():
            cls.poll_message_set("Select an active project")
            return False
        if kitsu_props.edit_active_id == "" or cache.edit_active_get().id == "":
            cls.poll_message_set("Select an edit entity from Kitsu Context Menu")
            return False
        if kitsu_props.task_type_active_id == "":
            cls.poll_message_set("Select a task type from Kitsu Context Menu")
            return False
        if not addon_prefs.is_edit_export_root_valid:
            cls.poll_message_set("Edit Export Directory is Invalid, see Add-On preferences")
            return False
        if not addon_prefs.is_edit_export_pattern_valid:
            cls.poll_message_set("Edit Export File Pattern is Invalid, see Add-On preferences")
            return False
        return True

    def invoke(self, context, event):
        self.thumbnail_frame = context.scene.frame_current

        # Remove file name if set in render filepath
        dir_path = bpy.path.abspath(context.scene.render.filepath)
        if not os.path.isdir(Path(dir_path)):
            dir_path = Path(dir_path).parent
        self.render_dir = str(dir_path)

        # 'frame_start' is optionally property appearing on all edit_entries for a project if it exists (used in watchtower)
        server_frame_start = cache.edit_active_get().get_frame_start()
        if server_frame_start is int:
            self.frame_start = server_frame_start
        self.use_frame_start = bool(server_frame_start is not None)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "comment")
        layout.prop(self, 'task_status')

        # Only set `frame_start` if exists on current project
        if self.use_frame_start:
            layout.prop(self, "frame_start")
        layout.prop(self, "thumbnail_frame")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        edit_entity = cache.edit_active_get()
        task_type_entity = cache.task_type_active_get()
        kitsu_props = context.scene.kitsu

        # Ensure thumbnail frame is not outside of frame range
        if self.thumbnail_frame not in range(
            0, (context.scene.frame_end - context.scene.frame_start) + 1
        ):
            self.report(
                {"ERROR"},
                f"Thumbnail frame '{self.thumbnail_frame}' is outside of frame range ",
            )
            return {"CANCELLED"}

        # Build render_path
        render_path = Path(kitsu_props.edit_export_file)
        render_path_str = render_path.as_posix()
        render_name = render_path.name
        if not render_path.parent.exists():
            self.report({"ERROR"}, f"Render path is not set to a directory. '{self.render_dir}'")
            return {"CANCELLED"}

        # Render Sequence to .mp4
        with override_render_path(self, context, render_path_str):
            with override_render_format(self, context, enable_sequencer=True):
                bpy.ops.render.opengl(animation=True, sequencer=True)

        # Create comment with video
        task_status = TaskStatus.by_id(self.task_status)
        task = Task.by_name(edit_entity, task_type_entity)
        comment = task.add_comment(
            task_status,
            comment=self.comment,
        )
        task.add_preview_to_comment(
            comment,
            render_path_str,
            self.thumbnail_frame,
        )
        # Update edit_entry's frame_start if 'frame_start' is found on server
        if self.use_frame_start:
            edit_entity.set_frame_start(self.frame_start)

        self.report({"INFO"}, f"Submitted new comment 'Revision {kitsu_props.edit_export_version}'")
        return {"FINISHED"}


class KITSU_OT_edit_export_set_version(bpy.types.Operator):
    bl_idname = "kitsu.edit_export_set_version"
    bl_label = "Version"
    bl_property = "versions"
    bl_description = (
        "Sets version of edit export. Warning triangle in ui "
        "indicates that version already exists on disk"
    )

    versions: bpy.props.EnumProperty(
        items=opsdata.get_edit_export_versions_enum_list, name="Versions"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(addon_prefs.edit_export_dir != "")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        kitsu_props = context.scene.kitsu
        version = self.versions

        if not version:
            return {"CANCELLED"}

        if kitsu_props.get('edit_export_version') == version:
            return {"CANCELLED"}

        # Update global scene cache version prop.
        kitsu_props.edit_export_version = version
        logger.info("Set edit export version to %s", version)

        # Redraw ui.
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class KITSU_OT_edit_export_increment_version(bpy.types.Operator):
    bl_idname = "kitsu.edit_export_increment_version"
    bl_label = "Add Version Increment"
    bl_description = "Increment the edit export version by one"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Incremenet version.
        version = opsdata.add_edit_export_version_increment(context)

        # Update cache_version prop.
        context.scene.kitsu.edit_export_version = version

        # Report.
        self.report({"INFO"}, f"Add edit export version {version}")

        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_edit_export_import_latest(bpy.types.Operator):
    bl_idname = "kitsu.edit_export_import_latest"
    bl_label = "Import Latest Edit Export"
    bl_description = (
        "Find and import the latest editorial render found in the Editorial Export Directory for the current shot. "
        "Will only Import if the latest export is not already imported. "
        "Will remove any previous exports currently in the file's Video Sequence Editor"
    )

    _existing_edit_exports = []
    _removed_movie = 0
    _removed_audio = 0
    _latest_export_name = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            cls.poll_message_set("Login to a Kitsu Server")
            return False
        if not cache.project_active_get():
            cls.poll_message_set("Select an active project")
            return False
        if cache.shot_active_get().id == "":
            cls.poll_message_set("Please set an active shot in Kitsu Context UI")
            return False
        if not prefs.addon_prefs_get(context).is_edit_export_root_valid:
            cls.poll_message_set("Edit Export Directory is Invalid, see Add-On Preferences")
            return False
        return True

    def get_filepath(self, strip):
        if hasattr(strip, "filepath"):
            return strip.filepath
        if hasattr(strip, "sound"):
            return strip.sound.filepath

    def compare_strip_to_path(self, strip: Sequence, compare_path: Path) -> bool:
        strip_path = Path(bpy.path.abspath(self.get_filepath(strip)))
        return bool(compare_path.absolute() == strip_path.absolute())

    def compare_strip_to_paths(self, strip: Sequence, compare_paths: List[Path]) -> bool:
        for compare_path in compare_paths:
            if self.compare_strip_to_path(strip, compare_path):
                return True
        return False

    def get_existing_edit_exports(
        self, context: Context, all_edit_export_paths: List[Path]
    ) -> List[Sequence]:
        sequences = context.scene.sequence_editor.sequences

        # Collect Existing Edit Export
        for strip in sequences:
            if self.compare_strip_to_paths(strip, all_edit_export_paths):
                self._existing_edit_exports.append(strip)
        return self._existing_edit_exports

    def check_if_latest_edit_export_is_imported(self, context: Context) -> bool:
        # Check if latest edit export is already loaded.
        for strip in self._existing_edit_exports:
            latest_edit_export_path = edit_export_get_latest(context)
            if self.compare_strip_to_path(strip, latest_edit_export_path):
                self._latest_export_name = latest_edit_export_path.name
                return True

    def remove_existing_edit_exports(self, context: Context) -> None:
        # Remove Existing Strips to make way for new Strip
        sequences = context.scene.sequence_editor.sequences
        for strip in self._existing_edit_exports:
            if strip.type == "MOVIE":
                self._removed_movie += 1
            if strip.type == "SOUND":
                self._removed_audio += 1
            sequences.remove(strip)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Reset Values
        self._existing_edit_exports = []
        self._removed_movie = 0
        self._removed_audio = 0
        self._latest_export_name = ""

        addon_prefs = prefs.addon_prefs_get(context)

        # Get paths to all edit exports
        all_edit_export_paths = edit_export_get_all(context)
        if all_edit_export_paths == []:
            self.report(
                {"WARNING"},
                f"No Edit Exports found in '{addon_prefs.edit_export_dir}' using pattern '{addon_prefs.edit_export_file_pattern}' See Add-On Preferences",
            )
            return {"CANCELLED"}

        # Collect all existing edit exports
        self.get_existing_edit_exports(context, all_edit_export_paths)

        # Stop latest export is already imported
        if self.check_if_latest_edit_export_is_imported(context):
            self.report(
                {"WARNING"},
                f"Latest Editorial Export already loaded '{self._latest_export_name}'",
            )
            return {"CANCELLED"}

        # Remove old edit exports
        self.remove_existing_edit_exports(context)

        # Import new edit export
        shot = cache.shot_active_get()
        strips = edit_export_import_latest(context, shot)

        if strips is None:
            self.report({"WARNING"}, f"Loaded Latest Editorial Export failed to import!")
            return {"CANCELLED"}

        # Report.
        if self._removed_movie > 0 or self._removed_audio > 0:
            removed_msg = (
                f"Removed {self._removed_movie} Movie Strips and {self._removed_audio} Audio Strips"
            )
            self.report(
                {"INFO"}, f"Loaded Latest Editorial Export, '{strips[0].name}'. {removed_msg}"
            )
        else:
            self.report({"INFO"}, f"Loaded Latest Editorial Export, '{strips[0].name}'")
        return {"FINISHED"}


classes = [
    KITSU_OT_edit_export_publish,
    KITSU_OT_edit_export_set_version,
    KITSU_OT_edit_export_increment_version,
    KITSU_OT_edit_export_import_latest,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
