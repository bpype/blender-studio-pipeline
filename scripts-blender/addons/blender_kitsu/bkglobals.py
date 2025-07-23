# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

FPS = 24
VERSION_PATTERN = r"v\d\d\d"
FRAME_START = 101

# Naming Conventions Set by https://studio.blender.org/tools/naming-conventions/introduction
DELIMITER = "-"  # Seperates items (e.g."{shot_name}-{shot_task}"")
SPACE_REPLACER = "_"  # Represents spaces in a single item (e.g. "my shot name" = "my_shot_name")

ASSET_TASK_MAPPING = {
    "geometry": "Geometry",
    "grooming": "Grooming",
    "modeling": "Modeling",
    "rigging": "Rigging",
    "sculpting": "Sculpting",
    "shading": "Shading",
}

ASSET_TYPE_MAPPING = {
    "char": "Character",
    "set": "Set",
    "props": "Prop",
    "env": "Library",
}

SEQ_TASK_MAPPING = {
    "previs": "Previsualization",
    "boards": "Boards",
}

SHOT_TASK_MAPPING = {
    "anim2D": "Anim2D",
    "anim": "Animation",
    "comp": "Compositing",
    "fx": "FX",
    "layout": "Layout",
    "lighting": "Lighting",
    "previz": "Previz",
    "rendering": "Rendering",
    "smear_to_mesh": "Smear to mesh",
    "storyboard": "Storyboard",
}

PREFIX_RIG = "RIG-"

MULTI_ASSETS = [
    "sprite",
    "snail",
    "spider",
    "peanut",
    "peanut_box",
    "pretzel",
    "corn_dart",
    "corn_darts_bag",
    "meat_stick",
    "salty_twists_bag",
    "salt_stick",
    "salt_stix_package",
    "briny_bear",
    "briny_bears_bag",
]  # list of assets that gets duplicated and therefore follows another naming sheme

ASSET_COLL_PREFIXES = ["CH-", "PR-", "SE-", "FX-", "EN-"]

ASSET_FOLDER_MAPPING = {
    "Character" : "chars",
    "FX" : "fx",
    "Library" : "lib",
    "Lighting" : "lgt",
    "Prop" : "props",
    "Set" : "sets",
}

# Kitsu Constants
KITSU_TV_PROJECT = 'tvshow'

# Kitsu Metadata Keys
KITSU_FILEPATH_KEY = "filepath"
KITSU_COLLECTION_KEY = "collection"

RES_DIR_PATH = Path(os.path.abspath(__file__)).parent.joinpath("res")

SCENE_NAME_PLAYBLAST = "playblast_playback"
PLAYBLAST_DEFAULT_STATUS = "Todo"

BUILD_SETTINGS_FILENAME = "settings.json"
BUILD_HOOKS_FILENAME = "hooks.py"

EDIT_TASK_TYPE = "Edit"
