# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Menu
from .prefs import get_addon_prefs
from .utils import get_deforming_armature


class EASYWEIGHT_MT_PIE_easy_weight(Menu):
    bl_label = "Easy Weight"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        prefs = get_addon_prefs(context)

        # 1) < Operators
        self.draw_operators(pie.column().box(), context)

        # 2) > Front Faces Only
        pie.prop(
            prefs,
            'global_front_faces_only',
            icon='OVERLAY',
            text="Paint Through Mesh",
            invert_checkbox=True,
        )

        # 3) V Overlay & Armature Display settings
        self.draw_overlay_settings(pie.column().box(), context)

        # 4) ^ Accumulate
        pie.prop(prefs, 'global_accumulate', icon='GP_SELECT_STROKES')

        # 5) <^ Empty
        pie.separator()

        # 6) ^> Toggle Falloff Shape
        icon = 'SPHERE' if prefs.global_falloff_shape_sphere else 'MESH_CIRCLE'
        text = "Spherical" if prefs.global_falloff_shape_sphere else "Projected Circle"
        pie.prop(
            prefs,
            'global_falloff_shape_sphere',
            text="Falloff Shape: " + text,
            icon=icon,
            invert_checkbox=prefs.global_falloff_shape_sphere,
        )

        # 7) <v Empty
        pie.separator()

        # 8) v>Empty
        pie.separator()

    def draw_operators(self, layout, context):
        layout.label(text="Operators")

        prefs = get_addon_prefs(context)

        deform_rig = get_deforming_armature(context.active_object)
        if deform_rig:
            layout.operator('object.focus_deform_vgroups', icon='ZOOM_IN')

            layout.operator(
                'object.delete_empty_deform_vgroups',
                text="Delete Empty Deform Groups",
                icon='GROUP_BONE',
            )
        if not prefs.auto_clean_weights:
            layout.operator(
                "object.vertex_group_clean", icon='BRUSH_DATA', text="Clean Zero-Weights"
            ).group_select_mode = 'ALL'
        layout.operator(
            'object.delete_unused_vgroups', text="Delete Unused Groups", icon='BRUSH_DATA'
        )

        layout.operator(
            'paint.weight_from_bones', text="Assign Automatic from Bones", icon='BONE_DATA'
        ).type = 'AUTOMATIC'
        op = layout.operator(
            'object.vertex_group_normalize_all', text="Normalize Deform Groups", icon='IPO_SINE'
        )
        op.group_select_mode = 'BONE_DEFORM'
        op.lock_active = False

    def draw_overlay_settings(self, layout, context):
        overlay = context.space_data.overlay
        tool_settings = context.tool_settings
        prefs = get_addon_prefs(context)
        layout.label(text="Overlay")
        if not prefs.always_show_zero_weights:
            row = layout.row()
            row.prop(tool_settings, "vertex_group_user", text="Zero Weights Display", expand=True)
        if hasattr(context.space_data, "overlay"):
            row = layout.row()
            row.prop(
                overlay,
                "show_wpaint_contours",
                text="Weight Contours",
                toggle=True,
                icon='MOD_INSTANCE',
            )
            row.prop(overlay, "show_paint_wire", text="Wireframe", toggle=True, icon='SHADING_WIRE')
            icon = 'HIDE_OFF' if overlay.show_bones else 'HIDE_ON'
            row.prop(overlay, "show_bones", text="Bones", toggle=True, icon=icon)

        if context.pose_object:
            col = layout.column()
            col.label(text="Armature Display")
            row = col.row(align=True)
            row.prop(context.pose_object.data, "display_type", expand=True)
            x_row = col.row()
            x_row.prop(context.pose_object, "show_in_front", toggle=True, icon='XRAY')
            if overlay.show_xray_bone:
                x_row.prop(overlay, 'show_xray_bone', text="X-Ray Overlay")


registry = [
    EASYWEIGHT_MT_PIE_easy_weight,
]
