# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from mathutils import Vector, kdtree
from typing import Dict, Tuple, List
from ..transfer_util import (
    transfer_data_clean,
    transfer_data_item_is_missing,
    transfer_data_item_init,
)
from .transfer_function_util.proximity_core import (
    is_obdata_identical,
)
from .... import constants, logging


def vertex_groups_clean(obj):
    transfer_data_clean(
        obj=obj, data_list=obj.vertex_groups, td_type_key=constants.VERTEX_GROUP_KEY
    )


def vertex_group_is_missing(transfer_data_item):
    return transfer_data_item_is_missing(
        transfer_data_item=transfer_data_item,
        td_type_key=constants.VERTEX_GROUP_KEY,
        data_list=transfer_data_item.id_data.vertex_groups,
    )


def init_vertex_groups(scene, obj):
    transfer_data_item_init(
        scene=scene,
        obj=obj,
        data_list=obj.vertex_groups,
        td_type_key=constants.VERTEX_GROUP_KEY,
    )


def transfer_vertex_groups(
    vertex_group_names: List[str],
    target_obj: bpy.types.Object,
    source_obj: bpy.types.Object,
):
    logger = logging.get_logger()
    for vertex_group_name in vertex_group_names:
        if not source_obj.vertex_groups.get(vertex_group_name):
            logger.error(f"Vertex Group {vertex_group_name} not found in {source_obj.name}")
            return

    # If topology matches transfer directly, otherwise use vertex proximity
    if is_obdata_identical(source_obj, target_obj):
        for vertex_group_name in vertex_group_names:
            transfer_single_vgroup_by_topology(source_obj, target_obj, vertex_group_name)
    else:
        precalc_and_transfer_multiple_groups(source_obj, target_obj, vertex_group_names, expand=2)


def transfer_single_vgroup_by_topology(source_obj, target_obj, vgroup_name):
    """Function to quickly transfer single vertex group between mesh objects in case of matching topology."""

    remove_vgroups([target_obj], [vgroup_name])

    vgroup_src = source_obj.vertex_groups.get(vgroup_name)
    vgroup_tgt = target_obj.vertex_groups.new(name=vgroup_name)

    for v in source_obj.data.vertices:
        if vgroup_src.index in [g.group for g in v.groups]:
            vgroup_tgt.add([v.index], vgroup_src.weight(v.index), 'REPLACE')


def remove_vgroups(objs, vgroup_names):
    for obj in objs:
        for vgroup_name in vgroup_names:
            target_vgroup = obj.vertex_groups.get(vgroup_name)
            if target_vgroup:
                obj.vertex_groups.remove(target_vgroup)


def precalc_and_transfer_multiple_groups(source_obj, target_obj, vgroup_names, expand=2):
    """Convenience function to transfer multiple groups."""

    remove_vgroups([target_obj], vgroup_names)

    kd_tree = build_kdtree(source_obj.data)
    vert_influence_map = build_vert_influence_map(source_obj, target_obj, kd_tree, expand)
    transfer_multiple_vertex_groups(
        source_obj,
        target_obj,
        vert_influence_map,
        src_vgroups=[source_obj.vertex_groups[name] for name in vgroup_names],
    )


def precalc_and_transfer_single_group(source_obj, target_obj, vgroup_name, expand=2):
    """Convenience function to transfer a single group. For transferring multiple groups,
    precalc_and_transfer_multiple_groups should be used as it is more efficient."""

    remove_vgroups([target_obj], [vgroup_name])

    kd_tree = build_kdtree(source_obj.data)
    vert_influence_map = build_vert_influence_map(source_obj, target_obj, kd_tree, expand)

    transfer_multiple_vertex_groups(
        source_obj,
        target_obj,
        vert_influence_map,
        [source_obj.vertex_groups[vgroup_name]],
    )


def build_kdtree(mesh):
    kd = kdtree.KDTree(len(mesh.vertices))
    for i, v in enumerate(mesh.vertices):
        kd.insert(v.co, i)
    kd.balance()
    return kd


