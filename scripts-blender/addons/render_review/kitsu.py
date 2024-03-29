# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from typing import List, Dict, Union, Any, Set, Optional
import bpy

from render_review import util
from blender_kitsu import cache, types, prefs
from blender_kitsu.sqe import opsdata, pull, push
from render_review.log import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


def is_auth() -> bool:
    return prefs.addon_prefs_get(bpy.context).session.is_auth()


def get_project() -> Optional[types.Project]:
    return cache.project_active_get()


def is_active_project() -> bool:
    return bool(cache.project_active_get())


def is_auth_and_project() -> bool:
    return bool(is_auth() and is_active_project())


def addon_prefs() -> bpy.types.AddonPreferences:
    return prefs.addon_prefs_get(bpy.context)


def create_meta_strip(
    context: bpy.types.Context, strip: bpy.types.Sequence
) -> bpy.types.MovieSequence:
    # Get frame range information from current strip.
    strip_range = range(strip.frame_final_start, strip.frame_final_end)
    channel = strip.channel + 1

    # Create new meta strip.
    meta_strip = context.scene.sequence_editor.sequences.new_movie(
        f"{strip.name}_metastrip",
        "",
        strip.channel + 1,
        strip.frame_final_start,
    )

    # Set blend alpha.
    meta_strip.blend_alpha = 0

    # Set frame in and out.
    meta_strip.frame_final_start = strip.frame_final_start
    meta_strip.frame_final_end = strip.frame_final_end
    # Meta_strip.channel = strip.channel + 1.

    # Init start frame offset.
    opsdata.init_start_frame_offset(meta_strip)

    logger.info(
        "%s created metastrip: %s",
        strip.name,
        meta_strip.name,
    )

    return meta_strip


def link_strip_by_name(
    context: bpy.types.Context,
    strip: bpy.types.Sequence,
    shot_name: str,
    sequence_name: str,
) -> None:
    # Get seq and shot.
    active_project = cache.project_active_get()
    seq = active_project.get_sequence_by_name(sequence_name)
    shot = active_project.get_shot_by_name(seq, shot_name)

    if not shot:
        logger.error("Unable to find shot %s on kitsu", shot_name)
        return

    # Pull shot meta.
    pull.shot_meta(strip, shot)

    # Rename strip.
    strip.name = shot.name

    # Pull sequence color.
    opsdata.append_sequence_color(context, seq)

    # Log.
    t = "Linked strip: %s to shot: %s with ID: %s" % (
        strip.name,
        shot.name,
        shot.id,
    )
    logger.info(t)
    util.redraw_ui()
