# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from .utils import get_addon_prefs


class EASYWEIGHT_MT_PIE_easy_weight(Menu):
    bl_label = "Easy Weight"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        prefs = get_addon_prefs(context)

        # 1) < Operators
        op = pie.operator('wm.call_menu_pie', text="Operators", icon='SETTINGS')
        op.name = 'EASYWEIGHT_MT_PIE_easy_weight_operators'

        # 2) > Front Faces Only
        pie.prop(
            prefs,
            'global_front_faces_only',
            icon='OVERLAY',
            text="Paint Through Mesh",
            invert_checkbox=True,
        )

        # 3) V Overlay & Armature Display settings
        op = pie.operator('wm.call_menu_pie', text="Overlays", icon='OVERLAY')
        op.name = 'EASYWEIGHT_MT_PIE_easy_weight_overlays'

        # 4) ^ Accumulate
        pie.prop(prefs, 'global_accumulate', icon='GP_SELECT_STROKES')

        # 5) <^ Weight Mirror
        pie.prop(
            context.active_object,
            'use_mesh_mirror_x',
            text="X Symmetry",
            icon='MOD_MIRROR'
        )

        # 6) ^> Toggle Falloff Shape
        icon = 'SPHERE' if prefs.global_falloff_shape_sphere else 'MESH_CIRCLE'
        text = "Sphere" if prefs.global_falloff_shape_sphere else "Circle"
        pie.prop(
            prefs,
            'global_falloff_shape_sphere',
            text="Falloff: " + text,
            icon=icon,
            invert_checkbox=prefs.global_falloff_shape_sphere,
        )

        # 7) <v Empty
        pie.separator()

        # 8) v>Empty
        pie.separator()



class EASYWEIGHT_MT_PIE_easy_weight_operators(Menu):
    bl_label = "Easy Weight Operators"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        # 1) < Focus Deforming Bones.
        pie.operator('object.focus_deform_vgroups', icon='ZOOM_IN')

        # 2) > Delete Empty Deform Groups.
        pie.operator(
            'object.delete_empty_deform_vgroups',
            text="Delete Empty Deform Groups",
            icon='GROUP_BONE',
        )

        # 3) V Symmetrize Weights.
        pie.operator(
            'object.symmetrize_vertex_weights',
            text="Symmetrize Vertex Groups",
            icon='MOD_MIRROR',
        )

        # 4) ^ Smooth Weights.
        op = pie.operator(
            'object.vertex_group_smooth',
            icon='MOD_SMOOTH'
        )
        if context.pose_object:
            op.group_select_mode='BONE_DEFORM'
        op.factor=1

        # 5) <^ Normalize Deforming Groups.
        op = pie.operator(
            'object.vertex_group_normalize_all', text="Normalize Deform Groups", icon='IPO_SINE'
        )
        if context.pose_object:
            op.group_select_mode = 'BONE_DEFORM'
        op.lock_active = False

        # 6) ^> Transfer Weights
        op = pie.operator(
            'object.data_transfer',
            text="Transfer All Groups to Selected Objects",
            icon='UV_SYNC_SELECT'
        )
        op.use_reverse_transfer=False
        op.data_type='VGROUP_WEIGHTS'
        op.layers_select_src='ALL'
        op.layers_select_dst='NAME'

        # 7) <v Auto Weights.
        pie.operator(
            'paint.weight_from_bones', text="Assign Automatic from Bones", icon='BONE_DATA'
        ).type = 'AUTOMATIC'

        # 8) v> Delete Unused Groups.
        pie.operator('object.delete_unused_vgroups', text="Delete Unused Groups", icon='BRUSH_DATA')


class EASYWEIGHT_MT_PIE_easy_weight_overlays(Menu):
    bl_label = "Weight Painting Overlay"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        overlay = context.space_data.overlay
        tool_settings = context.tool_settings
        prefs = get_addon_prefs(context)

        # 1) < X-Ray
        if context.pose_object.show_in_front:
            pie.prop(context.pose_object, "show_in_front", toggle=True, icon='XRAY', text="Armature X-Ray")
        else:
            pie.prop(overlay, 'show_xray_bone', text="X-Ray Overlay")

        # 2) > Weight Contours
        pie.prop(
            overlay,
            "show_wpaint_contours",
            text="Weight Contours",
            toggle=True,
            icon='MOD_INSTANCE',
        )

        # 3) V  Armature Display type
        if context.pose_object:
            box = pie.box()
            box.label(text="Armature Display Type")
            box.row(align=True).prop(context.pose_object.data, "display_type", expand=True)
        else:
            pie.separator()

        # 4) ^ Bones.
        icon = 'HIDE_OFF' if overlay.show_bones else 'HIDE_ON'
        pie.prop(overlay, "show_bones", text="Bones", toggle=True, icon=icon)

        # 5) <^ Show Zero Weights.
        if not prefs.always_show_zero_weights:
            pie.prop(tool_settings, "vertex_group_user", text="Zero Weights Display", expand=True)
        else:
            pie.separator()

        # 6) ^> Wireframe.
        if hasattr(context.space_data, "overlay"):
            pie.prop(overlay, "show_wireframes", text="Wireframe", toggle=True, icon='SHADING_WIRE')
        else:
            pie.separator()


registry = [
    EASYWEIGHT_MT_PIE_easy_weight,
    EASYWEIGHT_MT_PIE_easy_weight_operators,
    EASYWEIGHT_MT_PIE_easy_weight_overlays,
]
