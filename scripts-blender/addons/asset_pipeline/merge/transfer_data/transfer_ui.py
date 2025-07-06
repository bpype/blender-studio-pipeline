# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ... import constants
from ..task_layer import draw_task_layer_selection


def draw_transfer_data_type(
    layout: bpy.types.UILayout, transfer_data: bpy.types.CollectionProperty
) -> None:
    """Draw UI Element for items of a Transferable Data type"""
    asset_pipe = bpy.context.scene.asset_pipeline
    if transfer_data == []:
        return
    name, icon = constants.TRANSFER_DATA_TYPES[transfer_data[0].type]

    box = layout.box()
    header, panel = box.panel(transfer_data[0].obj_name + name, default_closed=True)
    header.label(text=name, icon=icon)
    if not panel:
        return

    box = panel.box()
    for transfer_data_item in transfer_data:
        row = box.row()
        row.label(text=f"{transfer_data_item.name}: ")

        if transfer_data_item.get("surrender"):
            enabled = (
                False
                if transfer_data_item.owner in asset_pipe.get_local_task_layers()
                else True
            )
            # Disable entire row if the item is surrender (prevents user from un-surrendering)
            row.enabled = enabled
            col = row.column()
            col.operator(
                "assetpipe.update_surrendered_transfer_data"
            ).transfer_data_item_name = transfer_data_item.name

        # New Row inside a column because draw_task_layer_selection() will enable/disable the entire row
        # Only need this to affect itself and the "surrender" property
        col = row.column()
        task_layer_row = col.row()

        draw_task_layer_selection(
            layout=task_layer_row,
            data=transfer_data_item,
        )
        surrender_icon = (
            "ORPHAN_DATA" if transfer_data_item.get("surrender") else "HEART"
        )
        task_layer_row.prop(
            transfer_data_item, "surrender", text="", icon=surrender_icon
        )


def draw_transfer_data(
    transfer_data: bpy.types.CollectionProperty, layout: bpy.types.UILayout
) -> None:
    """Draw UI List of Transferable Data"""
    vertex_groups = []
    material_slots = []
    modifiers = []
    constraints = []
    custom_props = []
    shape_keys = []
    attributes = []
    parent = []

    for transfer_data_item in transfer_data:
        if transfer_data_item.type == constants.VERTEX_GROUP_KEY:
            vertex_groups.append(transfer_data_item)
        if transfer_data_item.type == constants.MATERIAL_SLOT_KEY:
            material_slots.append(transfer_data_item)
        if transfer_data_item.type == constants.MODIFIER_KEY:
            modifiers.append(transfer_data_item)
        if transfer_data_item.type == constants.CONSTRAINT_KEY:
            constraints.append(transfer_data_item)
        if transfer_data_item.type == constants.CUSTOM_PROP_KEY:
            custom_props.append(transfer_data_item)
        if transfer_data_item.type == constants.SHAPE_KEY_KEY:
            shape_keys.append(transfer_data_item)
        if transfer_data_item.type == constants.ATTRIBUTE_KEY:
            attributes.append(transfer_data_item)
        if transfer_data_item.type == constants.PARENT_KEY:
            parent.append(transfer_data_item)

    draw_transfer_data_type(layout, vertex_groups)
    draw_transfer_data_type(layout, modifiers)
    draw_transfer_data_type(layout, material_slots)
    draw_transfer_data_type(layout, constraints)
    draw_transfer_data_type(layout, custom_props)
    draw_transfer_data_type(layout, shape_keys)
    draw_transfer_data_type(layout, attributes)
    draw_transfer_data_type(layout, parent)
