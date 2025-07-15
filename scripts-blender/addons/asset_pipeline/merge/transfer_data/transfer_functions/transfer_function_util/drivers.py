# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

def copy_driver(
    from_fcurve: bpy.types.FCurve, target: bpy.types.ID, data_path=None, index=None
) -> bpy.types.FCurve:
    """Copy an existing FCurve containing a driver to a new ID, by creating a copy
    of the existing driver on the target ID.

    Args:
        from_fcurve (bpy.types.FCurve): FCurve containing a driver
        target (bpy.types.ID): ID that can have drivers added to it
        data_path (_type_, optional): Data Path of existing driver. Defaults to None.
        index (_type_, optional): array index of the property drive. Defaults to None.

    Returns:
        bpy.types.FCurve: Fcurve containing copy of driver on target ID
    """

    if not target.animation_data:
        target.animation_data_create()

    new_fc = target.animation_data.drivers.from_existing(src_driver = from_fcurve)

    if data_path:
        new_fc.data_path = data_path
    if index:
        new_fc.array_index = index

    return new_fc


def find_drivers(id: bpy.types.ID, target_type: str, target_name: str) -> list[bpy.types.FCurve]:
    """_summary_

    Args:
        drivers (list[bpy.types.FCurve]): List or Collection Property containing Fcurves with drivers
        target_type (str): Name of data type found in driver data path, e.g. "modifiers"
        target_name (str): Name of data found in driver path, e.g. modifier's name

    Returns:
        list[bpy.types.FCurve]: List of FCurves containing drivers that match type & name
    """

    if not id.animation_data:
        return []

    found_drivers = []
    if id.animation_data is None or id.animation_data.drivers is None:
        return found_drivers
    drivers = id.animation_data.drivers
    for driver in drivers:
        if f'{target_type}["{target_name}"]' in driver.data_path:
            found_drivers.append(driver)
    return found_drivers


def transfer_drivers(
    source_id: bpy.types.ID, target_id: bpy.types.ID, target_type: str, target_name: str
) -> None:
    """Transfers Drivers from one ID to another, will copy and new drivres from source to from
    source to target, and will remove any drivers on the target that are not in the source.

    Args:
        source_id (bpy.types.ID): Source ID, containing drivers to copy
        target_id (bpy.types.ID): Target ID, which will recieve the drivers from source
        target_type (str): Name of driver target's type, like `modifier` or `constraint`
        target_name (str): Name of driver target, e.g. name of a modifier or contraint
    """
    source_fcurves = find_drivers(source_id, target_type, target_name)
    target_fcurves = find_drivers(target_id, target_type, target_name)

    # Clear old drivers
    for old_fcurve in list(set(target_fcurves) - set(source_fcurves)):
        target_id.animation_data.drivers.remove(old_fcurve)

    # Transfer new drivers
    for fcurve in source_fcurves:
        copy_driver(from_fcurve=fcurve, target=target_id)


def cleanup_drivers(id: bpy.types.ID, target_type: str, target_name: str) -> None:
    """Remove all drivers for transfer data that has been removed.

    Args:
        object (bpy.types.ID): ID, which has drivers to remove
        target_type (str): Name of driver target's type, like `modifier` or `constraint`
        target_name (str): Name of driver target, e.g. name of a modifier or contraint
    """
    target_fcurves = find_drivers(id, target_type, target_name)
    for fcurve in target_fcurves:
        id.animation_data.drivers.remove(fcurve)
