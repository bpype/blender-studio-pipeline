from typing import Dict, Tuple, List

import bpy
from bpy.props import IntProperty
from mathutils import Vector, kdtree


class EASYWEIGHT_OT_transfer_vertex_groups(bpy.types.Operator):
    """Transfer vertex groups from active to selected meshes"""

    bl_idname = "object.transfer_vertex_groups"
    bl_label = "Transfer Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    expand: IntProperty(
        name="Expand",
        default=2,
        min=0,
        max=5,
        description="Expand selection of source vertices from the nearest one. Higher values give smoother weights but pre-calculation takes longer",
    )

    def draw_transfer_vertex_groups_op(self, context):
        self.layout.operator(
            EASYWEIGHT_OT_transfer_vertex_groups.bl_idname,
            text=EASYWEIGHT_OT_transfer_vertex_groups.bl_label,
        )

    @classmethod
    def poll(cls, context):
        if not context.active_object or context.active_object.type != 'MESH':
            cls.poll_message_set("Active object must be a mesh.")
            return False
        selected_meshes = [ob for ob in context.selected_objects if ob.type == 'MESH']
        if len(selected_meshes) < 2:
            cls.poll_message_set("At least two meshes must be selected.")
            return False
        return True

    def execute(self, context):
        source_obj = context.object
        vgroups = source_obj.vertex_groups
        kd_tree = build_kdtree(source_obj.data)

        for target_obj in context.selected_objects:
            if target_obj == source_obj or target_obj.type != 'MESH':
                continue

            # Remove groups from the target obj that we will be transferring.
            for src_vg in vgroups:
                tgt_vg = target_obj.vertex_groups.get(src_vg.name)
                if tgt_vg:
                    target_obj.vertex_groups.remove(tgt_vg)

            vert_influence_map = build_vert_influence_map(
                source_obj, target_obj, kd_tree, self.expand
            )
            transfer_vertex_groups(source_obj, target_obj, vert_influence_map, vgroups)

        return {'FINISHED'}


def precalc_and_transfer_single_group(source_obj, target_obj, vgroup_name, expand=2):
    """Convenience function to transfer a single group. For transferring multiple groups,
    this is very inefficient and shouldn't be used.

    Instead, you should:
    - build_kd_tree ONCE per source mesh.
    - build_vert_influence_map and transfer_vertex_groups ONCE per object pair.
    """

    # Remove group from the target obj if it already exists.
    tgt_vg = target_obj.vertex_groups.get(vgroup_name)
    if tgt_vg:
        target_obj.vertex_groups.remove(tgt_vg)

    kd_tree = build_kdtree(source_obj.data)
    vert_influence_map = build_vert_influence_map(
        source_obj, target_obj, kd_tree, expand
    )
    transfer_vertex_groups(
        source_obj,
        target_obj,
        vert_influence_map,
        vgroups=[source_obj.vertex_groups[vgroup_name]],
    )


def build_kdtree(mesh):
    kd = kdtree.KDTree(len(mesh.vertices))
    for i, v in enumerate(mesh.vertices):
        kd.insert(v.co, i)
    kd.balance()
    return kd


def build_vert_influence_map(obj_from, obj_to, kd_tree, expand=2):
    verts_of_edge = {
        i: (e.vertices[0], e.vertices[1]) for i, e in enumerate(obj_from.data.edges)
    }

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
        (idx, 1 if dist == 0 else part / parts_sum)
        for part, dist in zip(parts, distances)
    ]

    return influences


def get_nearest_vert(
    coords: Vector, kd_tree: kdtree.KDTree
) -> Tuple[Vector, int, float]:
    """Return coordinate, index, and distance of nearest vert to coords in kd_tree."""
    return kd_tree.find(coords)


def other_vert_of_edge(
    edge: int, vert: int, verts_of_edge: Dict[int, Tuple[int, int]]
) -> int:
    verts = verts_of_edge[edge]
    assert vert in verts, f"Vert {vert} not part of edge {edge}."
    return verts[0] if vert == verts[1] else verts[1]


def transfer_vertex_groups(obj_from, obj_to, vert_influence_map, src_vgroups):
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


registry = [EASYWEIGHT_OT_transfer_vertex_groups]


def register():
    bpy.types.VIEW3D_MT_object.append(
        EASYWEIGHT_OT_transfer_vertex_groups.draw_transfer_vertex_groups_op
    )


def unregister():
    bpy.types.VIEW3D_MT_object.remove(
        EASYWEIGHT_OT_transfer_vertex_groups.draw_transfer_vertex_groups_op
    )
