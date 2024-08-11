# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Operator

from ..utils import poll_weight_paint_mode, reveal_bone, get_deforming_vgroups


class EASYWEIGHT_OT_focus_deform_bones(Operator):
    """While in Weight Paint Mode, reveal the layers of, unhide, and select the bones of all deforming vertex groups"""

    bl_idname = "object.focus_deform_vgroups"
    bl_label = "Focus Deforming Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_weight_paint_mode(cls, context, with_rig=True, with_groups=True)

    def execute(self, context):
        # Deselect all bones
        for pb in context.selected_pose_bones[:]:
            pb.bone.select = False

        # Reveal and select all deforming pose bones.
        deform_groups = get_deforming_vgroups(context.active_object)
        rig = context.pose_object
        for vg in deform_groups:
            pb = rig.pose.bones.get(vg.name)
            if not pb:
                continue
            reveal_bone(pb.bone, select=True)

        self.report({'INFO'}, "Un-hid and selected all deforming bones.")
        return {'FINISHED'}


registry = [EASYWEIGHT_OT_focus_deform_bones]
