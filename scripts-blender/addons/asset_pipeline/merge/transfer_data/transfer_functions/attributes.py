# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import mathutils
import bmesh
import numpy as np
from .transfer_function_util.proximity_core import (
    tris_per_face,
    closest_face_to_point,
    closest_tri_on_face,
    is_obdata_identical,
    transfer_corner_data,
)
from ..transfer_util import check_transfer_data_entry
from ...naming import merge_get_basename
from ...task_layer import get_transfer_data_owner
from .... import constants, logging


def attributes_get_editable(attributes):
    return [
        attribute
        for attribute in attributes
        if not (
            attribute.is_internal
            or attribute.is_required
            # Material Index is part of material transfer and should be skipped
            or attribute.name == 'material_index'
        )
    ]


def attribute_clean(obj):
    logger = logging.get_logger()
    if obj.type != "MESH":
        return
    attributes = attributes_get_editable(obj.data.attributes)
    attributes_to_remove = []
    for attribute in attributes:
        matches = check_transfer_data_entry(
            obj.transfer_data_ownership,
            merge_get_basename(attribute.name),
            constants.ATTRIBUTE_KEY,
        )
        if len(matches) == 0:
            attributes_to_remove.append(attribute.name)

    for attribute_name_to_remove in reversed(attributes_to_remove):
        attribute_to_remove = obj.data.attributes.get(attribute_name_to_remove)
        logger.debug(f"Cleaning attribute {attribute.name}")
        obj.data.attributes.remove(attribute_to_remove)


def attribute_is_missing(transfer_data_item):
    obj = transfer_data_item.id_data
    if obj.type != "MESH":
        return
    attributes = attributes_get_editable(obj.data.attributes)
    attribute_names = [attribute.name for attribute in attributes]
    if (
        transfer_data_item.type == constants.ATTRIBUTE_KEY
        and not transfer_data_item["name"] in attribute_names
    ):
        return True


def init_attributes(scene, obj):
    asset_pipe = scene.asset_pipeline
    if obj.type != "MESH":
        return
    transfer_data = obj.transfer_data_ownership
    td_type_key = constants.ATTRIBUTE_KEY
    for atttribute in attributes_get_editable(obj.data.attributes):
        # Only add new ownership transfer_data_item if vertex group doesn't have an owner
        matches = check_transfer_data_entry(transfer_data, atttribute.name, td_type_key)
        if len(matches) == 0:
            task_layer_owner, auto_surrender = get_transfer_data_owner(
                asset_pipe, td_type_key, atttribute.name
            )
            asset_pipe.add_temp_transfer_data(
                name=atttribute.name,
                owner=task_layer_owner,
                type=td_type_key,
                obj_name=obj.name,
                surrender=auto_surrender,
            )


def transfer_attribute(
    attribute_name: str,
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
):
    source_attributes = source_obj.data.attributes
    target_attributes = target_obj.data.attributes
    source_attribute = source_attributes.get(attribute_name)
    target_attribute = target_attributes.get(attribute_name)

    logger = logging.get_logger()
    if not source_attribute:
        logger.debug(f"Failed to find attribute to transfer: {attribute_name}")
        return

    if target_attribute:
        target_attributes.remove(target_attribute)

    target_attribute = target_attributes.new(
        name=attribute_name,
        type=source_attribute.data_type,
        domain=source_attribute.domain,
    )

    if not is_obdata_identical(source_obj, target_obj):
        proximity_transfer_single_attribute(
            source_obj, target_obj, source_attribute, target_attribute
        )
        return

    for source_data_item in source_attribute.data.items():
        index = source_data_item[0]
        source_data = source_data_item[1]
        keys = set(source_data.bl_rna.properties.keys()) - set(
            bpy.types.Attribute.bl_rna.properties.keys()
        )
        for key in list(keys):
            target_data = target_attribute.data[index]
            setattr(target_data, key, getattr(source_data, key))


