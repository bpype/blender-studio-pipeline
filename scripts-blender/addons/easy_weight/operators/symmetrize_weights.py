# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator, Object
from bpy.props import EnumProperty
from bpy.utils import flip_name
from mathutils.kdtree import KDTree

from ..utils import poll_deformed_mesh_with_vgroups


class EASYWEIGHT_OT_symmetrize_groups(Operator):
    """Symmetrize weights of vertex groups on a near-symmetrical mesh.\May have poor results on assymetrical meshes"""

    bl_idname = "object.symmetrize_vertex_weights"
    bl_label = "Symmetrize Vertex Weights"
    bl_options = {'REGISTER', 'UNDO'}

    groups: EnumProperty(
        name="Groups",
        description="Subset of vertex groups that should be symmetrized",
        items=[
            ('ACTIVE', 'Active', 'Active'),
            ('SELECTED', 'Selected Bones', 'Selected Bones'),
            ('ALL', 'All', 'All'),
        ],
    )

    direction: EnumProperty(
        name="Direction",
        description="Whether to symmetrize from left to right or from right to left",
        items=[
            ('AUTOMATIC', "Automatic", "Determine symmetrizing direction by the names of source vertex groups"),
            ('LEFT_TO_RIGHT', "Left to Right", "Left to Right"),
            ('RIGHT_TO_LEFT', "Right to Left", "Right to Left"),
        ],
        options={'SKIP_SAVE'},
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

        layout.prop(self, 'groups')
        layout.prop(self, 'direction')

    def execute(self, context):
        obj = context.active_object

        vgroups = [obj.vertex_groups.active]
        if self.groups == 'SELECTED':
            vgroups = []
            # Get vertex groups of selected bones.
            for pbone in context.selected_pose_bones:
                vgroup = obj.vertex_groups.get(pbone.name)
                if not vgroup:
                    continue
                flipped_vg = flip_name(pbone.name)
                if flipped_vg in vgroups:
                    self.report(
                        {'ERROR'},
                        f'Both sides selected: "{vgroup.name}" & "{flipped_vg.name}". Only one side should be selected.',
                    )
                    return {'CANCELLED'}
                vgroups.append(vgroup)

        elif self.groups == 'ALL':
            vgroups = obj.vertex_groups[:]

        vert_symm_map = get_vert_symm_map(obj=obj)

        if self.direction == 'AUTOMATIC':
            self.direction = 'LEFT_TO_RIGHT'
            righties = 0
            lefties = 0
            for vgroup in vgroups:
                name = vgroup.name.lower()
                if (
                    ".r" in name
                    or "_r" in name
                    or "r_" in name
                    or "right" in name
                ):
                    righties += 1
                elif (
                    ".l" in name
                    or "_l" in name
                    or "l_" in name
                    or "left" in name
                ):
                    lefties += 1
            if righties > lefties:
                self.direction = 'RIGHT_TO_LEFT'

        for vgroup in vgroups:
            symmetrize_vertex_group(
                obj=obj,
                vg_name=vgroup.name,
                vert_symm_map=vert_symm_map,
                right_to_left=self.direction == 'RIGHT_TO_LEFT',
            )

        msg_direction = self.direction.replace("_", " ").lower()
        self.report({'INFO'}, f"Symmetrized {len(vgroups)} groups {msg_direction}.")

        return {'FINISHED'}


def get_vert_symm_map(*, obj: Object, axis='X', symmetrize_pos_to_neg=False) -> dict[int, int]:
    """
    Create a mapping of vertex indicies, such that the index on one side maps
    to the index on the opposite side of the mesh on a given axis.
    """
    assert axis in 'XYZ', "Axis must be X, Y or Z!"
    vertices = obj.data.vertices

    size = len(vertices)
    kd = KDTree(size)
    for i, v in enumerate(vertices):
        kd.insert(v.co, i)
    kd.balance()

    coord_i = 'XYZ'.find(axis)

    # Figure out the function that will be used to determine whether a vertex
    # should be skipped or not.
    def zero_or_more(x):
        return x >= 0

    def zero_or_less(x):
        return x <= 0

    skip_func = zero_or_more if symmetrize_pos_to_neg else zero_or_less

    # For any vertex with an X coordinate > 0, try to find a vertex at
    # the coordinate with X flipped.
    vert_map = {}
    bad_counter = 0
    for vert_idx, vert in enumerate(vertices):
        if abs(vert.co[coord_i]) < 0.0001:
            vert_map[vert_idx] = vert_idx
            continue
        # if skip_func(vert.co[coord_i]):
        # 	continue
        flipped_co = vert.co.copy()
        flipped_co[coord_i] *= -1
        _opposite_co, opposite_idx, dist = kd.find(flipped_co)
        if dist > 0.1:  # pretty big threshold, for testing.
            bad_counter += 1
            continue
        if opposite_idx in vert_map.values():
            # This vertex was already mapped, and another vertex just matched with it.
            # No way to tell which is correct. Input mesh should just be more symmetrical.
            bad_counter += 1
            continue
        vert_map[vert_idx] = opposite_idx
    return vert_map


def symmetrize_vertex_group(
    *, obj: Object, vg_name: str, vert_symm_map: dict[int, int], right_to_left=False
):
    """
    Symmetrize weights of a single group. The vert_symm_map should first be
    calculated with get_vert_symm_map().
    """

    vgroup = obj.vertex_groups.get(vg_name)
    if not vgroup:
        return
    opp_name = flip_name(vg_name)
    opp_vgroup = obj.vertex_groups.get(opp_name)
    if not opp_vgroup:
        opp_vgroup = obj.vertex_groups.new(name=opp_name)

    is_dst_side = None
    if vgroup != opp_vgroup:
        # Clear weights of the opposite group from all vertices.
        opp_vgroup.remove(range(len(obj.data.vertices)))
    else:
        # If the name isn't flippable, only remove weights of vertices
        # whose X coord >= 0.

        # Figure out the function that will be used to determine whether a vertex
        # should be skipped or not.
        def zero_or_more(x):
            return x >= 0

        def zero_or_less(x):
            return x <= 0

        # Determine the function which determines whether an X coordinate is on 
        # the destination side.
        is_dst_side = zero_or_more if right_to_left else zero_or_less
        dst_side_verts = [i for i, v in enumerate(obj.data.vertices) if is_dst_side(v.co.x)]
        vgroup.remove(dst_side_verts)

    # Write the new, mirrored weights
    for src_idx, dst_idx in vert_symm_map.items():
        vert = obj.data.vertices[src_idx]
        if is_dst_side != None and is_dst_side(vert.co.x):
            continue
        try:
            src_weight = vgroup.weight(src_idx)
            if src_weight == 0:
                continue
        except RuntimeError:
            continue
        opp_vgroup.add([dst_idx], src_weight, 'REPLACE')


registry = [EASYWEIGHT_OT_symmetrize_groups]
