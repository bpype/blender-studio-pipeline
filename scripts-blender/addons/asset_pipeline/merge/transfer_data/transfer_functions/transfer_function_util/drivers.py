import bpy
from rigify.utils.misc import copy_attributes


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
    if not data_path:
        data_path = from_fcurve.data_path

    new_fc = None
    if index:
        new_fc = target.driver_add(data_path, index)
    else:
        new_fc = target.driver_add(data_path)

    copy_attributes(from_fcurve, new_fc)
    copy_attributes(from_fcurve.driver, new_fc.driver)

    # Remove default modifiers, variables, etc.
    for m in new_fc.modifiers:
        new_fc.modifiers.remove(m)
    for v in new_fc.driver.variables:
        new_fc.driver.variables.remove(v)

    # Copy modifiers
    for m1 in from_fcurve.modifiers:
        m2 = new_fc.modifiers.new(type=m1.type)
        copy_attributes(m1, m2)

    # Copy variables
    for v1 in from_fcurve.driver.variables:
        v2 = new_fc.driver.variables.new()
        copy_attributes(v1, v2)
        for i in range(len(v1.targets)):
            copy_attributes(v1.targets[i], v2.targets[i])

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
