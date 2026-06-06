# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Compatibility wrappers for the GeoNodes modifier input API.

Blender 5.2 replaced dict-style custom-property access on GeoNodes modifiers
with proper RNA properties.  All modifier input reads and writes in this add-on
go through these helpers so version branching stays in one place.

  Before 5.2:  modifier["identifier"] = value
  5.2+:        modifier.properties.inputs.identifier.value = value
"""

from typing import Any
import bpy
from bpy.types import NodesModifier, UILayout, NodeTreeInterfaceSocket


_ICON_FOR_SOCKET = {
    bpy.types.NodeTreeInterfaceSocketObject: 'OBJECT_DATA',
    bpy.types.NodeTreeInterfaceSocketMaterial: 'MATERIAL',
    bpy.types.NodeTreeInterfaceSocketImage: 'IMAGE_DATA',
    bpy.types.NodeTreeInterfaceSocketCollection: 'OUTLINER_COLLECTION',
}

_DATA_COLLECTION_FOR_SOCKET = {
    bpy.types.NodeTreeInterfaceSocketMaterial: 'materials',
    bpy.types.NodeTreeInterfaceSocketImage: 'images',
    bpy.types.NodeTreeInterfaceSocketCollection: 'collections',
}


def get_value(mod: NodesModifier, identifier: str) -> Any:
    if bpy.app.version >= (5, 2, 0):
        return getattr(mod.properties.inputs, identifier).value
    return mod[identifier]


def set_value(mod: NodesModifier, identifier: str, value: Any):
    if bpy.app.version >= (5, 2, 0):
        getattr(mod.properties.inputs, identifier).value = value
    else:
        prop_ui = mod.id_properties_ui(identifier).as_dict()
        if 'items' in prop_ui.keys():
            for item in prop_ui['items']:
                if item[0] == value:
                    mod[identifier] = item[4]
                    return
            print(f"Error: Item '{value}' not found in menu '{identifier}' of modifier '{mod.name}'")
        else:
            mod[identifier] = value


def is_input_value_settable(mod: NodesModifier, identifier: str) -> bool:
    """Return True if the modifier exposes a settable input with this identifier."""
    if bpy.app.version >= (5, 2, 0):
        inp = getattr(mod.properties.inputs, identifier, None)
        return inp is not None and hasattr(inp, 'value')
    return identifier in mod.keys()


def can_input_be_attribute(mod: NodesModifier, identifier: str) -> bool:
    """Return True if this input can be driven by an attribute field."""
    if bpy.app.version >= (5, 2, 0):
        inp = getattr(mod.properties.inputs, identifier, None)
        if inp is None or not hasattr(inp, 'type'):
            return False
        return any(item.identifier == 'ATTRIBUTE'
                   for item in inp.bl_rna.properties['type'].enum_items)
    return f'{identifier}_use_attribute' in mod.keys()


def get_input_is_attribute(mod: NodesModifier, identifier: str) -> bool:
    """Return True if this input is currently being driven by an attribute field."""
    if bpy.app.version >= (5, 2, 0):
        return getattr(mod.properties.inputs, identifier).type == 'ATTRIBUTE'
    return mod[f'{identifier}_use_attribute']


def set_input_is_attribute(mod: NodesModifier, identifier: str, value: bool):
    if bpy.app.version >= (5, 2, 0):
        getattr(mod.properties.inputs, identifier).type = 'ATTRIBUTE' if value else 'VALUE'
    else:
        mod[f'{identifier}_use_attribute'] = value


def set_attribute_name(mod: NodesModifier, identifier: str, name: str):
    if bpy.app.version >= (5, 2, 0):
        getattr(mod.properties.inputs, identifier).attribute_name = name
    else:
        mod[f'{identifier}_attribute_name'] = name


def get_enum_value_to_compare(mod: NodesModifier, identifier: str) -> list[tuple[str, str | int]]:
    """Return list of (identifier_str, comparable_value) pairs for a Menu socket.
    The comparable_value matches whatever get_value() returns for the same socket:
    an identifier string on 5.2+ (where .value is a string), an integer on older versions."""
    if bpy.app.version >= (5, 2, 0):
        inp = getattr(mod.properties.inputs, identifier)
        return [(item.identifier, item.identifier)
                for item in inp.bl_rna.properties['value'].enum_items]
    return [(item[0], item[4])
            for item in mod.id_properties_ui(identifier).as_dict()['items']]


def copy_inputs(source_mod: NodesModifier, target_mod: NodesModifier):
    """Copy all GeoNodes input values (and attribute settings) between modifiers."""
    if bpy.app.version >= (5, 2, 0):
        props = source_mod.properties
        if not props:
            return
        target_props = target_mod.properties
        for socket_name in props.inputs.keys():
            source_socket = getattr(props.inputs, socket_name, None)
            target_socket = getattr(target_props.inputs, socket_name, None)
            if source_socket and target_socket and hasattr(source_socket, "value"):
                target_socket.value = source_socket.value
    else:
        for key, value in source_mod.items():
            try:
                target_mod[key] = value
            except (TypeError, ValueError):
                target_mod[key] = type(target_mod[key])(value)


def draw_socket(
    layout: UILayout,
    mod: NodesModifier,
    v: NodeTreeInterfaceSocket,
    label: str,
    is_preset: bool,
):
    """Draw a GeoNodes input socket: value widget plus attribute toggle if supported."""
    if can_input_be_attribute(mod, v.identifier) and not v.force_non_field:
        if get_input_is_attribute(mod, v.identifier):
            _draw_attribute_name(layout, mod, v.identifier, text=label)
        else:
            _draw_input_simple(layout, mod, v.identifier, text=label)
        operator_id = ('brushstroke_tools.preset_toggle_attribute' if is_preset
                       else 'brushstroke_tools.brushstrokes_toggle_attribute')
        toggle = layout.operator(operator_id, text='',
                                 depress=get_input_is_attribute(mod, v.identifier),
                                 icon='SPREADSHEET')
        toggle.modifier_name = mod.name
        toggle.input_name = v.identifier
    else:
        socket_type = type(v)
        icon = _ICON_FOR_SOCKET.get(socket_type, 'NONE')
        search_prop = _DATA_COLLECTION_FOR_SOCKET.get(socket_type)
        _draw_input_simple(
            layout, mod, v.identifier,
            search_prop=search_prop,
            text=label, icon=icon,
        )


def _draw_attribute_name(
    layout: UILayout,
    mod: NodesModifier,
    identifier: str,
    **kwargs,
):
    """Draw a modifier input's attribute-name field."""
    if bpy.app.version >= (5, 2, 0):
        layout.prop(getattr(mod.properties.inputs, identifier), 'attribute_name', **kwargs)
    else:
        layout.prop(mod, f'["{identifier}_attribute_name"]', **kwargs)


def _draw_input_simple(
    layout: UILayout,
    mod: NodesModifier,
    identifier: str,
    search_prop: str | None = None,
    **kwargs,
):
    """Draw a modifier input value widget.
    Pass search_prop for prop_search on Blender < 4.2.
    Later versions use pointers, so no need for prop_search.
    """
    if bpy.app.version >= (5, 2, 0):
        layout.prop(getattr(mod.properties.inputs, identifier), 'value', **kwargs)
    elif search_prop:
        layout.prop_search(mod, f'["{identifier}"]', bpy.data, search_prop, **kwargs)
    else:
        layout.prop(mod, f'["{identifier}"]', **kwargs)
