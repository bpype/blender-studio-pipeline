# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator, Object, VertexGroup, Modifier

from ..utils import delete_vgroups, poll_deformed_mesh_with_vgroups, get_deforming_vgroups


class EASYWEIGHT_OT_delete_unused_vertex_groups(Operator):
    """Delete vertex groups which are not used by any modifiers, deforming bones, shape keys, or constraints"""

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


def delete_unused_vgroups(mesh_ob: Object) -> list[str]:
    """Returns a list of vertex group names that got deleted."""
    groups_to_delete = get_unused_vgroups(mesh_ob)

    names = [vgroup.name for vgroup in groups_to_delete]
    print(f"Deleting unused non-deform groups:")
    print("    " + "\n    ".join(names))

    delete_vgroups(mesh_ob, groups_to_delete)

    return names


def get_unused_vgroups(mesh_ob: Object) -> set[VertexGroup]:
    return set(mesh_ob.vertex_groups) - set(get_used_vgroups(mesh_ob))


def get_used_vgroups(mesh_ob: Object) -> list[VertexGroup]:
    """Get a list of vertex groups used by the object.

    Currently accounts for Modifiers, Armatures, GeoNodes, Physics,
    Shape Keys, and Constraints of dependent objects.
    """

    used_vgroups = []
    # Inputs of Modifiers, including GeoNodes.
    for modifier in mesh_ob.modifiers:
        if modifier.type == 'NODES':
            print(modifier.name)
            used_vgroups.extend(get_vgroups_used_by_geonodes(mesh_ob, modifier))
        else:
            used_vgroups.extend(get_referenced_vgroups(mesh_ob, modifier))
            if modifier.type == 'ARMATURE':
                used_vgroups.extend(get_deforming_vgroups(mesh_ob, modifier.object))
        # Masks of Physics settings.
        if hasattr(modifier, 'settings'):
            used_vgroups.extend(get_referenced_vgroups(mesh_ob, modifier.settings))

    # Masks of Shape Keys.
    used_vgroups.extend(get_vgroups_used_by_shape_keys(mesh_ob))

    # Constraints of dependent objects.
    used_vgroups.extend(get_vgroups_used_by_constraints_of_dependent_objects(mesh_ob))

    return used_vgroups


def get_referenced_vgroups(mesh_ob: Object, py_ob: object) -> list[VertexGroup]:
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


def get_vgroups_used_by_shape_keys(mesh_ob) -> list[VertexGroup]:
    mask_vgroups = []
    if not mesh_ob.data.shape_keys:
        return mask_vgroups
    for key_block in mesh_ob.data.shape_keys.key_blocks:
        vgroup = mesh_ob.vertex_groups.get(key_block.vertex_group)
        if vgroup and vgroup.name not in mask_vgroups:
            mask_vgroups.append(vgroup)
    return mask_vgroups


def get_vgroups_used_by_constraints_of_dependent_objects(
    mesh_ob: Object,
) -> list[VertexGroup]:
    used_vgroups = []
    dependent_objs = [id for id in bpy.data.user_map()[mesh_ob] if type(id) == Object]
    for dependent_obj in dependent_objs:
        constraint_lists = [dependent_obj.constraints]
        if dependent_obj.type == 'ARMATURE':
            constraint_lists += [pb.constraints for pb in dependent_obj.pose.bones]

        for constraint_list in constraint_lists:
            for constraint in constraint_list:
                if (
                    hasattr(constraint, 'target')
                    and hasattr(constraint, 'subtarget')
                    and constraint.target == mesh_ob
                    and constraint.subtarget
                ):
                    vgroup = mesh_ob.vertex_groups.get(constraint.subtarget)
                    if vgroup:
                        used_vgroups.append(vgroup)
                if constraint.space_object == mesh_ob and constraint.space_subtarget:
                    vgroup = mesh_ob.vertex_groups.get(constraint.space_subtarget)
                    if vgroup:
                        used_vgroups.append(vgroup)
    return used_vgroups


def get_vgroups_used_by_geonodes(mesh_ob: Object, modifier: Modifier) -> list[VertexGroup]:
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


registry = [EASYWEIGHT_OT_delete_unused_vertex_groups]
