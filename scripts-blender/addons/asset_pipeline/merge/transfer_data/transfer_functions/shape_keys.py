import bpy
import mathutils
import bmesh
import numpy as np
from .transfer_function_util.proximity_core import (
    tris_per_face,
    closest_face_to_point,
    closest_tri_on_face,
)
from .transfer_function_util.drivers import transfer_drivers
from ..transfer_util import (
    transfer_data_item_is_missing,
    transfer_data_item_init,
    check_transfer_data_entry,
)
from ...naming import merge_get_basename
from .... import constants, logging


def shape_key_set_active(obj, shape_key_name):
    for index, shape_key in enumerate(obj.data.shape_keys.key_blocks):
        if shape_key.name == shape_key_name:
            obj.active_shape_key_index = index


def shape_keys_clean(obj):
    if obj.type != "MESH" or obj.data.shape_keys is None:
        return

    for shape_key in obj.data.shape_keys.key_blocks:
        matches = check_transfer_data_entry(
            obj.transfer_data_ownership,
            merge_get_basename(shape_key.name),
            constants.SHAPE_KEY_KEY,
        )
        if len(matches) == 0:
            obj.shape_key_remove(shape_key)


def shape_key_is_missing(transfer_data_item):
    if not transfer_data_item.type == constants.SHAPE_KEY_KEY:
        return
    obj = transfer_data_item.id_data
    if obj.type != 'MESH':
        return
    if not obj.data.shape_keys:
        return True
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.SHAPE_KEY_KEY,
        data_list=obj.data.shape_keys.key_blocks,
    )


def init_shape_keys(scene, obj):
    if obj.type != "MESH" or obj.data.shape_keys is None:
        return

    # Check that the order is legal.
    # Key Blocks must be ordered after the key they are Relative To.
    for i, kb in enumerate(obj.data.shape_keys.key_blocks):
        if kb.relative_key:
            base_shape_idx = obj.data.shape_keys.key_blocks.find(kb.relative_key.name)
            if base_shape_idx > i:
                raise Exception(
                    f'Shape Key "{kb.name}" must be ordered after its base shape "{kb.relative_key.name}" on object "{obj.name}".'
                )

    transfer_data_item_init(
        scene=scene,
        obj=obj,
        data_list=obj.data.shape_keys.key_blocks,
        td_type_key=constants.SHAPE_KEY_KEY,
    )


def transfer_shape_key(
    context: bpy.types.Context,
    shape_key_name: str,
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
):
    logger = logging.get_logger()
    if not source_obj.data.shape_keys:
        return
    sk_source = source_obj.data.shape_keys.key_blocks.get(shape_key_name)
    assert sk_source

    sk_target = None
    if not target_obj.data.shape_keys:
        sk_target = target_obj.shape_key_add()
    if not sk_target:
        sk_target = target_obj.data.shape_keys.key_blocks.get(shape_key_name)
    if not sk_target:
        sk_target = target_obj.shape_key_add()

    sk_target.name = sk_source.name
    sk_target.vertex_group = sk_source.vertex_group
    if sk_source.relative_key != sk_source:
        relative_key = None
        if target_obj.data.shape_keys:
            relative_key = target_obj.data.shape_keys.key_blocks.get(sk_source.relative_key.name)
        if relative_key:
            sk_target.relative_key = relative_key
        else:
            # If the base shape of one of our shapes was removed by another task layer,
            # the result will probably be pretty bad, but it's not a catastrophic failure.
            # Proceed with a warning.
            logger.warning(
                f'Base shape "{sk_source.relative_key.name}" of Key "{sk_source.name}" was removed from "{target_obj.name}"'
            )

    sk_target.slider_min = sk_source.slider_min
    sk_target.slider_max = sk_source.slider_max
    sk_target.value = sk_source.value
    sk_target.mute = sk_source.mute

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
        weights = mathutils.interpolate.poly_3d_calc([tri[i].vert.co for i in range(3)], point)

        vals_weighted = [
            weights[i]
            * (
                sk_source.data[tri[i].vert.index].co
                - source_obj.data.vertices[tri[i].vert.index].co
            )
            for i in range(3)
        ]
        val = mathutils.Vector(sum(np.array(vals_weighted)))
        sk_target.data[i].co = vert.co + val

    if source_obj.data.shape_keys is None:
        return

    transfer_drivers(source_obj, target_obj, 'key_blocks', shape_key_name)
