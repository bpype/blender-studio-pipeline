# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from typing import Tuple

import bpy

from .. import bkglobals
from ..types import Sequence, Project, Shot
from ..logger import LoggerFactory
import gazu

logger = LoggerFactory.getLogger()


def shot_meta(strip: bpy.types.Strip, shot: Shot) -> None:
    # Update shot info.

    shot.name = strip.kitsu.shot_name
    shot.description = strip.kitsu.shot_description
    shot.data["frame_in"] = strip.frame_final_start
    shot.data["frame_out"] = strip.frame_final_end
    shot.data["3d_start"] = strip.kitsu_3d_start
    shot.nb_frames = strip.frame_final_duration
    shot.data["fps"] = bkglobals.FPS

    # If user changed the sequence the shot belongs to
    # (can only be done by operator not by hand).
    if strip.kitsu.sequence_id != shot.sequence_id:
        sequence = Sequence.by_id(strip.kitsu.sequence_id)
        shot.sequence_id = sequence.id
        shot.parent_id = sequence.id
        shot.sequence_name = sequence.name

    # Update on server.
    shot.update()
    logger.info("Pushed meta to shot: %s from strip: %s", shot.name, strip.name)


def new_shot(
    strip: bpy.types.Strip, sequence: Sequence, project: Project, add_tasks=False
) -> Shot:
    frame_range = (strip.frame_final_start, strip.frame_final_end)
    shot = project.create_shot(
        sequence,
        strip.kitsu.shot_name,
        nb_frames=strip.frame_final_duration,
        frame_in=frame_range[0],
        frame_out=frame_range[1],
        data={"fps": bkglobals.FPS, "3d_start": bkglobals.FRAME_START},
    )

    if add_tasks:
        create_intial_tasks(shot, project)

    # Update description, no option to pass that on create.
    if strip.kitsu.shot_description:
        shot.description = strip.kitsu.shot_description
        shot.update()

    # Set project name locally, will be available on next pull.
    shot.project_name = project.name
    logger.info("Pushed create shot: %s for project: %s", shot.name, project.name)
    return shot


def new_sequence(strip: bpy.types.Strip, project: Project) -> Sequence:
    sequence = project.create_sequence(
        strip.kitsu.sequence_name,
        strip.kitsu.episode_id
    )
    logger.info(
        "Pushed create sequence: %s for project: %s", sequence.name, project.name
    )
    return sequence


def delete_shot(strip: bpy.types.Strip, shot: Shot) -> str:
    result = shot.remove()
    logger.info(
        "Pushed delete shot: %s for project: %s",
        shot.name,
        shot.project_name or "Unknown",
    )
    strip.kitsu.clear()
    return result


def create_intial_tasks(shot: Shot, project: Project):
    shot_entity = gazu.shot.get_shot(shot.id)
    for task_type in gazu.task.all_task_types_for_project(project.id):
        if task_type["for_entity"] == "Shot":
            gazu.task.new_task(shot_entity, task_type)
