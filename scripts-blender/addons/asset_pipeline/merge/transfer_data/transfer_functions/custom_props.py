# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..transfer_util import find_ownership_data
from ...task_layer import get_transfer_data_owner

from .... import constants
from .transfer_function_util.properties import (
    get_all_runtime_prop_names,
    remove_property,
    copy_runtime_property,
)

def transfer_custom_prop(prop_name, target_obj, source_obj):
    copy_runtime_property(source_obj, target_obj, prop_name)


def custom_prop_clean(obj):
    cleaned_item_names = set()
    for key in get_valid_runtime_prop_names(obj):
        ownership_data = find_ownership_data(
            obj.transfer_data_ownership,
            key,
            constants.CUSTOM_PROP_KEY,
        )
        if not ownership_data:
            cleaned_item_names.add(key)
            remove_property(obj, key)

    return cleaned_item_names


def custom_prop_is_missing(transfer_data_item):
    obj = transfer_data_item.id_data
    return transfer_data_item.type == constants.CUSTOM_PROP_KEY and not transfer_data_item["name"] in get_valid_runtime_prop_names(obj)


def init_custom_prop(scene, obj):
    asset_pipe = scene.asset_pipeline
    transfer_data = obj.transfer_data_ownership
    td_type_key = constants.CUSTOM_PROP_KEY

    for prop_name in get_valid_runtime_prop_names(obj):
        ownership_data = find_ownership_data(transfer_data, prop_name, td_type_key)
        if not ownership_data:
            task_layer_owner, auto_surrender = get_transfer_data_owner(
                asset_pipe, td_type_key, prop_name
            )
            asset_pipe.add_temp_transfer_data(
                name=prop_name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def get_valid_runtime_prop_names(id):
    all_props = get_all_runtime_prop_names(id)
    return [p for p in all_props if p not in constants.ADDON_OWN_PROPERTIES]
