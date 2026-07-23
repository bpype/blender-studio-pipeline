# SPDX-FileCopyrightText: 2024-2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from bpy.props import EnumProperty
from bpy.types import Object, Operator, VertexGroup
from bpy.utils import flip_name
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from ..utils import poll_deformed_mesh_with_vgroups


class EASYWEIGHT_OT_symmetrize_groups(Operator):
    """Symmetrize weights of vertex groups on a near-symmetrical mesh. May have poor results on assymetrical meshes"""

    bl_idname = "object.symmetrize_vertex_weights"
    bl_label = "Symmetrize Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}

    groups: EnumProperty(
        name="Groups",
        description="Subset of vertex groups that should be symmetrized",
        items=[
            ("ACTIVE", "Active", "Active"),
            ("SELECTED", "Selected Bones", "Selected Bones"),
            ("ALL", "All", "All"),
        ],
    )

    direction: EnumProperty(
        name="Direction",
        description="Whether to symmetrize from left to right or from right to left",
        items=[
            (
                "AUTOMATIC",
                "Automatic",
                "Determine symmetrizing direction by the names of source vertex groups",
            ),
            ("LEFT_TO_RIGHT", "Left to Right", "Left to Right"),
            ("RIGHT_TO_LEFT", "Right to Left", "Right to Left"),
        ],
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context):
        return poll_deformed_mesh_with_vgroups(cls, context, must_deform=False)

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "groups")
        layout.prop(self, "direction")

    def execute(self, context):
        obj = context.active_object

        if self.groups == "SELECTED":
            vgroups = []
            # Get vertex groups of selected bones.
            for pbone in context.selected_pose_bones:
                vgroup = obj.vertex_groups.get(pbone.name)
                if not vgroup:
                    continue
                flipped_name = flip_name(pbone.name)
                if flipped_name in [vg.name for vg in vgroups]:
                    self.report(
                        {"ERROR"},
                        f'Both sides selected: "{vgroup.name}" & "{flipped_name}". Only one side should be selected.',
                    )
                    return {"CANCELLED"}
                vgroups.append(vgroup)

        elif self.groups == "ALL":
            vgroups = obj.vertex_groups[:]

        else:
            active_vgroup = obj.vertex_groups.active
            if not active_vgroup:
                self.report({"ERROR"}, "There is no active vertex group.")
                return {"CANCELLED"}
            vgroups = [active_vgroup]

        mirror_bvh, mirror_tris = build_mirror_bvh(obj=obj)

        if self.direction == "AUTOMATIC":
            self.direction = "LEFT_TO_RIGHT"
            righties = sum(1 for vg in vgroups if is_side_right(vg.name) is True)
            lefties = sum(1 for vg in vgroups if is_side_right(vg.name) is False)
            if righties > lefties:
                self.direction = "RIGHT_TO_LEFT"

        for vgroup in vgroups:
            symmetrize_vertex_group(
                obj=obj,
                vg_name=vgroup.name,
                mirror_bvh=mirror_bvh,
                mirror_tris=mirror_tris,
                right_to_left=self.direction == "RIGHT_TO_LEFT",
            )

        msg_direction = self.direction.replace("_", " ").lower()
        self.report({"INFO"}, f"Symmetrized {len(vgroups)} groups {msg_direction}.")

        return {"FINISHED"}


def is_side_right(name: str) -> bool | None:
    """
    Best-effort guess of whether a vertex group name refers to the right or left
    side of the character, based on common naming conventions. Returns True for
    the right side, False for the left side, or None if undetermined.
    """
    tokens = re.split(r"[._\- ]", name.lower())
    if "r" in tokens or "right" in tokens:
        return True
    if "l" in tokens or "left" in tokens:
        return False
    return None


def build_mirror_bvh(*, obj: Object) -> tuple[BVHTree, list[tuple[int, int, int]]]:
    """
    Build a BVHTree of the mesh's triangles, so that for any 3D position, the
    closest point on the mesh surface (and the triangle it lies on) can be found.
    This is used to sample vertex group weights, interpolated at arbitrary mirrored
    positions, which gives much better results than matching to the single nearest
    vertex on meshes that aren't perfectly symmetrical.
    """
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = [v.co for v in mesh.vertices]
    triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    bvh = BVHTree.FromPolygons(vertices, triangles)
    return bvh, triangles


