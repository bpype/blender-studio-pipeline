# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional
from . import pull
import bpy
from .. import bkglobals, prefs
from ..logger import LoggerFactory
from ..types import Sequence, Task, TaskStatus, Shot, TaskType

logger = LoggerFactory.getLogger()

_sqe_shot_enum_list: List[Tuple[str, str, str]] = []
_sqe_not_linked: List[Tuple[str, str, str]] = []
_sqe_duplicates: List[Tuple[str, str, str]] = []
_sqe_multi_project: List[Tuple[str, str, str]] = []


def sqe_get_not_linked(self, context):
    return _sqe_not_linked


def sqe_get_duplicates(self, context):
    return _sqe_duplicates


def sqe_get_multi_project(self, context):
    return _sqe_multi_project


def sqe_update_not_linked(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list = []

    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    for strip in strips:
        if strip.kitsu.initialized and not strip.kitsu.linked:
            enum_list.append((strip.name, strip.name, ""))

    return enum_list


def sqe_update_duplicates(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list = []
    data_dict = {}
    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    # Create data dict that holds all shots ids and the corresponding strips that are linked to it.
    for i in range(len(strips)):
        if strips[i].kitsu.linked:
            # Get shot_id, shot_name, create entry in data_dict if id not existent.
            shot_id = strips[i].kitsu.shot_id
            shot_name = strips[i].kitsu.shot_name
            if shot_id not in data_dict:
                data_dict[shot_id] = {"name": shot_name, "strips": []}

            # Append i to strips list.
            if strips[i] not in set(data_dict[shot_id]["strips"]):
                data_dict[shot_id]["strips"].append(strips[i])

            # Comparet to all other strip.
            for j in range(i + 1, len(strips)):
                if shot_id == strips[j].kitsu.shot_id:
                    data_dict[shot_id]["strips"].append(strips[j])

    # Convert in data strucutre for enum property.
    for shot_id, data in data_dict.items():
        if len(data["strips"]) > 1:
            enum_list.append(("", data["name"], shot_id))
            for strip in data["strips"]:
                enum_list.append((strip.name, strip.name, ""))

    return enum_list


def sqe_update_multi_project(context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    """get all strips that are initialized but not linked yet"""
    enum_list: List[Tuple[str, str, str]] = []
    data_dict: Dict[str, Any] = {}

    if context.selected_sequences:
        strips = context.selected_sequences
    else:
        strips = context.scene.sequence_editor.sequences_all

    # Create data dict that holds project names as key and values the corresponding sequence strips.
    for strip in strips:
        if strip.kitsu.linked:
            project = strip.kitsu.project_name
            if project not in data_dict:
                data_dict[project] = []

            # Append i to strips list.
            if strip not in set(data_dict[project]):
                data_dict[project].append(strip)

    # Convert in data strucutre for enum property.
    for project, strips in data_dict.items():
        enum_list.append(("", project, ""))
        for strip in strips:
            enum_list.append((strip.name, strip.name, ""))

    return enum_list


def resolve_pattern(pattern: str, var_lookup_table: Dict[str, str]) -> str:
    matches = re.findall(r"\<(\w+)\>", pattern)
    matches = list(set(matches))
    # If no variable detected just return value.
    if len(matches) == 0:
        return pattern
    else:
        result = pattern
        for to_replace in matches:
            if to_replace in var_lookup_table:
                to_insert = var_lookup_table[to_replace]
                result = result.replace("<{}>".format(to_replace), to_insert)
            else:
                logger.warning(
                    "Failed to resolve variable: %s not defined!", to_replace
                )
                return ""
        return result


def get_shots_enum_for_link_shot_op(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    global _sqe_shot_enum_list

    if not self.sequence_enum:
        return []

    zseq_active = Sequence.by_id(self.sequence_enum)

    _sqe_shot_enum_list.clear()
    _sqe_shot_enum_list.extend(
        [(s.id, s.name, s.description or "") for s in zseq_active.get_all_shots()]
    )
    return _sqe_shot_enum_list


def upload_preview(
    context: bpy.types.Context, filepath: Path, task_type: TaskType, comment: str = ""
) -> None:
    # Get shot by id which is in filename of thumbnail.
    shot_id = filepath.name.split(bkglobals.SPACE_REPLACER)[0]
    shot = Shot.by_id(shot_id)

    # Find task from task type for that shot, ca be None of no task was added for that task type.
    task = Task.by_name(shot, task_type)

    if not task:
        # Turns out a entity on the server can have 0 tasks even tough task types exist
        # you have to create a task first before being able to upload a thumbnail.
        task_status = TaskStatus.by_short_name("wip")
        task = Task.new_task(shot, task_type, task_status=task_status)
    else:
        task_status = TaskStatus.by_id(task.task_status_id)

    # Create a comment, e.G 'Update thumbnail'.
    comment_obj = task.add_comment(task_status, comment=comment)

    # Add_preview_to_comment.
    task.add_preview_to_comment(comment_obj, filepath.as_posix())

    logger.info(f"Uploaded preview for shot: {shot.name} under: {task_type.name}")


def init_start_frame_offset(strip: bpy.types.Strip) -> None:
    # Frame start offset.
    offset_start = strip.frame_final_start - strip.frame_start
    # Cast offset start to int, since after Blender 3.3 strip values are floats
    strip.kitsu.frame_start_offset = int(offset_start)


def append_sequence_color(
    context: bpy.types.Context, seq: Sequence
) -> Optional[Tuple[str, str, str]]:
    """
    Extend scene.kitsu.sequence_colors property with seq.data['color'] value if it exists.
    """
    # Pull sequencee color property.

    if not seq.data:
        logger.info("%s failed to load sequence color. Missing 'data' key")
        return None
    if not "color" in seq.data:
        logger.info("%s failed to load sequence color. Missing data['color'] key")
        return None

    try:
        item = context.scene.kitsu.sequence_colors[seq.id]
    except:
        item = context.scene.kitsu.sequence_colors.add()
        item.name = seq.id
        logger.info(
            "Added %s to scene.kitsu.seqeuence_colors",
            seq.name,
        )
    finally:
        item.color = tuple(seq.data["color"])

    return tuple(seq.data["color"])


def push_sequence_color(context: bpy.types.Context, sequence: Sequence) -> None:
    # Updates sequence color and logs.
    try:
        item = context.scene.kitsu.sequence_colors[sequence.id]
    except KeyError:
        logger.info(
            "%s failed to push sequence color. Does not exists in 'context.scene.kitsu.sequence_colors'",
            sequence.name,
        )
    else:
        sequence.update_data({"color": list(item.color)})
        logger.info("%s pushed sequence color", sequence.name)


def create_metadata_strip(
    scene: bpy.types.Scene, name: str, channel, frame_start: int, frame_end: int
) -> bpy.types.MovieStrip:

    addon_prefs = prefs.addon_prefs_get(bpy.context)
    strip = scene.sequence_editor.sequences.new_movie(
        name,
        addon_prefs.metadatastrip_file,
        channel,
        frame_start,
    )

    strip.frame_final_end = frame_end

    # Set blend alpha.
    strip.blend_alpha = 0

    init_start_frame_offset(strip)

    return strip


def link_metadata_strip(
    context, shot: Shot, seq: Sequence, strip: bpy.types.MovieStrip
) -> bpy.types.MovieStrip:
    # Pull shot meta.
    pull.shot_meta(strip, shot)

    # Rename strip.
    strip.name = shot.name

    # Pull sequence color.
    append_sequence_color(context, seq)
    return strip
