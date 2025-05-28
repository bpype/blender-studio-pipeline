# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bl_ui.generic_ui_list import draw_ui_list
from .operators import geomod_get_identifier
from .prefs import get_addon_prefs


class GNSK_UL_main(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
        gnsk = item

        if self.layout_type != 'DEFAULT':
            # Other layout types not supported by this UIList.
            return

        split = layout.row().split(factor=0.66, align=True)

        row = split.row()
        if gnsk.storage_object:
            row.prop(gnsk.storage_object, 'name', text="", emboss=False, icon='OBJECT_DATA')
        modifier = gnsk.modifier
        if not modifier:
            row.alert=True
            row.label(text="Error: Modifier was removed.")
            return
        identifier = geomod_get_identifier(modifier, "Factor")
        row = split.row(align=True)
        row.prop(modifier, f'["{identifier}"]', text="", emboss=True)
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        ops = []
        ops.append(
            row.operator('object.geonode_shapekey_switch_focus', text="", icon='SCULPTMODE_HLT')
        )

        other_target_objs = gnsk.other_affected_objects
        if len(other_target_objs) > 0:
            ops.append(
                row.operator(
                    'object.geonode_shapekey_select_objects', text="", icon='RESTRICT_SELECT_OFF'
                )
            )
        for other_ob in other_target_objs:
            if other_ob in context.selected_objects:
                addon_prefs = get_addon_prefs(context)
                if addon_prefs.no_alt_key and len(gnsk.storage_object.geonode_shapekey_targets) > 1:
                    ops.append(
                        row.operator(
                            'object.geonode_shapekey_influence_slider',
                            text="",
                            icon='ARROW_LEFTRIGHT',
                        )
                    )
                    break

        for op in ops:
            op.gnsk_index = gnsk.index


class GNSK_PT_GeoNodeShapeKeys(bpy.types.Panel):
    """Panel to draw the GeoNode ShapeKey UI"""

    bl_label = "GeoNode Shape Keys"
    bl_idname = "GNSK_PT_GeoNodeShapeKeys"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "DATA_PT_shape_keys"

    @classmethod
    def poll(cls, context):
        ob = context.object

        return ob.override_library or len(ob.geonode_shapekey_targets) > 0

    def draw(self, context):
        layout = self.layout

        ob = context.object
        if ob.geonode_shapekey_targets:
            layout.operator(
                'object.geonode_shapekey_switch_focus',
                icon='FILE_REFRESH',
            )
            return

        list_ops = draw_ui_list(
            layout,
            context,
            class_name='GNSK_UL_main',
            unique_id='GNSK List',
            list_path='object.geonode_shapekeys',
            active_index_path='object.geonode_shapekey_index',
            insertion_operators=False,
            move_operators=False,
        )

        list_ops.operator('object.add_geonode_shape_key', text="", icon='ADD')

        row = list_ops.row()
        row.operator('object.remove_geonode_shape_key', text="", icon='REMOVE')


def draw_gnsk_uvmap_op(self, context):
    layout = self.layout
    layout.operator('object.geonode_shapekey_ensure_uvmap')


registry = [
    GNSK_UL_main,
]


def register():
    if hasattr(bpy.types.DATA_PT_shape_keys, 'replacement') and bpy.types.DATA_PT_shape_keys.replacement:
        GNSK_PT_GeoNodeShapeKeys.bl_parent_id = bpy.types.DATA_PT_shape_keys.replacement
    bpy.utils.register_class(GNSK_PT_GeoNodeShapeKeys)

    bpy.types.MESH_MT_shape_key_context_menu.append(draw_gnsk_uvmap_op)


def unregister():
    bpy.utils.unregister_class(GNSK_PT_GeoNodeShapeKeys)

    bpy.types.MESH_MT_shape_key_context_menu.remove(draw_gnsk_uvmap_op)
