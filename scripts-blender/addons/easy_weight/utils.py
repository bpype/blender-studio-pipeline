# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import PoseBone, Object, VertexGroup, Bone, EditBone

from . import __package__ as base_package


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


def poll_deformed_mesh_with_vgroups(operator, context, must_deform=True) -> bool:
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


def delete_vgroups(mesh_ob, vgroups: list[VertexGroup]):
    for vgroup in vgroups:
        mesh_ob.vertex_groups.remove(vgroup)


def get_deforming_vgroups(mesh_ob: Object, arm_ob: Object = None) -> list[VertexGroup]:
    """Get the vertex groups of a mesh object that correspond to a deform bone in the given armature."""

    if not arm_ob:
        arm_ob = get_deforming_armature(mesh_ob)
    if not arm_ob:
        return []

    deforming_vgroups = []

    for bone in arm_ob.data.bones:
        if bone.name in mesh_ob.vertex_groups and bone.use_deform:
            deforming_vgroups.append(mesh_ob.vertex_groups[bone.name])

    return deforming_vgroups


def get_deforming_armature(mesh_ob: Object) -> Object | None:
    """Return first Armature modifier's target object."""
    for mod in mesh_ob.modifiers:
        if mod.type == 'ARMATURE':
            return mod.object


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
            operator.poll_message_set(
                "Couldn't find deforming armature, or it is not in pose mode."
            )
            return False

    if with_groups and not obj.vertex_groups:
        operator.poll_message_set("This mesh object has no vertex groups yet.")
        return False

    return True


def reveal_bone(bone: Bone or EditBone or PoseBone, select=True):
    """Reveall and optionally select a bone, regardless of current
    selection or visibility states.
    """
    if type(bone) == PoseBone:
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
        ensure_visible_bone_collection(bone)

    bone.hide = False

    if select:
        bone.select = True


def ensure_visible_bone_collection(bone: Bone or EditBone or PoseBone):
    """If target bone not in any enabled collections, enable first one."""
    # NOTE: This function was lifted from CloudRig.
    if type(bone) == PoseBone:
        bone = bone.bone

    armature = bone.id_data
    collections = armature.collections

    if len(bone.collections) == 0:
        return

    if not any([coll.is_visible_effectively for coll in bone.collections]):
        coll = bone.collections[0]
        while coll:
            if collections.is_solo_active:
                coll.is_solo = True
            else:
                coll.is_visible = True
            coll = coll.parent
