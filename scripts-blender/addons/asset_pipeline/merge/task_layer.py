# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later


from bpy.types import Collection, Context, Object, Operator, PropertyGroup, UILayout

from .. import config, constants
from ..props import AssetTransferData


def get_default_task_layer_owner(td_type: str, name="") -> tuple[str, bool] | None:
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
    asset_pipe: PropertyGroup,
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
    context: Context,
    layout: UILayout,
    *,
    id: Object | Collection | AssetTransferData,
    show_all_task_layers=False,
    text="",
) -> None:
    """Draw an prop search UI for ownership of either OBJ/COL or Task Layer.
    It has three modes, 'Show All Task Layers" "Show All Task Layers Greyed Out" and
    "Only Show Local Task Layers"

    - When the property is already set to a local task layer show: "Only Show Local Task Layers"
    - When a property is owned by an external task layer: "Show All Task Layers Greyed Out" so they user cannot edit it
    - When a user is overriding or the object is new (using default ownership): "Show All Task Layers"
    Args:
        layout: UI element to draw into.
        data: ID with the ownership data.
        show_all_task_layers: True when we want to list all task layers in the production as options.
        text: Title to display for the prop_search.
        current_data_owner(str, optional): Property that is named by data_owner_name so it can be checked, property should return a string
    """

    # Get the current data owner from OBJ/COL or Transferable Data Item if it hasn't been passed

    prop_name = "owner" if hasattr(id, "owner") else "asset_id_owner"
    prop_name = "owner_selection" if hasattr(id, "owner_selection") else prop_name
    current_owner = getattr(id, prop_name)

    asset_pipe = context.scene.asset_pipeline

    row = layout.row()
    if current_owner not in asset_pipe.local_task_layers:
        show_all_task_layers = True
        if not isinstance(id, Operator):
            row.enabled = False

    if show_all_task_layers:
        row.prop_search(
            id,
            prop_name,
            asset_pipe,
            'all_task_layers',
            text=text,
        )
    else:
        row.prop_search(
            id,
            prop_name,
            asset_pipe,
            'local_task_layers',
            text=text,
        )
