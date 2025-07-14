# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import PropertyGroup, bpy_prop_collection, Object
from ..transfer_util import check_transfer_data_entry
from ...task_layer import get_transfer_data_owner
from bpy.utils import flip_name

from .... import constants


def transfer_custom_prop(prop_name, target_obj, source_obj):
    if is_addon_prop(source_obj, prop_name):
        src_pg = getattr(source_obj, prop_name)
        tgt_pg = getattr(target_obj, prop_name)
        if prop_name in source_obj.bl_rna.properties:
            copy_property_group(src_pg, tgt_pg)
        else:
            # HACK: If we need to transfer add-on data, but the add-on is not present, 
            # we have to write to the system properties, which is API abuse that could
            # lose support any moment, but there is no other way to do this atm.
            target_obj.bl_system_properties_get()[prop_name] = source_obj.bl_system_properties_get()[prop_name]
    else:
        # Copy custom properties created via UI
        prop = source_obj.id_properties_ui(prop_name)
        target_obj[prop_name] = source_obj[prop_name]
        new_prop = target_obj.id_properties_ui(prop_name)
        new_prop.update_from(prop)


def is_addon_prop(obj, key):
    return key in obj.bl_system_properties_get().keys()


def copy_property_group(src_pg: PropertyGroup, dst_pg: PropertyGroup, x_mirror=False):
    """
    Copy the values from one PropertyGroup into another of the same type.
    Optionally, X-mirror names (e.g., ".L" <-> ".R") in strings and Object references.
    """
    assert isinstance(dst_pg, PropertyGroup) and isinstance(src_pg, PropertyGroup)
    assert dst_pg.__class__ == src_pg.__class__

    for key in src_pg.bl_rna.properties.keys():
        if key in ('rna_type', 'bl_rna'):
            continue
        if not src_pg.is_property_set(key):
            dst_pg.property_unset(key)
            continue
        value = getattr(src_pg, key)
        if isinstance(value, bpy_prop_collection):
            dst_coll = getattr(dst_pg, key)
            dst_coll.clear()
            for src_entry in value:
                if isinstance(src_entry, PropertyGroup):
                    dst_entry = dst_coll.add()
                    copy_property_group(src_entry, dst_entry, x_mirror)
        elif isinstance(value, PropertyGroup):
            copy_property_group(value, getattr(dst_pg, key), x_mirror)
        elif src_pg.is_property_readonly(key):
            # This has to come after CollectionProperty and PropertyGroup checks, 
            # since they are technically read-only.
            continue
        elif isinstance(value, str):
            setattr(dst_pg, key, flip_name(value) if x_mirror else value)
        elif isinstance(value, Object):
            setattr(dst_pg, key, get_opposite_obj(value) if x_mirror else value)
        else:
            setattr(dst_pg, key, value)


def get_opposite_obj(obj: Object) -> Object:
    """Return the X-mirrored version of a Blender object by name (and library if linked)."""
    flipped_name = flip_name(obj.name)
    lib = obj.library
    return (
        bpy.data.objects.get((lib, flipped_name)) if lib else
        bpy.data.objects.get(flipped_name)
    ) or obj


def custom_prop_clean(obj):
    cleaned_item_names = set()
    for key in get_all_runtime_prop_names(obj):
        matches = check_transfer_data_entry(
            obj.transfer_data_ownership,
            key,
            constants.CUSTOM_PROP_KEY,
        )
        if len(matches) == 0:
            cleaned_item_names.add(key)
            remove_property(obj, key)

    return cleaned_item_names


def custom_prop_is_missing(transfer_data_item):
    obj = transfer_data_item.id_data
    return transfer_data_item.type == constants.CUSTOM_PROP_KEY and not transfer_data_item["name"] in get_all_runtime_prop_names(obj)


def init_custom_prop(scene, obj):
    asset_pipe = scene.asset_pipeline
    transfer_data = obj.transfer_data_ownership
    td_type_key = constants.CUSTOM_PROP_KEY

    for prop_name in get_all_runtime_prop_names(obj):
        matches = check_transfer_data_entry(transfer_data, prop_name, td_type_key)
        if len(matches) == 0:
            task_layer_owner, auto_surrender = get_transfer_data_owner(
                asset_pipe, td_type_key, prop_name
            )
            asset_pipe.add_temp_transfer_data(
                name=prop_name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def remove_property(obj, prop_name):
    if prop_name in obj:
        del obj[prop_name]
    elif prop_name in obj.bl_rna.properties:
        obj.property_unset(prop_name)
    elif prop_name in obj.bl_system_properties_get():
        disabled_addon_props = obj.bl_system_properties_get()
        del disabled_addon_props[prop_name]
    else:
        raise KeyError(f"{prop_name} not found in {obj.name}")


def get_all_runtime_prop_names(owner):
    custom_props = list(owner.keys())
    addon_props = list(owner.bl_system_properties_get().keys())
    props = custom_props + addon_props
    props = [p for p in props if p not in constants.ADDON_OWN_PROPERTIES]
    return props
