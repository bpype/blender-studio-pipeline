# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Object, PropertyGroup, bpy_prop_collection
from bpy.utils import flip_name
from rna_prop_ui import IDPropertyGroup

# Functions to manage runtime properties, which include custom properties and add-on properties.
# These functions aim to abstract away that distinction, and also abstract away whether something is a single value,
# a PropertyGroup, or a CollectionProperty.
# Currently the minimum Blender version for this code is 5.0, but it could probably be made backwards-compatible.


def copy_all_runtime_properties(src_id, tgt_id, x_mirror=False):
    """Copy add-on and custom properties from source to target.
    Both should be the same type.
    Should support anything that supports custom properties or property registration.
    """
    for prop_name in get_all_runtime_prop_names(src_id):
        copy_runtime_property(src_id, tgt_id, prop_name, x_mirror)


def get_all_runtime_prop_names(owner):
    custom_props = list(owner.keys())
    addon_props = get_addon_prop_names(owner)
    props = custom_props + addon_props
    return props


def get_addon_prop_names(owner):
    if bpy.app.version >= (5, 0, 0):
        return list(owner.bl_system_properties_get().keys())
    else:
        return [prop_name for prop_name in owner.keys() if is_addon_prop(owner, prop_name)]


def copy_runtime_property(src_id, tgt_id, prop_name, x_mirror=False):
    """Copy add-on properties or custom properties."""
    if is_addon_prop(src_id, prop_name):
        if is_registered_addon_prop(src_id, prop_name):
            src_prop = getattr(src_id, prop_name)
            tgt_prop = getattr(tgt_id, prop_name)
            if isinstance(src_prop, bpy_prop_collection):
                copy_coll_prop(src_prop, tgt_prop, x_mirror)
            elif isinstance(src_prop, PropertyGroup):
                copy_property_group(src_prop, tgt_prop, x_mirror)
            else:
                copy_single_addon_prop(src_id, tgt_id, prop_name, x_mirror)
        else:
            if bpy.app.version >= (5, 0, 0):
                # HACK: If we need to copy add-on properties, but the add-on is not present,
                # we have to write to the system properties, which is API abuse that could
                # lose support any moment, but there is no other way to do this atm.
                try:
                    tgt_id.bl_system_properties_get()[prop_name] = src_id.bl_system_properties_get()[prop_name]
                except TypeError:
                    # Happens for at least a mysterious "booleans" custom property which seems to be an empty PropGroup. Where is it coming from!?
                    pass
            else:
                tgt_id[prop_name] = src_id[prop_name]
    else:
        copy_custom_property(src_id, tgt_id, prop_name)


def copy_property_group(src_pg: PropertyGroup, tgt_pg: PropertyGroup, x_mirror=False):
    """
    Copy the values from one PropertyGroup into another of the same type.
    Optionally, X-mirror names (e.g., ".L" <-> ".R") in strings and Object references.
    """
    assert isinstance(tgt_pg, PropertyGroup) and isinstance(src_pg, PropertyGroup)
    assert tgt_pg.__class__ == src_pg.__class__

    for prop_name in src_pg.bl_rna.properties.keys():
        if prop_name in ('rna_type', 'bl_rna'):
            continue
        if not src_pg.is_property_set(prop_name):
            tgt_pg.property_unset(prop_name)
            continue
        value = getattr(src_pg, prop_name)
        if isinstance(value, bpy_prop_collection):
            tgt_collprop = getattr(tgt_pg, prop_name)
            copy_coll_prop(value, tgt_collprop)
        elif isinstance(value, PropertyGroup):
            copy_property_group(value, getattr(tgt_pg, prop_name), x_mirror)
        else:
            copy_single_addon_prop(src_pg, tgt_pg, prop_name, x_mirror)
    for prop_name in src_pg.keys():
        if is_custom_prop(src_pg, prop_name):
            # PropertyGroups also support custom properties.
            copy_custom_property(src_pg, tgt_pg, prop_name, x_mirror)


def copy_coll_prop(src_cp, tgt_cp, x_mirror=False):
    tgt_cp.clear()
    for src_pg in src_cp:
        assert isinstance(src_pg, PropertyGroup)
        tgt_pg = tgt_cp.add()
        copy_property_group(src_pg, tgt_pg, x_mirror)


def copy_custom_property(src_owner, tgt_owner, prop_name, x_mirror=False):
    """Copy a custom property (one that was created via the UI or via Python dictionary syntax)."""
    prop = src_owner.id_properties_ui(prop_name)
    assert prop, f'Property "{prop_name}" not found in {src_owner}.'
    value = src_owner[prop_name]
    if x_mirror:
        value = x_mirror_value(value)

    tgt_owner[prop_name] = value
    new_prop = tgt_owner.id_properties_ui(prop_name)
    new_prop.update_from(prop)


def copy_single_addon_prop(src, tgt, prop_name, x_mirror=False) -> True:
    if src.is_property_readonly(prop_name):
        # This "early" exit has to come after CollectionProperty & PropertyGroup
        # checks, since they are technically read-only.
        return False

    value = getattr(src, prop_name)
    if x_mirror:
        value = x_mirror_value(value)

    setattr(tgt, prop_name, value)
    return True


def x_mirror_value(value):
    if isinstance(value, str):
        return flip_name(value)
    elif isinstance(value, Object):
        get_opposite_obj(value)
    else:
        return value


def get_opposite_obj(obj: Object) -> Object:
    """Return the X-mirrored version of a Blender object by name (and library if linked)."""
    flipped_name = flip_name(obj.name)
    lib = obj.library
    return (bpy.data.objects.get((lib, flipped_name)) if lib else bpy.data.objects.get(flipped_name)) or obj


def is_addon_prop(owner, prop_name):
    if bpy.app.version >= (5, 0, 0):
        return prop_name in owner.bl_system_properties_get().keys()
    else:
        # NOTE: I don't think it's possible to detect pre-5.0 non-PropertyGroup/CollectionProperty non-registered add-on properties.
        # They just behave completely as custom properties.
        return prop_name in owner and (
            isinstance(owner[prop_name], IDPropertyGroup) or isinstance(owner[prop_name], list)
        )


def is_registered_addon_prop(owner, prop_name):
    return is_addon_prop(owner, prop_name) and prop_name in owner.bl_rna.properties


def is_custom_prop(owner, prop_name):
    return prop_name in owner.keys() and not is_addon_prop(owner, prop_name)


def remove_property(obj, prop_name):
    if is_custom_prop(obj, prop_name):
        del obj[prop_name]
    if is_registered_addon_prop(obj, prop_name):
        obj.property_unset(prop_name)
    elif is_addon_prop(obj, prop_name):
        disabled_addon_props = obj.bl_system_properties_get()
        del disabled_addon_props[prop_name]
    else:
        raise KeyError(f"{prop_name} not found in {obj.name}")
