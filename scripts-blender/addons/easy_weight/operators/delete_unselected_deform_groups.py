# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator

from ..utils import delete_vgroups, poll_weight_paint_mode, get_deforming_vgroups


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


registry = [EASYWEIGHT_OT_delete_unselected_deform_groups]
