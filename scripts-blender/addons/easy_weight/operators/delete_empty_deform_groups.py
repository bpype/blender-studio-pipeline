# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator, Object, VertexGroup
from bpy.utils import flip_name

from ..utils import delete_vgroups, poll_deformed_mesh_with_vgroups, get_deforming_vgroups


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


def get_non_deforming_vgroups(mesh_ob: Object) -> set:
    """Get the vertex groups of a mesh object that don't correspond to a deform bone in the given armature."""
    deforming_vgroups = get_deforming_vgroups(mesh_ob)
    return set(mesh_ob.vertex_groups) - set(deforming_vgroups)


def get_empty_deforming_vgroups(mesh_ob: Object) -> list[VertexGroup]:
    deforming_vgroups = get_deforming_vgroups(mesh_ob)
    empty_deforming_groups = [vg for vg in deforming_vgroups if not vgroup_has_weight(mesh_ob, vg)]

    # If there's no Mirror modifier, we're done.
    if not 'MIRROR' in (m.type for m in mesh_ob.modifiers):
        return empty_deforming_groups

    # Mirror Modifier: A group is not considered empty if it is the opposite
    # of a non-empty group.
    for vgroup in empty_deforming_groups[:]:
        opp_vgroup = mesh_ob.vertex_groups.get(flip_name(vgroup.name))
        if not opp_vgroup:
            continue
        if opp_vgroup not in empty_deforming_groups:
            empty_deforming_groups.remove(vgroup)

    return empty_deforming_groups


def get_vgroup_weight_on_vert(vgroup, vert_idx) -> float:
    # Despite how terrible this is, as of 04/Jun/2021 it seems to be the
    # only only way to ask Blender if a vertex is assigned to a vertex group.
    try:
        weight = vgroup.weight(vert_idx)
        return weight
    except RuntimeError:
        return -1


def vgroup_has_weight(mesh_ob, vgroup) -> bool:
    for i in range(0, len(mesh_ob.data.vertices)):
        if get_vgroup_weight_on_vert(vgroup, i) > 0:
            return True
    return False


registry = [EASYWEIGHT_OT_delete_empty_deform_groups]
