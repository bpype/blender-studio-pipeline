# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    check_transfer_data_entry,
)
from ...naming import task_layer_prefix_name_get
from .transfer_function_util.drivers import transfer_drivers, cleanup_drivers
from ...task_layer import get_transfer_data_owner
from .... import constants, logging


def constraints_clean(obj):
    cleaned_names = transfer_data_clean(
        obj=obj, data_list=obj.constraints, td_type_key=constants.CONSTRAINT_KEY
    )

    # Remove Drivers that match the cleaned item's name
    for name in cleaned_names:
        cleanup_drivers(obj, 'constraints', name)

def constraint_is_missing(transfer_data_item):
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.CONSTRAINT_KEY,
        data_list=transfer_data_item.id_data.constraints,
    )


def init_constraints(scene, obj):
    td_type_key = constants.CONSTRAINT_KEY
    transfer_data = obj.transfer_data_ownership
    asset_pipe = scene.asset_pipeline
    task_layer_owner, auto_surrender = get_transfer_data_owner(
        asset_pipe,
        td_type_key,
    )
    for const in obj.constraints:
        const.name = task_layer_prefix_name_get(const.name, task_layer_owner)
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        matches = check_transfer_data_entry(transfer_data, const.name, td_type_key)
        if len(matches) == 0:
            asset_pipe.add_temp_transfer_data(
                name=const.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def transfer_constraint(constraint_name, target_obj, source_obj):
    logger = logging.get_logger()
    context = bpy.context
    # Remove old and sync existing constraints.
    old_con = target_obj.constraints.get(constraint_name)
    if old_con:
        target_obj.constraints.remove(old_con)

    src_idx = source_obj.constraints.find(constraint_name)
    if src_idx == -1:
        # This happens if a modifier's transfer data is still around, but the modifier
        # itself was removed.
        logger.debug(f"Constraint Transfer cancelled, '{constraint_name}' not found on '{source_obj.name}'")
        return

    src_con = source_obj.constraints[src_idx]
    new_con = target_obj.constraints.new(src_con.type)
    new_con.name = src_con.name

    props = [p.identifier for p in src_con.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(src_con, prop)
        setattr(new_con, prop, value)

    # Armature constraints have some nested properties we need to copy...
    if src_con.type == "ARMATURE":
        for target_item in src_con.targets:
            new_target = new_con.targets.new()
            new_target.target = target_item.target
            new_target.subtarget = target_item.subtarget

    transfer_drivers(source_obj, target_obj, 'constraints', constraint_name)