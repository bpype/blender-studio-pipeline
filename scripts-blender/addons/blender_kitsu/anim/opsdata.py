# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re
from typing import Any, Dict, List, Optional, Tuple, Union, Generator

import bpy

from .. import bkglobals, util
from ..types import Shot
from ..logger import LoggerFactory

logger = LoggerFactory.getLogger()


def is_item_local(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # Local collection of blend file.
    if not item.override_library and not item.library:
        return True
    return False


def is_item_lib_override(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # Collection from libfile and overwritten.
    if item.override_library and not item.library:
        return True
    return False


def is_item_lib_source(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    #  Source collection from libfile not overwritten.
    if not item.override_library and item.library:
        return True
    return False


def create_collection_instance(
    context: bpy.types.Context,
    ref_coll: bpy.types.Collection,
    instance_name: str,
) -> bpy.types.Object:
    # Use empty to instance source collection.
    instance_obj = bpy.data.objects.new(name=instance_name, object_data=None)
    instance_obj.instance_collection = ref_coll
    instance_obj.instance_type = "COLLECTION"

    parent_collection = context.scene.collection
    parent_collection.objects.link(instance_obj)

    logger.info(
        "Instanced collection: %s as: %s",
        ref_coll.name,
        instance_obj.name,
    )

    return instance_obj


def find_rig(coll: bpy.types.Collection, log: bool = True) -> Optional[bpy.types.Armature]:
    valid_rigs = []

    for obj in coll.all_objects:
        # Default rig name: 'RIG-rex' / 'RIG-Rex'.
        if obj.type != "ARMATURE":
            continue

        if not obj.name.startswith(bkglobals.PREFIX_RIG):
            continue

        valid_rigs.append(obj)

    if not valid_rigs:
        return None

    if log:
        for rig in valid_rigs:
            logger.info("Found rig: %s", rig.name)
    return valid_rigs


def find_asset_collections(
    top_level_col: bpy.types.Collection, log: bool = True
) -> List[bpy.types.Collection]:
    asset_colls: List[bpy.types.Collection] = []
    for coll in top_level_col.children_recursive:
        if not is_item_lib_override(coll):
            continue

        for prefix in bkglobals.ASSET_COLL_PREFIXES:
            if not coll.name.startswith(prefix):
                continue

            asset_colls.append(coll)
    if log:
        logger.info(
            "Found asset collections:\n%s", ", ".join([c.name for c in asset_colls])
        )
    return asset_colls


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def find_asset_collections_in_scene(
    scene: bpy.types.Scene, log: bool = True
) -> List[bpy.types.Collection]:
    asset_colls: List[bpy.types.Collection] = []
    colls: List[bpy.types.Collection] = []

    # Get all collections that are linked in this scene.
    for coll in scene.collection.children:
        colls.extend(list(traverse_collection_tree(coll)))

    for coll in colls:
        for prefix in bkglobals.ASSET_COLL_PREFIXES:
            if not coll.name.startswith(prefix):
                continue

            asset_colls.append(coll)
    if log:
        logger.info(
            "Found asset collections:\n%s", ", ".join([c.name for c in asset_colls])
        )

    return asset_colls


def get_ref_coll(coll: bpy.types.Collection) -> bpy.types.Collection:
    if not coll.override_library:
        return coll

    return coll.override_library.reference


def find_asset_name(name: str) -> str:
    name = _kill_increment_end(name)
    if name.endswith(bkglobals.SPACE_REPLACER + "rig"):
        name = name[:-4]
    return name.split(bkglobals.DELIMITER)[-1]  # CH-rex -> 'rex'


def _kill_increment_end(str_value: str) -> str:
    match = re.search(r"\.\d\d\d$", str_value)
    if match:
        return str_value.replace(match.group(0), "")
    return str_value


def is_multi_asset(asset_name: str) -> bool:
    if asset_name.startswith("thorn"):
        return True

    if asset_name.startswith("pine_cone"):
        return True

    if asset_name.startswith("pee_"):
        return True

    if asset_name.lower() in bkglobals.MULTI_ASSETS:
        return True

    return False


action_names_cache: List[str] = []
# We need this in order to increment prefixes of duplications of the same asset correctly
# gets cleared populated during call of KITSU_OT_anim_check_action_names.
_current_asset: str = ""
_current_asset_idx: int = 0
# We need these two variables to track if we are on the first asset that is currently processed
# (if there are multiple ones) because the first one CAN get keep it postfix.


def gen_action_name(
    armature: bpy.types.Armature, collection: bpy.types.Collection, shot: Shot
) -> str:
    global action_names_cache
    global _current_asset
    global _current_asset_idx
    action_names_cache.sort()

    def _find_postfix(action_name: str) -> Optional[str]:
        # ANI-lady_bug_A.030_0020_A.v001.
        split1 = action_name.split(bkglobals.DELIMITER)[-1]  # lady_bug_A.030_0020_A.v001
        split2 = split1.split(".")[0]  # lady_bug_A
        split3 = split2.split(bkglobals.SPACE_REPLACER)[-1]  # A
        if len(split3) == 1:
            # is postfix
            # print(f"{action.name} found postfix: {split3}")
            return split3
        else:
            return None

    ref_coll = get_ref_coll(collection)
    action_prefix = "ANI"
    asset_name = find_asset_name(ref_coll.name).lower()
    asset_name = asset_name.replace(".", bkglobals.SPACE_REPLACER)

    # Track on which repition we are of the same asset.
    if asset_name == _current_asset:
        _current_asset_idx += 1
    else:
        _current_asset_idx = 0
    _current_asset = asset_name

    version = "v001"
    shot_name = shot.name
    has_action = False
    final_postfix = ""

    # Overwrite version v001 if there is an action which already contains a version.
    if armature.animation_data:
        if armature.animation_data.action:
            has_action = True
            version = util.get_version(armature.animation_data.action.name) or "v001"

    # Action name for single aset.
    delimiter = bkglobals.DELIMITER  # Currently set to '-'
    space = bkglobals.SPACE_REPLACER  # Currently set to '_'
    action_name = (
        f"{action_prefix}{delimiter}{asset_name}{delimiter}{shot_name}{delimiter}{version}"
    )

    if is_multi_asset(asset_name):
        existing_postfixes = []

        # Find all actions that relate to the same asset except for the asset.
        for action_name in action_names_cache:
            # Skip action that was input as parameter of this function.
            if has_action and action_name == armature.animation_data.action.name:
                # Print(f"Skipping action same name: {action_name}").
                continue

            # print(action_names_cache)
            if action_name.startswith(f"{action_prefix}{delimiter}{asset_name}"):
                multi_postfix = _find_postfix(action_name)
                if multi_postfix:
                    # print(f"Found postfix {multi_postfix} for aseet : {asset_name}")
                    existing_postfixes.append(multi_postfix)

        # print(f"EXISTING: {existing_postfixes}")
        if existing_postfixes:
            if _current_asset_idx == 0:
                # print(f"{asset_name} is first asset can keep postfix")
                final_postfix = multi_postfix
            else:
                # Otherwise increment the postfix by one.
                existing_postfixes.sort()
                final_postfix = chr(
                    ord(existing_postfixes[-1]) + 1
                )  # handle postfix == Z > [
        else:
            # If there are no existing postfixes the first one is A.
            final_postfix = "A"

        if has_action:
            # Overwrite multi_postfix if multi_postfix exists.
            current_postfix = _find_postfix(armature.animation_data.action.name)

            # If existing action already has a postfix check if that one is in
            # existing postfixes, if not use the actions post fix.
            if current_postfix:
                if current_postfix not in existing_postfixes:
                    final_postfix = current_postfix

        # Action name for multi asset.
        action_name = f"{action_prefix}{delimiter}{asset_name}{space}{final_postfix}{delimiter}{shot_name}{delimiter}{version}"

    return action_name
