import bpy
from ..transfer_util import check_transfer_data_entry
from ...task_layer import get_transfer_data_owner

from .... import constants, logging


def transfer_custom_prop(prop_name, target_obj, source_obj):

    if target_obj.get(prop_name):
        remove_custom_prop(target_obj, prop_name)

    if hasattr(source_obj[prop_name], "to_dict"):
        # Copy add-on data & previously registered add-on data
        target_obj[prop_name] = source_obj[prop_name].to_dict()
    elif type(source_obj[prop_name]) == list:
        # Copy list data
        target_obj[prop_name] = source_obj[prop_name].copy()
    else:
        # Copy custom properties created via UI
        prop = source_obj.id_properties_ui(prop_name)
        target_obj[prop_name] = source_obj[prop_name]
        new_prop = target_obj.id_properties_ui(prop_name)
        new_prop.update_from(prop)


def custom_prop_clean(obj):
    cleaned_item_names = set()
    data_list = get_valid_props(obj)
    for item in data_list:
        matches = check_transfer_data_entry(
            obj.transfer_data_ownership,
            item,
            constants.CUSTOM_PROP_KEY,
        )
        if len(matches) == 0 or item in constants.INVALID_CUSTOM_PROP_KEYS:
            cleaned_item_names.add(item)
            remove_custom_prop(obj, item)
            data_list.remove(item)

    return cleaned_item_names


def remove_invalid_props(obj):
    removed_item_indexes = set()

    for index, item in enumerate(obj.transfer_data_ownership):
        if item.name in constants.INVALID_CUSTOM_PROP_KEYS:
            removed_item_indexes.add(index)

    for index in sorted(removed_item_indexes, reverse=True):
        obj.transfer_data_ownership.remove(index)

    return


def custom_prop_is_missing(transfer_data_item):
    obj = transfer_data_item.id_data
    if transfer_data_item.type == constants.CUSTOM_PROP_KEY and not transfer_data_item[
        "name"
    ] in get_valid_props(obj):
        return True


def init_custom_prop(scene, obj):
    asset_pipe = scene.asset_pipeline
    transfer_data = obj.transfer_data_ownership
    td_type_key = constants.CUSTOM_PROP_KEY

    remove_invalid_props(obj)

    for prop_name in get_valid_props(obj):
        matches = check_transfer_data_entry(transfer_data, prop_name, td_type_key)
        if len(matches) == 0:
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


def get_valid_props(obj):
    props = []
    for key in obj.keys():
        # Skip if prop is defined by an add-on (registered at obj level)
        if key not in constants.INVALID_CUSTOM_PROP_KEYS:
            props.append(key)
    return props


def remove_custom_prop(obj, prop_name):
    with bpy.context.temp_override(object=obj):
        bpy.ops.wm.properties_remove(data_path="object", property_name=prop_name)
