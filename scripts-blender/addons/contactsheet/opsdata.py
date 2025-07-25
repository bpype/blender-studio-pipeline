# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, List, Tuple

import bpy

from . import checksqe
from .log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


def get_valid_cs_sequences(
    sequence_list: List["bpy.types.Strip"],
) -> List["bpy.types.Strip"]:
    """
    Returns list of valid sequences out of input sequence list
    """
    valid_sequences = [
        s for s in sequence_list if s.type in ["MOVIE", "IMAGE"] and not s.mute
    ]
    return valid_sequences


def get_sqe_editor(context: bpy.types.Context) -> Optional[bpy.types.Area]:
    sqe_editor = None

    for area in context.screen.areas:
        if area.type == "SEQUENCE_EDITOR":
            sqe_editor = area

    return sqe_editor


def fit_frame_range_to_strips(
    context: bpy.types.Context, strips: Optional[List["bpy.types.Strip"]] = None
) -> Tuple[int, int]:
    def get_sort_tuple(strip: "bpy.types.Strip") -> Tuple[int, int]:
        return (strip.frame_final_start, strip.frame_final_duration)

    if not strips:
        strips = context.scene.sequence_editor.sequences_all

    if not strips:
        return (0, 0)

    strips = list(strips)
    strips.sort(key=get_sort_tuple)

    context.scene.frame_start = strips[0].frame_final_start
    context.scene.frame_end = strips[-1].frame_final_end

    return (context.scene.frame_start, context.scene.frame_end)


def get_top_level_valid_strips_continuous(
    context: bpy.types.Context,
) -> List["bpy.types.Strip"]:

    sequences_tmp = get_valid_cs_sequences(
        list(context.scene.sequence_editor.sequences_all)
    )

    sequences_tmp.sort(key=lambda s: (s.channel, s.frame_final_start), reverse=True)
    sequences: List["bpy.types.Strip"] = []

    for strip in sequences_tmp:

        occ_ranges = checksqe.get_occupied_ranges_for_strips(sequences)
        s_range = range(strip.frame_final_start, strip.frame_final_end + 1)

        if not checksqe.is_range_occupied(s_range, occ_ranges):
            sequences.append(strip)

    return sequences


def poll_make_contactsheet(context: bpy.types.Context) -> bool:

    if not context.scene.sequence_editor.sequences_all:
        return False

    sequences = context.selected_sequences

    if not sequences:
        valid_sequences = get_top_level_valid_strips_continuous(context)
    else:
        valid_sequences = get_valid_cs_sequences(sequences)

    return bool(valid_sequences)


# TODO: add function to actually get sequences, same structure in 3 places.
