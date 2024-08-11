# SPDX-License-Identifier: GPL-2.0-or-later

from typing import List, Dict

import bpy
from bpy.types import Operator, VertexGroup, Object, Modifier
from bpy.props import EnumProperty
from bpy.utils import flip_name

from mathutils.kdtree import KDTree

def poll_deformed_mesh_with_vgroups(operator, context, must_deform=True):
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        operator.poll_message_set("No active mesh object.")
        return False
    if must_deform and ('ARMATURE' not in [m.type for m in obj.modifiers]):
        operator.poll_message_set("This mesh is not deformed by an Armature modifier.")
        return False
    if not obj.vertex_groups:
        operator.poll_message_set("This mesh has no vertex groups yet.")
        return False
    return True

class EASYWEIGHT_OT_delete_empty_deform_groups(Operator):
    """Delete vertex groups which are associated to deforming bones but don't have any weights"""

    bl_idname = "object.delete_empty_deform_vgroups"
    bl_label = "Delete Empty Deform Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_deformed_mesh_with_vgroups(cls, context)

    def execute(self, context):
        empty_groups = get_empty_deforming_vgroups(context.active_object)

        num_groups = len(empty_groups)
        print(f"Deleting empty deform groups:")
        print("    " + "\n    ".join([vg.name for vg in empty_groups]))

        delete_vgroups(context.active_object, empty_groups)

        self.report({'INFO'}, f"Deleted {num_groups} empty deform groups.")

        return {'FINISHED'}


class EASYWEIGHT_OT_delete_unselected_deform_groups(Operator):
    """Delete deforming vertex groups that do not correspond to any selected pose bone"""

    bl_idname = "object.delete_unselected_deform_vgroups"
    bl_label = "Delete Unselected Deform Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_weight_paint_mode(cls, context, with_rig=True, with_groups=True)

    def execute(self, context):
        deforming_groups = get_deforming_vgroups(context.active_object)
        selected_bone_names = [b.name for b in context.selected_pose_bones]
        unselected_def_groups = [
            vg for vg in deforming_groups if vg.name not in selected_bone_names
        ]

        print(f"Deleting unselected deform groups:")
        deleted_names = [vg.name for vg in unselected_def_groups]
        print("    " + "\n    ".join(deleted_names))

        delete_vgroups(context.active_object, unselected_def_groups)

        self.report({'INFO'}, f"Deleted {len(deleted_names)} unselected deform groups.")
        return {'FINISHED'}


class EASYWEIGHT_OT_focus_deform_bones(Operator):
    """While in Weight Paint Mode, reveal the layers of, unhide, and select the bones of all deforming vertex groups"""

    bl_idname = "object.focus_deform_vgroups"
    bl_label = "Focus Deforming Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_weight_paint_mode(cls, context, with_rig=True, with_groups=True)

    def execute(self, context):
        deform_groups = get_deforming_vgroups(context.active_object)
        rig = context.pose_object

        # Deselect all bones
        for pb in context.selected_pose_bones[:]:
            pb.bone.select = False

        # Reveal and select all deforming pose bones.
        for vg in deform_groups:
            pb = rig.pose.bones.get(vg.name)
            if not pb:
                continue
            reveal_bone(pb.bone, select=True)

        return {'FINISHED'}


class EASYWEIGHT_OT_delete_unused_vertex_groups(Operator):
    """Delete vertex groups which are not used by any modifiers, deforming bones, shape keys or constraints"""

    bl_idname = "object.delete_unused_vgroups"
    bl_label = "Delete Unused Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_deformed_mesh_with_vgroups(cls, context, must_deform=False)

    def execute(self, context):
        deleted_names = delete_unused_vgroups(context.active_object)

        self.report({'INFO'}, f"Deleted {len(deleted_names)} unused non-deform groups.")
        return {'FINISHED'}