def proximity_transfer_single_attribute(
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    source_attribute: bpy.types.Attribute,
    target_attribute: bpy.types.Attribute,
):
    # src_dat = source_obj.data
    # tgt_dat = target_obj.data
    # if type(src_dat) is not type(tgt_dat) or not (src_dat or tgt_dat):
    #     return False
    # if type(tgt_dat) is not bpy.types.Mesh:  # TODO: support more types
    #     return False

    # If target attribute already exists, remove it.
    # tgt_attr = tgt_dat.attributes.get(source_attribute.name)
    # if tgt_attr is not None:
    #     try:
    #         tgt_dat.attributes.remove(tgt_attr)
    #     except RuntimeError:
    #         # Built-ins like "position" cannot be removed, and should be skipped.
    #         return

    # Create target attribute.
    # target_attribute = tgt_dat.attributes.new(
    #     source_attribute.name, source_attribute.data_type, source_attribute.domain
    # )
    logger = logging.get_logger()

    data_sfx = {
        'INT8': 'value',
        'INT': 'value',
        'FLOAT': 'value',
        'FLOAT2': 'vector',
        'BOOLEAN': 'value',
        'STRING': 'value',
        'BYTE_COLOR': 'color',
        'FLOAT_COLOR': 'color',
        'FLOAT_VECTOR': 'vector',
    }

    data_sfx = data_sfx[source_attribute.data_type]

    # if topo_match:
    #     # TODO: optimize using foreach_get/set rather than loop
    #     for i in range(len(source_attribute.data)):
    #         setattr(tgt_attr.data[i], data_sfx, getattr(source_attribute.data[i], data_sfx))
    #     return

    # proximity fallback
    if source_attribute.data_type == 'STRING':
        # TODO: add NEAREST transfer fallback for attributes without interpolation
        logger.warning(
            f'Proximity based transfer for generic attributes of type STRING not supported yet. Skipping attribute {source_attribute.name} on {target_obj}.'
        )
        return

    domain = source_attribute.domain
    if (
        domain == 'POINT'
    ):  # TODO: deduplicate interpolated point domain proximity transfer
        bm_source = bmesh.new()
        bm_source.from_mesh(source_obj.data)
        bm_source.faces.ensure_lookup_table()

        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

        tris_dict = tris_per_face(bm_source)

        for i, vert in enumerate(target_obj.data.vertices):
            p = vert.co
            face = closest_face_to_point(bm_source, p, bvh_tree)

            (tri, point) = closest_tri_on_face(tris_dict, face, p)
            if not tri:
                continue
            weights = mathutils.interpolate.poly_3d_calc(
                [tri[i].vert.co for i in range(3)], point
            )

            if data_sfx in ['color']:
                vals_weighted = [
                    weights[i]
                    * (
                        np.array(
                            getattr(source_attribute.data[tri[i].vert.index], data_sfx)
                        )
                    )
                    for i in range(3)
                ]
            else:
                vals_weighted = [
                    weights[i]
                    * (getattr(source_attribute.data[tri[i].vert.index], data_sfx))
                    for i in range(3)
                ]
            setattr(target_attribute.data[i], data_sfx, sum(np.array(vals_weighted)))
        return
    elif domain == 'EDGE':
        # TODO support proximity fallback for generic edge attributes
        logger.warning(
            f'Proximity based transfer of generic edge attributes not supported yet. Skipping attribute {source_attribute.name} on {target_obj}.'
        )
        return
    elif domain == 'FACE':
        bm_source = bmesh.new()
        bm_source.from_mesh(source_obj.data)
        bm_source.faces.ensure_lookup_table()

        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)
        for i, face in enumerate(target_obj.data.polygons):
            p_target = face.center
            closest_face = closest_face_to_point(bm_source, p_target, bvh_tree)
            setattr(
                target_attribute.data[i],
                data_sfx,
                getattr(source_attribute.data[closest_face.index], data_sfx),
            )
        return
    elif domain == 'CORNER':
        transfer_corner_data(
            source_obj,
            target_obj,
            source_attribute.data,
            target_attribute.data,
            data_suffix=data_sfx,
        )
        return
