# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from typing import Any, Dict, List, Tuple
from pathlib import Path

import bpy
from . import bkglobals
from . import cache, prefs

# TODO: restructure that to not import from anim.
from .playblast import ops as ops_playblast
from .playblast import opsdata as ops_playblast_data
from .logger import LoggerFactory
from .context import core as context_core

logger = LoggerFactory.getLogger()


# Get functions for window manager properties.
def _get_project_active(self):
    return cache.project_active_get().name


def _resolve_pattern(pattern: str, var_lookup_table: Dict[str, str]) -> str:
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
                logger.warning("Failed to resolve variable: %s not defined!", to_replace)
                return ""
        return result


def _get_sequences(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    project_active = cache.project_active_get()

    if not project_active or not addon_prefs.session.is_auth:
        return [("None", "None", "")]

    enum_list = [(s.name, s.name, "") for s in project_active.get_sequences_all()]
    return enum_list


def _gen_shot_preview(self: Any) -> str:
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    shot_counter_increment = addon_prefs.shot_counter_increment
    shot_counter_digits = addon_prefs.shot_counter_digits
    shot_counter_start = self.shot_counter_start
    shot_pattern = addon_prefs.shot_pattern
    examples: List[str] = []
    sequence = self.selected_sequence_name
    episode = cache.episode_active_get()
    var_project = (
        self.var_project_custom if self.var_use_custom_project else self.var_project_active
    )
    var_sequence = self.var_sequence_custom if self.var_use_custom_seq else sequence
    var_lookup_table = {
        "Sequence": var_sequence,
        "Project": var_project,
        "Episode": episode.name,
    }

    for count in range(3):
        counter_number = shot_counter_start + (shot_counter_increment * count)
        counter = str(counter_number).rjust(shot_counter_digits, "0")
        var_lookup_table["Counter"] = counter
        examples.append(_resolve_pattern(shot_pattern, var_lookup_table))

    return " | ".join(examples) + "..."


def get_task_type_name_file_suffix() -> str:
    name = cache.task_type_active_get().name.lower()

    task_mappings = {**bkglobals.SHOT_TASK_MAPPING, **bkglobals.SEQ_TASK_MAPPING}
    for key, value in task_mappings.items():
        if name == value.lower():
            return key

    return name


def get_playblast_dir(self: Any) -> str:
    # shared/editorial/footage/{dev,pre,pro,post}
    # shared/editorial/<episode>/footage/{dev,pre,pro,post}

    # shared/editorial/footage//110_rextoria/110_0030/110_0030-anim

    addon_prefs = prefs.addon_prefs_get(bpy.context)
    if not addon_prefs.is_playblast_root_valid:
        return ""

    episode = cache.episode_active_get()
    sequence = cache.sequence_active_get()
    shot = cache.shot_active_get()
    delimiter = bkglobals.DELIMITER

    # Start building path
    if context_core.is_sequence_context():
        playblast_dir = addon_prefs.seq_playblast_root_path
    else:
        playblast_dir = addon_prefs.shot_playblast_root_path

    playblast_dir = set_episode_variable(playblast_dir)

    if context_core.is_sequence_context():
        playblast_dir = playblast_dir / sequence.name / 'sequence_previews'
        return playblast_dir.as_posix()

    task_type_name_suffix = get_task_type_name_file_suffix()

    playblast_dir = (
        playblast_dir / sequence.name / shot.name / f"{shot.name}{delimiter}{task_type_name_suffix}"
    )
    return playblast_dir.as_posix()


def get_playblast_file(self: Any) -> str:
    if not self.playblast_dir:
        return ""

    task_type_name_suffix = get_task_type_name_file_suffix()
    version = self.playblast_version
    shot = cache.shot_active_get()
    episode = cache.episode_active_get()
    sequence = cache.sequence_active_get()
    delimiter = bkglobals.DELIMITER

    # 070_0010_A-anim-v001.mp4.

    kitsu_props = bpy.context.scene.kitsu
    kitsu_props.get("category")

    if context_core.is_sequence_context():
        # Assuming sequences called 000_name, get 000
        entity_name = sequence.name.split('_')[0]
        if episode:
            # If episode is present, append to the name
            entity_name = f"{episode.name}_{entity_name}"
    elif context_core.is_shot_context():
        entity_name = shot.name
    else:
        entity_name = ''

    file_name = f"{entity_name}{delimiter}{task_type_name_suffix}{delimiter}{version}.mp4"

    return Path(self.playblast_dir).joinpath(file_name).as_posix()


def get_edit_export_dir() -> str:
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    return set_episode_variable(Path(addon_prefs.edit_export_dir))


def get_edit_export_file(self: Any) -> str:
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    export_dir = get_edit_export_dir()
    version = self.edit_export_version
    file_pattern = addon_prefs.edit_export_file_pattern
    file_name = file_pattern.replace('v###', version)
    return export_dir.joinpath(file_name).as_posix()


_active_category_cache_init: bool = False
_active_category_cache: str = ""


def reset_task_type(self: Any, context: bpy.types.Context) -> None:
    global _active_category_cache_init
    global _active_category_cache

    if not _active_category_cache_init:
        _active_category_cache = self.category
        _active_category_cache_init = True
        return

    if self.category == _active_category_cache:
        return None

    cache.task_type_active_reset(context)
    _active_category_cache = self.category
    return None


def on_shot_change(self: Any, context: bpy.types.Context) -> None:
    # Reset versions.
    ops_playblast_data.init_playblast_file_model(context)

    # Check frame range.
    ops_playblast.load_post_handler_check_frame_range(context)


def reset_all_kitsu_props(self: Any, context: bpy.types.Context) -> None:
    cache.sequence_active_reset(context)
    cache.asset_type_active_reset(context)
    cache.shot_active_reset(context)
    cache.asset_active_reset(context)
    cache.episode_active_reset(context)
    cache.task_type_active_reset(context)


def set_episode_variable(base_path: Path) -> Path:
    episode = cache.episode_active_get()
    active_project = cache.project_active_get()
    if not (
        episode
        and '<episode>' in base_path.parts
        and active_project.production_type == bkglobals.KITSU_TV_PROJECT
    ):
        return base_path
    i = base_path.parts.index('<episode>')
    return Path(*base_path.parts[:i]).joinpath(episode.name, *base_path.parts[i + 1 :])