class EASYWEIGHT_OT_symmetrize_groups(Operator):
    """Symmetrize weights of vertex groups on a near-perfectly symmetrical mesh (Will have poor results on assymetrical meshes)"""

    bl_idname = "object.symmetrize_vertex_weights"
    bl_label = "Symmetrize Vertex Weights"
    bl_options = {'REGISTER', 'UNDO'}

    groups: EnumProperty(
        name="Subset",
        description="Subset of vertex groups that should be symmetrized",
        items=[
            ('ACTIVE', 'Active', 'Active'),
            ('BONES', 'Selected Bones', 'Selected Bones'),
            ('ALL', 'All', 'All'),
        ],
    )

    direction: EnumProperty(
        name="Direction",
        description="Whether to symmetrize left to right or vice versa",
        items=[
            ('LEFT_TO_RIGHT', "Left to Right", "Left to Right"),
            ('RIGHT_TO_LEFT', "Right to Left", "Right to Left"),
        ],
    )

    @classmethod
    def poll(cls, context):
        return poll_deformed_mesh_with_vgroups(cls, context, must_deform=False)

    def execute(self, context):
        obj = context.active_object

        vgs = [obj.vertex_groups.active]
        if self.groups == 'SELECTED':
            # Get vertex groups of selected bones.
            for vg_name in context.context.selected_pose_bones:
                vg = obj.vertex_groups.get(vg_name)
                if not vg:
                    continue
                flipped_vg = flip_name(vg_name)
                if flipped_vg in vgs:
                    self.report(
                        {'ERROR'},
                        f'Both sides selected: "{vg.name}" & "{flipped_vg.name}". Only one side should be selected.',
                    )
                    return {'CANCELLED'}
                vgs.append(vg)

            vgs = [obj.vertex_groups.get(pb.name) for pb in context.selected_pose_bones]
        elif self.groups == 'ALL':
            vgs = obj.vertex_groups[:]

        symmetry_mapping = get_symmetry_mapping(obj=obj)

        for vg in vgs:
            symmetrize_vertex_group(
                obj=obj,
                vg_name=vg.name,
                symmetry_mapping=symmetry_mapping,
                right_to_left=self.direction == 'RIGHT_TO_LEFT',
            )
        return {'FINISHED'}


def poll_weight_paint_mode(operator, context, with_rig=False, with_groups=False):
    """Function used for operator poll functions, ie. to determine whether
    operators should be available or not."""

    obj = context.active_object
    if context.mode != 'PAINT_WEIGHT':
        operator.poll_message_set("Must be in Weight Paint mode.")
        return False
    if with_rig:
        if not 'ARMATURE' in (m.type for m in obj.modifiers):
            operator.poll_message_set("This mesh is not deformed by an Armature modifier.")
            return False
        if not context.pose_object or context.pose_object != get_deforming_armature(obj):
            operator.poll_message_set("Couldn't find deforming armature, or it is not in pose mode.")
            return False

    if with_groups and not obj.vertex_groups:
        operator.poll_message_set("This mesh object has no vertex groups yet.")
        return False

    return True


def reveal_bone(bone, select=True):
    """bone can be edit/pose/data bone.
    This function should work regardless of selection or visibility states"""
    if type(bone) == bpy.types.PoseBone:
        bone = bone.bone
    armature = bone.id_data

    if hasattr(armature, 'layers'):
        # Blender 3.6 and below: Bone Layers.
        enabled_layers = [i for i in range(32) if armature.layers[i]]

        # If none of this bone's layers are enabled, enable the first one.
        bone_layers = [i for i in range(32) if bone.layers[i]]
        if not any([i in enabled_layers for i in bone_layers]):
            armature.layers[bone_layers[0]] = True
    else:
        # Blender 4.0 and above: Bone Collections.
        if not any([coll.is_visible for coll in bone.collections]):
            bone.collections[0].is_visible = True

    bone.hide = False

    if select:
        bone.select = True


def delete_vgroups(mesh_ob, vgroups: List[VertexGroup]):
    for vg in vgroups:
        mesh_ob.vertex_groups.remove(vg)


### Functions for finding deforming vertex groups. ###


def get_deforming_armature(mesh_ob) -> Object:
    """Return first Armature modifier's target object."""
    for mod in mesh_ob.modifiers:
        if mod.type == 'ARMATURE':
            return mod.object


def get_deforming_vgroups(mesh_ob: Object, arm_ob: Object = None) -> List[VertexGroup]:
    """Get the vertex groups of a mesh object that correspond to a deform bone in the given armature."""

    if not arm_ob:
        arm_ob = get_deforming_armature(mesh_ob)
    if not arm_ob:
        return []

    deforming_vgroups = []

    for b in arm_ob.data.bones:
        if b.name in mesh_ob.vertex_groups and b.use_deform:
            deforming_vgroups.append(mesh_ob.vertex_groups[b.name])

    return deforming_vgroups


def get_non_deforming_vgroups(mesh_ob: Object) -> set:
    """Get the vertex groups of a mesh object that don't correspond to a deform bone in the given armature."""
    deforming_vgroups = get_deforming_vgroups(mesh_ob)
    return set(mesh_ob.vertex_groups) - set(deforming_vgroups)


