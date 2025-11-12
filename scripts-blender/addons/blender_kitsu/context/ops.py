# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Dict, Optional, Set
from pathlib import Path

import bpy

from .. import bkglobals, cache, util, prefs
from ..logger import LoggerFactory
from ..types import TaskType, AssetType
from ..context import core as context_core

logger = LoggerFactory.getLogger()


class KITSU_OT_con_productions_load(bpy.types.Operator):
    """
    Gets all productions that are available in server and let's user select. Invokes a search Popup (enum_prop) on click.
    """

    bl_idname = "kitsu.con_productions_load"
    bl_label = "Productions Load"
    bl_property = "enum_prop"
    bl_description = "Sets active project"

    enum_prop: bpy.props.EnumProperty(items=cache.get_projects_enum_list)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Store vars to check if project / seq / shot changed.
        project_prev_id = cache.project_active_get().id

        # Update kitsu metadata.
        cache.project_active_set_by_id(context, self.enum_prop)

        # Clear active shot when sequence changes.
        if self.enum_prop != project_prev_id:
            cache.sequence_active_reset(context)
            cache.episode_active_reset(context)
            cache.asset_type_active_reset(context)
            cache.shot_active_reset(context)
            cache.asset_active_reset(context)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_con_detect_context(bpy.types.Operator):
    bl_idname = "kitsu.con_detect_context"
    bl_label = "Detect Context"
    bl_description = "Auto detects context by looking at file path"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context) and cache.project_active_get() and bpy.data.filepath
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Update kitsu metadata.
        filepath = Path(bpy.data.filepath)
        active_project = cache.project_active_get()

        kitsu_props = context.scene.kitsu
        addon_prefs = context.preferences.addons['.'.join(__package__.split('.')[:-1])].preferences

        is_edit_type = str(filepath).startswith(str(prefs.project_root_dir_get(context) / addon_prefs.edit_dir_name))

        if is_edit_type:
            kitsu_props.category = "EDIT"
            if active_project.production_type == bkglobals.KITSU_TV_PROJECT:
                episode = active_project.get_episode_by_name(filepath.parents[0].name)
                if episode:
                    kitsu_props.episode_active_name = episode.name
            kitsu_props.edit_active_name = context_core.get_versioned_file_basename(filepath.stem)
            kitsu_props.task_type_active_name = bkglobals.EDIT_TASK_TYPE

            util.ui_redraw()
            return {"FINISHED"}

        # TODO REFACTOR THIS WHOLE THING, BAD HACK
        # Path is different for tvshow
        if (
            active_project.production_type == bkglobals.KITSU_TV_PROJECT
            and filepath.parents[3].name == addon_prefs.shot_dir_name
        ):
            episode = active_project.get_episode_by_name(filepath.parents[2].name)
            category = filepath.parents[3].name
        else:
            episode = None
            category = filepath.parents[2].name

        item_group = filepath.parents[1].name
        item = filepath.parents[0].name
        item_task_type = filepath.stem.split(bkglobals.DELIMITER)[-1]

        # Sanity check that the folder struture is correct depending on the type.
        is_shot_type = category == addon_prefs.shot_dir_name
        is_seq_type = category == addon_prefs.seq_dir_name
        is_asset_type = category == addon_prefs.asset_dir_name

        if not is_shot_type and not is_seq_type and not is_asset_type:
            self.report(
                {"ERROR"},
                (
                    f"Expected '{addon_prefs.shot_dir_name}' or '{addon_prefs.asset_dir_name}' 3 folders up. "
                    f"Got: '{filepath.parents[2].as_posix()}' instead. "
                    "Blend file might not be saved in project structure"
                ),
            )
            return {"CANCELLED"}

        if is_shot_type or is_seq_type:
            # TODO: check if frame range update gets triggered.

            # Set category.
            if is_shot_type:
                kitsu_props.category = "SHOT"
                task_mapping = bkglobals.SHOT_TASK_MAPPING
            else:
                kitsu_props.category = "SEQ"
                task_mapping = bkglobals.SEQ_TASK_MAPPING

            if episode:
                kitsu_props.episode_active_name = episode.name

            # Detect and load sequence.
            sequence = active_project.get_sequence_by_name(item_group, episode)
            if not sequence:
                self.report({"ERROR"}, f"Failed to find sequence: '{item_group}' on server")
                return {"CANCELLED"}

            kitsu_props.sequence_active_name = sequence.name

            if is_shot_type:
                # Detect and load shot.
                shot = active_project.get_shot_by_name(sequence, item)
                if not shot:
                    self.report({"ERROR"}, f"Failed to find shot: '{item}' on server")
                    return {"CANCELLED"}

                kitsu_props.shot_active_name = shot.name

            # Detect and load shot task type.
            task_type = self._find_type_entity(item_task_type, task_mapping, TaskType)

            if not task_type:
                self.report(
                    {"ERROR"},
                    f"Failed to find task type: '{item_task_type}' on server",
                )
                return {"CANCELLED"}

            kitsu_props.task_type_active_name = task_type.name

        elif is_asset_type:
            # Set category.
            kitsu_props.category = "ASSET"

            # Detect and load asset type.
            asset_type = self._find_type_entity(item_group, bkglobals.ASSET_TYPE_MAPPING, AssetType)

            if not asset_type:
                self.report(
                    {"ERROR"},
                    f"Failed to find asset type: '{item_group}' on server",
                )
                return {"CANCELLED"}

            kitsu_props.asset_type_active_name = asset_type.name
            # Detect and load asset.
            asset = active_project.get_asset_by_name(item)
            if not asset:
                self.report({"ERROR"}, f"Failed to find asset: '{item}' on server")
                return {"CANCELLED"}
            kitsu_props.asset_active_name = asset.name

            # If split == 1 then filepath has no task type in name, skip asset task_type
            if len(filepath.stem.split(bkglobals.DELIMITER)) > 1:
                # Detect and load asset task_type.
                task_type = self._find_type_entity(
                    item_task_type, bkglobals.ASSET_TASK_MAPPING, TaskType
                )

                if not task_type:
                    self.report(
                        {"ERROR"},
                        f"Failed to find task type: '{item_task_type}' on server",
                    )
                    return {"CANCELLED"}

                kitsu_props.task_type_active_name = task_type.name

        util.ui_redraw()
        self.report({"INFO"}, f"Context Successfully Set!")
        return {"FINISHED"}

    def _find_type_entity(
        self, key: str, mapping: Dict[str, str], entity_type: TaskType | AssetType
    ) -> Optional[str]:

        # Attempt to find by mapping
        if key in mapping:
            task_type = entity_type.by_name(mapping[key])
            if task_type:
                return task_type

        # Try fetching name directly
        task_type = entity_type.by_name(key)
        if task_type:
            return task_type

        # Fallback to task shortname
        task_type = entity_type.by_short_name(key)
        if task_type:
            return task_type

        return None


