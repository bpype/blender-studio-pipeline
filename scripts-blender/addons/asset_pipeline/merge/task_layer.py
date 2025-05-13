# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from .. import constants
from .. import config


def get_default_task_layer_owner(td_type: str, name="") -> [str, bool]:
    if td_type == constants.ATTRIBUTE_KEY:
        if name in config.ATTRIBUTE_DEFAULTS:
            return (
                config.ATTRIBUTE_DEFAULTS[name]['default_owner'],
                config.ATTRIBUTE_DEFAULTS[name]['auto_surrender'],
            )

    try:
        return (
            config.TRANSFER_DATA_DEFAULTS[td_type]['default_owner'],
            config.TRANSFER_DATA_DEFAULTS[td_type]['auto_surrender'],
        )
    except KeyError:
        from .. import logging

        logger = logging.get_logger()
        logger.fatal(f"Task Layer File missing key {td_type}")
        # TODO stop execution of operator at this point if this fails


def get_transfer_data_owner(
    asset_pipe: bpy.types.PropertyGroup,
    td_type_key: str,
    name="",
) -> [str, bool]:
    default_tl, auto_surrender = get_default_task_layer_owner(td_type_key, name)
    if default_tl in asset_pipe.get_local_task_layers():
        # If the default owner is local to the file, don't use auto_surrender
        return default_tl, False
    else:
        # If the default owner is not local, pass auto surrender value
        return asset_pipe.get_local_task_layers()[0], auto_surrender


def draw_task_layer_selection(
    layout: bpy.types.UILayout,
    data: bpy.types.CollectionProperty or bpy.types.ID,
    show_all_task_layers=False,
    show_local_task_layers=False,
    text="",
    data_owner_name="",
    current_data_owner=None,
) -> None:
    """Draw an prop search UI for ownership of either OBJ/COL or Task Layer.
    It has three modes, 'Show All Task Layers" "Show All Task Layers Greyed Out" and
    "Only Show Local Task Layers"

    - When the property is already set to a local task layer show: "Only Show Local Task Layers"
    - When a property is owned by an external task layer: "Show All Task Layers Greyed Out" so they user cannot edit it
    - When a user is overriding or the object is new (using default ownership): "Show All Task Layers"
    Args:
        layout (bpy.types.UILayout): Any UI Layout element like self.layout or row
        data (bpy.types.CollectionProperty or bpy.types.ID): Object, Collection or Transferable Data Item
        show_all_task_layers (bool, optional): Used when user is overriding or default ownership is set. Defaults to False.
        show_local_task_layers (bool, optional): Force Showing Local Task Layers Only. Defaults to False.
        text (str, optional): Title of prop search. Defaults to "".
        data_owner_name(str, optional): Name of Data if it needs to be specified
        current_data_owner(str, optional): Property that is named by data_owner_name so it can be checked, property should return a string
    """

    # Set data_owner_name based on type of it hasn't been passed
    if data_owner_name == "":
        # These rna_type.names are defined by class names in props.py
        if data.rna_type.name in ["AssetTransferData", 'AssetTransferDataTemp']:
            data_owner_name = "owner"
        else:
            data_owner_name = "asset_id_owner"

    # Get the current data owner from OBJ/COL or Transferable Data Item if it hasn't been passed
    if current_data_owner is None:
        current_data_owner = data.get(data_owner_name)

    asset_pipe = bpy.context.scene.asset_pipeline

    if show_all_task_layers == True:
        # Show All Task Layers
        layout.prop_search(
            data,
            data_owner_name,
            asset_pipe,
            'all_task_layers',
            text=text,
        )
        return
    if (
        current_data_owner not in [tl.name for tl in asset_pipe.local_task_layers]
        and not show_local_task_layers
    ):
        # Show All Task Layers Greyed Out
        layout.enabled = False
        layout.prop_search(
            data,
            data_owner_name,
            asset_pipe,
            'all_task_layers',
            text=text,
        )
        return
    else:
        # Only Show Local Task Layers
        layout.prop_search(
            data,
            data_owner_name,
            asset_pipe,
            'local_task_layers',
            text=text,
        )
