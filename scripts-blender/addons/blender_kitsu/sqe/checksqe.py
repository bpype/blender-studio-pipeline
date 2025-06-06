# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Dict, List

import bpy

from ..logger import LoggerFactory
from ..sqe import checkstrip

logger = LoggerFactory.getLogger()


def _is_range_in(range1: range, range2: range) -> bool:
    """Whether range1 is a subset of range2"""
    # usual strip setup strip1(101, 120)|strip2(120, 130)|strip3(130, 140)
    # first and last frame can be the same for each strip
    range2 = range(range2.start + 1, range2.stop - 1)

    if not range1:
        return True  # empty range is subset of anything
    if not range2:
        return False  # non-empty range can't be subset of empty range
    if len(range1) > 1 and range1.step % range2.step:
        return False  # must have a single value or integer multiple step
    return range1.start in range2 or range1[-1] in range2


def get_occupied_ranges(context: bpy.types.Context) -> Dict[str, List[range]]:
    """
    Scans sequence editor and returns a dictionary. It contains a key for each channel
    and a list of ranges with the occupied frame ranges as values.
    """
    # {'1': [(101, 213), (300, 320)]}.
    ranges: Dict[str, List[range]] = {}

    # Populate ranges.
    for strip in context.scene.sequence_editor.sequences_all:
        ranges.setdefault(str(strip.channel), [])
        ranges[str(strip.channel)].append(
            range(strip.frame_final_start, strip.frame_final_end + 1)
        )

    # Sort ranges tuple list.
    for channel in ranges:
        liste = ranges[channel]
        ranges[channel] = sorted(liste, key=lambda item: item.start)

    return ranges


def is_range_occupied(range_to_check: range, occupied_ranges: List[range]) -> bool:
    for r in occupied_ranges:
        # Range(101, 150).
        if _is_range_in(range_to_check, r):
            return True
        continue
    return False


def get_shot_strips(context: bpy.types.Context) -> List[bpy.types.Strip]:
    shot_strips = []
    shot_strips.extend(
        [
            strip
            for strip in context.scene.sequence_editor.sequences_all
            if checkstrip.is_valid_type(strip, log=False)
            and checkstrip.is_linked(strip, log=False)
        ]
    )
    return shot_strips