class KITSU_OT_con_set_asset(bpy.types.Operator):
    bl_idname = "kitsu.con_set_asset"
    bl_label = "Set Kitsu Asset"
    bl_description = (
        "Mark the current file & target collection as an Asset on Kitsu Server "
        "Assets marked with this method will be automatically loaded by the "
        "Shot Builder, if the Asset is casted to the buider's target shot"
    )

    _published_file_path: Path = None

    use_asset_pipeline_publish: bpy.props.BoolProperty(  # type: ignore
        name="Use Asset Pipeline Publish",
        description=(
            "Find the Publish of this file in the 'Publish' folder and use it's filepath for Kitsu Asset`"
            "Selected   Collection must be named exactly the same between current file and Publish"
        ),
        default=False,
    )

    @classmethod
    def poll(cls, context):
        kitsu_props = context.scene.kitsu
        if bpy.data.filepath == "":
            cls.poll_message_set("Blend file must be saved")
            return False
        if not bpy.data.filepath.startswith(str(prefs.project_root_dir_get(context))):
            cls.poll_message_set("Blend file must be saved in project structure")
            return False
        if not context_core.is_asset_context():
            cls.poll_message_set("Kitsu Context panel must be set to 'Asset'")
            return False
        if kitsu_props.asset_type_active_name == "":
            cls.poll_message_set("Asset Type must be set")
            return False
        if kitsu_props.asset_active_name == "":
            cls.poll_message_set("Asset must be set")
            return False
        if not kitsu_props.asset_col:
            cls.poll_message_set("Asset Collection must be set")
            return False
        return True

    def is_asset_pipeline_enabled(self, context) -> bool:
        for addon in context.preferences.addons:
            if addon.module == "asset_pipeline":
                return True
        return False

    def is_asset_pipeline_folder(self, context) -> bool:
        current_folder = Path(bpy.data.filepath).parent
        return current_folder.joinpath("task_layers.json").exists()

    def get_asset_pipeline_publish(self, context) -> Path:
        from asset_pipeline.merge.publish import find_latest_publish

        return find_latest_publish(Path(bpy.data.filepath))

    def invoke(self, context, event):
        if self.is_asset_pipeline_enabled(context) and self.is_asset_pipeline_folder(context):
            self._published_file_path = self.get_asset_pipeline_publish(context)
            if self._published_file_path.exists():
                self.use_asset_pipeline_publish = True
                wm = context.window_manager
                return wm.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        relative_path = self._published_file_path.relative_to(Path(bpy.data.filepath).parent)
        box = layout.box()
        box.enabled = self.use_asset_pipeline_publish
        box.label(text=f"//{str(relative_path)}")
        layout.prop(self, "use_asset_pipeline_publish")

    def execute(self, context):
        project_root = prefs.project_root_dir_get(context)
        if self.use_asset_pipeline_publish:
            relative_path = self._published_file_path.relative_to(project_root)
        else:
            relative_path = Path(bpy.data.filepath).relative_to(project_root)
        blender_asset = context.scene.kitsu.asset_col
        blender_asset.asset_mark()
        kitsu_asset = cache.asset_active_get()
        if not kitsu_asset:
            self.report({"ERROR"}, "Failed to find active Kitsu Asset")
            return {"CANCELLED"}

        kitsu_asset.set_asset_path(relative_path, blender_asset.name)
        self.report(
            {"INFO"},
            f"Kitsu Asset '{kitsu_asset.name}' set to Collection '{blender_asset.name}' at path '{relative_path}'",
        )
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
    KITSU_OT_con_productions_load,
    KITSU_OT_con_detect_context,
    KITSU_OT_con_set_asset,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