def build_vert_influence_map(obj_from, obj_to, kd_tree, expand=2):
    verts_of_edge = {i: (e.vertices[0], e.vertices[1]) for i, e in enumerate(obj_from.data.edges)}

    edges_of_vert: Dict[int, List[int]] = {}
    for edge_idx, edge in enumerate(obj_from.data.edges):
        for vert_idx in edge.vertices:
            if vert_idx not in edges_of_vert:
                edges_of_vert[vert_idx] = []
            edges_of_vert[vert_idx].append(edge_idx)

    # A mapping from target vertex index to a list of source vertex indicies and
    # their influence.
    # This can be pre-calculated once per object pair, to minimize re-calculations
    # of subsequent transferring of individual vertex groups.
    vert_influence_map: List[int, List[Tuple[int, float]]] = {}
    for i, dest_vert in enumerate(obj_to.data.vertices):
        vert_influence_map[i] = get_source_vert_influences(
            dest_vert, obj_from, kd_tree, expand, edges_of_vert, verts_of_edge
        )

    return vert_influence_map


def get_source_vert_influences(
    target_vert, obj_from, kd_tree, expand=2, edges_of_vert={}, verts_of_edge={}
) -> List[Tuple[int, float]]:
    _coord, idx, dist = get_nearest_vert(target_vert.co, kd_tree)
    source_vert_indices = [idx]

    if dist == 0:
        # If the vertex position is a perfect match, just use that one vertex with max influence.
        return [(idx, 1)]

    for i in range(0, expand):
        new_indices = []
        for vert_idx in source_vert_indices:
            for edge in edges_of_vert[vert_idx]:
                vert_other = other_vert_of_edge(edge, vert_idx, verts_of_edge)
                if vert_other not in source_vert_indices:
                    new_indices.append(vert_other)
        source_vert_indices.extend(new_indices)

    distances: List[Tuple[int, float]] = []
    distance_total = 0
    for src_vert_idx in source_vert_indices:
        distance = (target_vert.co - obj_from.data.vertices[src_vert_idx].co).length
        distance_total += distance
        distances.append((src_vert_idx, distance))

    # Calculate influences such that the total of all influences adds up to 1.0,
    # and the influence is inversely correlated with the distance.
    parts = [1 / (dist / distance_total) for idx, dist in distances]
    parts_sum = sum(parts)

    influences = [
        (idx, 1 if dist == 0 else part / parts_sum) for part, dist in zip(parts, distances)
    ]

    return influences


def get_nearest_vert(coords: Vector, kd_tree: kdtree.KDTree) -> Tuple[Vector, int, float]:
    """Return coordinate, index, and distance of nearest vert to coords in kd_tree."""
    return kd_tree.find(coords)


def other_vert_of_edge(edge: int, vert: int, verts_of_edge: Dict[int, Tuple[int, int]]) -> int:
    verts = verts_of_edge[edge]
    assert vert in verts, f"Vert {vert} not part of edge {edge}."
    return verts[0] if vert == verts[1] else verts[1]


def transfer_multiple_vertex_groups(obj_from, obj_to, vert_influence_map, src_vgroups):
    """Transfer src_vgroups in obj_from to obj_to using a pre-calculated vert_influence_map."""

    for src_vg in src_vgroups:
        target_vg = obj_to.vertex_groups.get(src_vg.name)
        if target_vg == None:
            target_vg = obj_to.vertex_groups.new(name=src_vg.name)

    for i, dest_vert in enumerate(obj_to.data.vertices):
        source_verts = vert_influence_map[i]

        # Vertex Group Name : Weight
        vgroup_weights = {}

        for src_vert_idx, influence in source_verts:
            for group in obj_from.data.vertices[src_vert_idx].groups:
                group_idx = group.group
                vg = obj_from.vertex_groups[group_idx]
                if vg not in src_vgroups:
                    continue
                if vg.name not in vgroup_weights:
                    vgroup_weights[vg.name] = 0
                vgroup_weights[vg.name] += vg.weight(src_vert_idx) * influence

        # Assign final weights of this vertex in the vertex groups.
        for vg_name in vgroup_weights.keys():
            target_vg = obj_to.vertex_groups.get(vg_name)
            target_vg.add([dest_vert.index], vgroup_weights[vg_name], 'REPLACE')
