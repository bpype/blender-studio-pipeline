from typing import Any

from bpy.types import Modifier


def geomod_get_identifier(modifier: Modifier, param_name: str) -> str:
    if hasattr(modifier.node_group, 'interface'):
        # 4.0
        input = modifier.node_group.interface.items_tree.get(param_name)
    else:
        # 3.6
        input = modifier.node_group.inputs.get(param_name)

    if input:
        return input.identifier


def geomod_get_data_path(modifier: Modifier, param_name: str) -> str:
    return f'modifiers["{modifier.name}"]["{geomod_get_identifier(modifier, param_name)}"]'


def geomod_set_param_value(modifier: Modifier, param_name: str, param_value: Any):
    input_id = geomod_get_identifier(modifier, param_name)
    # Note: Must use setattr, see T103865.
    setattr(modifier, f'["{input_id}"]', param_value)


def geomod_get_param_value(modifier: Modifier, param_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    return modifier[input_id]


def geomod_set_param_use_attribute(modifier: Modifier, param_name: str, use_attrib: bool):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id + "_use_attribute"] = use_attrib


def geomod_set_param_attribute(modifier: Modifier, param_name: str, attrib_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id + "_use_attribute"] = True
    modifier[input_id + "_attribute_name"] = attrib_name