def barycentric_weights(
    p: Vector, a: Vector, b: Vector, c: Vector
) -> tuple[float, float, float] | None:
    """
    Return the barycentric weights of point p with respect to triangle a, b, c,
    assuming p lies in the triangle's plane. Returns None for a degenerate triangle.
    """
    v0 = b - a
    v1 = c - a
    v2 = p - a
    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-10:
        return None
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return u, v, w


def sample_mirrored_weight(
    *,
    obj: Object,
    vgroup: VertexGroup,
    mirror_bvh: BVHTree,
    mirror_tris: list[tuple[int, int, int]],
    co: Vector,
) -> float:
    """
    Find the point on the mesh surface mirrored (on the X axis) from `co`, and
    return `vgroup`'s weight interpolated at that point.
    """

    def weight_of(vert_idx: int) -> float:
        try:
            return vgroup.weight(vert_idx)
        except RuntimeError:
            return 0.0

    mirrored_co = co.copy()
    mirrored_co.x *= -1
    location, _normal, tri_idx, _dist = mirror_bvh.find_nearest(mirrored_co)
    if tri_idx is None:
        return 0.0

    verts = obj.data.vertices
    a_idx, b_idx, c_idx = mirror_tris[tri_idx]
    weights = barycentric_weights(
        location, verts[a_idx].co, verts[b_idx].co, verts[c_idx].co
    )
    if not weights:
        # Degenerate triangle; fall back to whichever of its 3 vertices is closest.
        nearest_idx = min(
            (a_idx, b_idx, c_idx), key=lambda i: (verts[i].co - location).length
        )
        return weight_of(nearest_idx)

    u, v, w = weights
    return u * weight_of(a_idx) + v * weight_of(b_idx) + w * weight_of(c_idx)


def symmetrize_vertex_group(
    *,
    obj: Object,
    vg_name: str,
    mirror_bvh: BVHTree,
    mirror_tris: list[tuple[int, int, int]],
    right_to_left=False,
):
    """
    Symmetrize weights of a single group. mirror_bvh/mirror_tris should first be
    calculated with build_mirror_bvh().
    """

    vgroup = obj.vertex_groups.get(vg_name)
    if not vgroup:
        return
    opp_name = flip_name(vg_name)
    opp_vgroup = obj.vertex_groups.get(opp_name)
    if not opp_vgroup:
        opp_vgroup = obj.vertex_groups.new(name=opp_name)

    verts = obj.data.vertices

    if vgroup != opp_vgroup:
        # `vg_name` isn't necessarily the side that should act as the source: it's
        # just whichever one of the pair happened to be active/selected/passed in.
        # Use `right_to_left` to decide which one is actually the source, swapping
        # roles if needed, so the requested direction is honored either way.
        vg_is_right = is_side_right(vg_name)
        if vg_is_right is not None and vg_is_right != right_to_left:
            vgroup, opp_vgroup = opp_vgroup, vgroup

        # Rewrite all vertices, mirrored from this group.
        dst_indices = range(len(verts))
    else:
        # If the name isn't flippable, only rewrite vertices on the destination
        # side (X coord >= 0, or <= 0 for the opposite direction).
        def zero_or_more(x):
            return x >= 0

        def zero_or_less(x):
            return x <= 0

        is_dst_side = zero_or_more if right_to_left else zero_or_less
        dst_indices = [i for i, v in enumerate(verts) if is_dst_side(v.co.x)]

    # Sample all the new, mirrored weights before touching the vertex group, so that
    # clearing old weights below can't affect a nearby triangle's interpolation
    # (relevant when vgroup and opp_vgroup are the same, e.g. a center bone).
    new_weights = {
        dst_idx: sample_mirrored_weight(
            obj=obj,
            vgroup=vgroup,
            mirror_bvh=mirror_bvh,
            mirror_tris=mirror_tris,
            co=verts[dst_idx].co,
        )
        for dst_idx in dst_indices
    }

    if vgroup != opp_vgroup:
        # Clear weights of the opposite group from all vertices before rewriting.
        opp_vgroup.remove(range(len(verts)))
    else:
        vgroup.remove(dst_indices)

    for dst_idx, weight in new_weights.items():
        if weight <= 0.0:
            continue
        opp_vgroup.add([dst_idx], weight, "REPLACE")


registry = [EASYWEIGHT_OT_symmetrize_groups]
