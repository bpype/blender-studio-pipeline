# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

def transfer_active_color_attribute_index(target_obj, active_color_name):
    # active_color_name = source_obj.data.color_attributes.active_color_name
    if active_color_name is None or active_color_name == "":
        return
    for color_attribute in target_obj.data.color_attributes:
        if color_attribute.name == active_color_name:
            target_obj.data.color_attributes.active_color = color_attribute


def transfer_active_uv_layer_index(target_obj, active_uv_name):
    # active_uv = source_obj.data.uv_layers.active
    if active_uv_name is None or active_uv_name == "":
        return
    for uv_layer in target_obj.data.uv_layers:
        if uv_layer.name == active_uv_name:
            target_obj.data.uv_layers.active = uv_layer