def get_empty_deforming_vgroups(mesh_ob: Object) -> List[VertexGroup]:
    deforming_vgroups = get_deforming_vgroups(mesh_ob)
    empty_deforming_groups = [vg for vg in deforming_vgroups if not vgroup_has_weight(mesh_ob, vg)]

    # If there's no Mirror modifier, we're done.
    if not 'MIRROR' in (m.type for m in mesh_ob.modifiers):
        return empty_deforming_groups

    # Mirror Modifier: A group is not considered empty if it is the opposite
    # of a non-empty group.
    for vg in empty_deforming_groups[:]:
        opposite_vg = mesh_ob.vertex_groups.get(flip_name(vg.name))
        if not opposite_vg:
            continue
        if opposite_vg not in empty_deforming_groups:
            empty_deforming_groups.remove(vg)

    return empty_deforming_groups


def get_vgroup_weight_on_vert(vgroup, vert_idx) -> float:
    # Despite how terrible this is, as of 04/Jun/2021 it seems to be the
    # only only way to ask Blender if a vertex is assigned to a vertex group.
    try:
        w = vgroup.weight(vert_idx)
        return w
    except RuntimeError:
        return -1


def vgroup_has_weight(mesh_ob, vgroup) -> bool:
    for i in range(0, len(mesh_ob.data.vertices)):
        if get_vgroup_weight_on_vert(vgroup, i) > 0:
            return True
    return False


### Functions for symmetrizing. ###


def get_symmetry_mapping(*, obj: Object, axis='X', symmetrize_pos_to_neg=False) -> Dict[int, int]:
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
    *, obj: Object, vg_name: str, symmetry_mapping: Dict[int, int], right_to_left=False
):
    """
    Symmetrize weights of a single group. The symmetry_mapping should first be
    calculated with get_symmetry_mapping().
    """

    vg = obj.vertex_groups.get(vg_name)
    if not vg:
        return
    opp_name = flip_name(vg_name)
    opp_vg = obj.vertex_groups.get(opp_name)
    if not opp_vg:
        opp_vg = obj.vertex_groups.new(name=opp_name)

    skip_func = None
    if vg != opp_vg:
        # Clear weights of the opposite group from all vertices.
        opp_vg.remove(range(len(obj.data.vertices)))
    else:
        # If the name isn't flippable, only remove weights of vertices
        # whose X coord >= 0.

        # Figure out the function that will be used to determine whether a vertex
        # should be skipped or not.
        def zero_or_more(x):
            return x >= 0

        def zero_or_less(x):
            return x <= 0

        skip_func = zero_or_more if right_to_left else zero_or_less

    # Write the new, mirrored weights
    for src_idx, dst_idx in symmetry_mapping.items():
        vert = obj.data.vertices[src_idx]
        if skip_func != None and skip_func(vert.co.x):
            continue
        try:
            src_weight = vg.weight(src_idx)
            if src_weight == 0:
                continue
        except RuntimeError:
            continue
        opp_vg.add([dst_idx], src_weight, 'REPLACE')


### Functions detecting and deleting unused vertex groups. ###


def delete_unused_vgroups(mesh_ob: Object) -> List[str]:
    """Returns a list of vertex group names that got deleted."""
    groups_to_delete = get_unused_vgroups(mesh_ob)

    names = [vg.name for vg in groups_to_delete]
    print(f"Deleting unused non-deform groups:")
    print("    " + "\n    ".join(names))

    delete_vgroups(mesh_ob, groups_to_delete)

    return names


def get_unused_vgroups(mesh_ob: Object) -> List[VertexGroup]:
    return set(mesh_ob.vertex_groups) - set(get_used_vgroups(mesh_ob))


def get_used_vgroups(mesh_ob: Object) -> List[VertexGroup]:
    """Get a list of vertex groups used by the object.

    Currently accounts for Modifiers, Armatures, GeoNodes, Physics, and Shape Keys.
    Accounting for constraints of dependent objects would be possible as well, using bpy.data.user_map(). TODO.
    """

    used_vgroups = []
    # Modifiers
    for modifier in mesh_ob.modifiers:
        if modifier.type == 'NODES':
            print(modifier.name)
            used_vgroups.extend(get_vgroups_used_by_geonodes(mesh_ob, modifier))
        else:
            used_vgroups.extend(get_referenced_vgroups(mesh_ob, modifier))
            if modifier.type == 'ARMATURE':
                used_vgroups.extend(get_deforming_vgroups(mesh_ob, modifier.object))
        # Physics settings
        if hasattr(modifier, 'settings'):
            used_vgroups.extend(get_referenced_vgroups(mesh_ob, modifier.settings))

    # Shape Keys
    used_vgroups.extend(get_vgroups_used_by_shape_keys(mesh_ob))

    # Constraints of dependent objects.
    used_vgroups.extend(get_vgroups_used_by_constraints_of_dependent_objects(mesh_ob))

    return used_vgroups


