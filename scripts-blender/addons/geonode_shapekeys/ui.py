# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bl_ui.generic_ui_list import draw_ui_list

from .geonode_util import geomod_get_identifier, geomod_get_param_attribute, geomod_get_param_value
from .operators import TRANSFER_MODES
from .prefs import get_addon_prefs
from .props import GeoNodeShapeKey


def is_missing_uvs(gnsk: GeoNodeShapeKey, modifier) -> bool:
    """Whether the modifier is in Tangent Space mode, without the UV Map that mode requires."""
    mode = geomod_get_param_value(modifier, "Transfer Mode")
    if mode not in ("Tangent Space", TRANSFER_MODES["Tangent Space"]):
        return False

    uv_name = geomod_get_param_attribute(modifier, "UVMap")
    storage = gnsk.storage_object
    for ob in (gnsk.id_data, storage):
        if not ob or ob.type != 'MESH' or uv_name not in ob.data.uv_layers:
            return True
    return False


class GNSK_UL_main(bpy.types.UIList):
    def draw_item(self, context, layout, data, item: GeoNodeShapeKey, _icon, _active_data, _active_propname):
        gnsk = item

        if self.layout_type != 'DEFAULT':
            # Other layout types not supported by this UIList.
            return

        split = layout.row().split(factor=0.4, align=True)

        row = split.row()
        if gnsk.storage_object:
            row.prop(gnsk.storage_object, 'name', text="", emboss=False, icon='OBJECT_DATA')
        modifier = gnsk.modifier
        if not modifier:
            row.alert=True
            row.label(text="Error: Modifier was removed.")
            return
        row = split.row(align=True)
        # Highlight the mode when it can't work: Tangent Space needs a UV Map on both objects.
        mode_row = row.row(align=True)
        mode_row.alert = is_missing_uvs(gnsk, modifier)
        if bpy.app.version >= (5, 2, 0):
            mode_row.prop(getattr(modifier.properties.inputs, geomod_get_identifier(modifier, "Transfer Mode")), "value", text="", emboss=True)
            row.prop(getattr(modifier.properties.inputs, geomod_get_identifier(modifier, "Factor")), "value", text="", emboss=True)
        else:
            mode_row.prop(modifier, f'["{geomod_get_identifier(modifier, "Transfer Mode")}"]', text="", emboss=True)
            row.prop(modifier, f'["{geomod_get_identifier(modifier, "Factor")}"]', text="", emboss=True)
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        ops = []
        ops.append(
            row.operator('object.geonode_shapekey_switch_focus', text="", icon='SCULPTMODE_HLT')
        )
        ops[-1].mode = "SCULPT"
        ops.append(
            row.operator('object.geonode_shapekey_switch_focus', text="", icon='MOD_VERTEX_WEIGHT')
        )
        ops[-1].mode = "WEIGHT"

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
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob or ob.type != 'MESH':
            return False

        if len(ob.geonode_shapekey_targets) > 0:
            return True

        # Works on local and overridden objects, but linked objects
        # without an override can't store modifiers.
        return not ob.library

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
