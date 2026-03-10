# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import ID, FCurve


def copy_driver(from_fcurve: FCurve, target: ID, data_path=None, index=None) -> FCurve:
    """Copy an existing FCurve containing a driver to a new ID, by creating a copy
    of the existing driver on the target ID.

    Args:
        from_fcurve (FCurve): FCurve containing a driver
        target (ID): ID that can have drivers added to it
        data_path (_type_, optional): Data Path of existing driver. Defaults to None.
        index (_type_, optional): array index of the property drive. Defaults to None.

    Returns:
        FCurve: Fcurve containing copy of driver on target ID
    """

    if not target.animation_data:
        target.animation_data_create()

    new_fc = target.animation_data.drivers.from_existing(src_driver=from_fcurve)

    if data_path:
        new_fc.data_path = data_path
    if index:
        new_fc.array_index = index

    return new_fc


def find_drivers(id: ID, target_type: str, target_name: str) -> list[FCurve]:
    """Return a filtered list of driver FCurves on the given ID.

    Args:
        id: ID whose drivers should be searched.
        target_type: Part of the data path for filtering drivers.
        target_name (str): Name of data found in driver path, e.g. modifier's name

    Returns:
        list[FCurve]: List of FCurves containing drivers that match type & name
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


def transfer_drivers(source_id: ID, target_id: ID, target_type: str, target_name: str) -> None:
    """Copy any new drivers from source_id to target_id,
    and remove any drivers on target_id not present on source_id.

    Args:
        source_id (ID): Source ID, containing drivers to copy
        target_id (ID): Target ID, which will recieve the drivers from source
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


def cleanup_drivers(id: ID, target_type: str, target_name: str) -> None:
    """Remove all drivers for transfer data that has been removed.

    Args:
        object (ID): ID, which has drivers to remove
        target_type (str): Name of driver target's type, like `modifier` or `constraint`
        target_name (str): Name of driver target, e.g. name of a modifier or contraint
    """
    target_fcurves = find_drivers(id, target_type, target_name)
    for fcurve in target_fcurves:
        id.animation_data.drivers.remove(fcurve)
