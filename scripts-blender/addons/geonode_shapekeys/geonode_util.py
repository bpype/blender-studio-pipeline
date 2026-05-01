from typing import Any

import bpy
from bpy.types import Modifier


def geomod_get_identifier(modifier: Modifier, param_name: str, must_exist=False) -> str:
    if hasattr(modifier.node_group, 'interface'):
        # 4.0+
        input = modifier.node_group.interface.items_tree.get(param_name)
    else:
        # 3.6
        input = modifier.node_group.inputs.get(param_name)

    if input:
        return input.identifier
    elif must_exist:
        raise ValueError("No such Modifier socket: ", param_name, "On modifier: ", modifier.name)


def geomod_get_data_path(modifier: Modifier, param_name: str) -> str:
    identifier = geomod_get_identifier(modifier, param_name)
    if bpy.app.version >= (5, 2):
        return f'modifiers["{modifier.name}"].properties.inputs.{identifier}.value'
    return f'modifiers["{modifier.name}"]["{identifier}"]'


def geomod_set_param_value(modifier: Modifier, param_name: str, param_value: Any):
    input_id = geomod_get_identifier(modifier, param_name)
    if bpy.app.version >= (5, 2):
        getattr(modifier.properties.inputs, input_id).value = param_value
    else:
        # Must use setattr, see T103865.
        setattr(modifier, f'["{input_id}"]', param_value)


def geomod_get_param_value(modifier: Modifier, param_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    if not input_id:
        return
    if bpy.app.version >= (5, 2):
        return getattr(modifier.properties.inputs, input_id).value
    return modifier[input_id]


def geomod_set_param_use_attribute(modifier: Modifier, param_name: str, use_attrib: bool):
    input_id = geomod_get_identifier(modifier, param_name)
    if bpy.app.version >= (5, 2):
        getattr(modifier.properties.inputs, input_id).type = "ATTRIBUTE" if use_attrib else "VALUE"
    else:
        modifier[input_id + "_use_attribute"] = use_attrib


def geomod_set_param_attribute(modifier: Modifier, param_name: str, attrib_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    if bpy.app.version >= (5, 2):
        prop = getattr(modifier.properties.inputs, input_id)
        prop.type = "ATTRIBUTE"
        prop.attribute_name = attrib_name
    else:
        modifier[input_id + "_use_attribute"] = True
        modifier[input_id + "_attribute_name"] = attrib_name
