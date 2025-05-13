# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .. import bkglobals
from ..types import Cache, Sequence, Project, Shot
from ..logger import LoggerFactory

logger = LoggerFactory.getLogger()


def shot_meta(strip: bpy.types.Strip, shot: Shot, clear_cache: bool = True) -> None:
    if clear_cache:
        # Clear cache before pulling.
        Cache.clear_all()

    # Update sequence props.
    seq = Sequence.by_id(shot.parent_id)
    strip.kitsu.sequence_id = seq.id
    strip.kitsu.sequence_name = seq.name

    # Update shot props.
    strip.kitsu.shot_id = shot.id
    strip.kitsu.shot_name = shot.name
    strip.kitsu.shot_description = shot.description if shot.description else ""

    # Update project props.
    project = Project.by_id(shot.project_id)
    strip.kitsu.project_id = project.id
    strip.kitsu.project_name = project.name

    # Update meta props.
    strip.kitsu.initialized = True
    strip.kitsu.linked = True

    # Update strip name.
    strip.name = shot.name

    # Log.
    logger.info("Pulled meta from shot: %s to strip: %s", shot.name, strip.name)