def get_referenced_vgroups(mesh_ob: Object, py_ob: object) -> List[VertexGroup]:
    """Return a list of vertex groups directly referenced by any of the PyObject's members.
    Note that this is NOT a recursive function, and it can't really become one.

    Useful for determining if a vertex group is used by anything or not, but
    you still have to be thorough, and call this function on any sub-member
    of some object that might reference vertex groups."""
    referenced_vgroups = []
    for member in dir(py_ob):
        value = getattr(py_ob, member)
        if type(value) != str:
            continue
        vg = mesh_ob.vertex_groups.get(value)
        if vg:
            referenced_vgroups.append(vg)
    return referenced_vgroups


def get_vgroups_used_by_shape_keys(mesh_ob) -> List[VertexGroup]:
    mask_vgroups = []
    if not mesh_ob.data.shape_keys:
        return mask_vgroups
    for sk in mesh_ob.data.shape_keys.key_blocks:
        vg = mesh_ob.vertex_groups.get(sk.vertex_group)
        if vg and vg.name not in mask_vgroups:
            mask_vgroups.append(vg)
    return mask_vgroups


def get_vgroups_used_by_constraints_of_dependent_objects(
    mesh_ob: Object,
) -> List[VertexGroup]:
    used_vgroups = []
    dependent_objs = [id for id in bpy.data.user_map()[mesh_ob] if type(id) == Object]
    for dependent_obj in dependent_objs:
        if dependent_obj.type == 'ARMATURE':
            constraint_lists = [pb.constraints for pb in dependent_obj.pose.bones]
        else:
            constraint_lists = [dependent_obj.constraints]

        for constraint_list in constraint_lists:
            for constraint in constraint_list:
                if constraint.type == 'ARMATURE':
                    for tgt in constraint.targets:
                        if tgt.target == mesh_ob and tgt.subtarget:
                            vg = mesh_ob.vertex_groups.get(constraint.subtarget)
                            if vg:
                                used_vgroups.append(vg)
                elif (
                    hasattr(constraint, 'target')
                    and hasattr(constraint, 'subtarget')
                    and constraint.target == mesh_ob
                    and constraint.subtarget
                ):
                    vg = mesh_ob.vertex_groups.get(constraint.subtarget)
                    if vg:
                        used_vgroups.append(vg)
                if constraint.space_object == mesh_ob and constraint.space_subtarget:
                    vg = mesh_ob.vertex_groups.get(constraint.space_subtarget)
                    if vg:
                        used_vgroups.append(vg)
    return used_vgroups


def get_vgroups_used_by_geonodes(mesh_ob: Object, modifier: Modifier) -> List[VertexGroup]:
    used_vgroups = []
    for identifier in geomod_get_input_identifiers(modifier):
        use_attrib = identifier + "_use_attribute"
        if use_attrib in modifier and modifier[use_attrib]:
            attrib_name = modifier[identifier + "_attribute_name"]
            if attrib_name in mesh_ob.vertex_groups:
                # NOTE: Could be a false positive if this is a non-vertexgroup attribute with a matching name.
                used_vgroups.append(mesh_ob.vertex_groups[attrib_name])
    return used_vgroups


def geomod_get_input_identifiers(modifier: Modifier) -> set[str]:
    if hasattr(modifier.node_group, 'interface'):
        # 4.0
        return {
            socket.identifier
            for socket in modifier.node_group.interface.items_tree
            if socket.item_type == 'SOCKET'
            and socket.in_out == 'INPUT'
            and socket.socket_type != 'NodeSocketGeometry'
        }
    else:
        # 3.6
        return {input.identifier for input in modifier.node_group.inputs[1:]}


registry = [
    EASYWEIGHT_OT_delete_empty_deform_groups,
    EASYWEIGHT_OT_focus_deform_bones,
    EASYWEIGHT_OT_delete_unselected_deform_groups,
    EASYWEIGHT_OT_delete_unused_vertex_groups,
    EASYWEIGHT_OT_symmetrize_groups,
]
