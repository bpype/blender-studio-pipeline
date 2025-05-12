# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from . import utils
from mathutils import Vector
from bpy.types import WorkSpaceTool

def preserve_draw_settings(context, restore=False):
    props_list = ['curve_type',
                  'depth_mode',
                  'use_pressure_radius',
                  'use_project_only_selected',
                  'radius_taper_start',
                  'radius_taper_end',
                  'radius_min',
                  'radius_max',
                  'surface_offset',
                  'use_offset_absolute',
                  'use_stroke_endpoints',]
    if restore:
        draw_settings_dict = context.scene['BSBST-TMP-draw_settings_dict']
        for k, v in draw_settings_dict.items():
            setattr(context.tool_settings.curve_paint_settings, k, v)
        del context.scene['BSBST-TMP-draw_settings_dict']
    else:
        draw_settings_dict = dict()
        for item in props_list:
            draw_settings_dict[item] = getattr(context.tool_settings.curve_paint_settings, item)
        context.scene['BSBST-TMP-draw_settings_dict'] = draw_settings_dict

class BSBST_tool_settings(bpy.types.PropertyGroup):
    brush_color: bpy.props.FloatVectorProperty(name='Brush Color',
                                               size=3,
                                               subtype='COLOR',
                                               default=(0.,.5,1.),
                                               soft_min=0,
                                               soft_max=1,
                                               update=None,
                                               )
    radius_taper_start: bpy.props.FloatProperty(name='Taper Start', default=0, min=0, max=1, subtype='FACTOR')
    radius_taper_end: bpy.props.FloatProperty(name='Taper End', default=0, min=0, max=1, subtype='FACTOR')
    radius_min: bpy.props.FloatProperty(name='Radius Min', default=0, min=0, soft_max=10)
    radius_max: bpy.props.FloatProperty(name='Radius Max', default=1, min=0, soft_max=10)
    surface_offset: bpy.props.FloatProperty(name='Surface Offset', default=0, soft_max=10)
    use_project_only_selected: bpy.props.BoolProperty(name='Project Onto Selected',
                                                      default=True,
                                                      description='Project the strokes only on selected objects if applicable.')
    use_pressure_radius: bpy.props.BoolProperty(name='Use Pressure',
                                                default=True,
                                                description='Map tablet pressure to curve radius',)
    use_offset_absolute: bpy.props.BoolProperty(name='Absolute Offset',
                                                default=False,
                                                description="Apply a fixed offset. (Don't scale by the radius.)")

class BSBST_OT_draw(bpy.types.Macro):
    """
    Custom draw operation for hair curves
    """
    bl_idname = "brushstroke_tools.draw"
    bl_label = "Custom Draw"
    bl_options = {'REGISTER', 'UNDO'}

class BSBST_OT_pre_process_brushstroke(bpy.types.Operator):
    """
    Set up custom draw tool for curve drawing
    """
    bl_idname = "brushstroke_tools.pre_process_brushstroke"
    bl_label = "Custom Draw Pre Process"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool_settings = context.scene.BSBST_tool_settings

        preserve_draw_settings(context)

        # fix some settings
        context.tool_settings.curve_paint_settings.curve_type = 'POLY'
        context.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        context.tool_settings.curve_paint_settings.use_stroke_endpoints = False

        is_other_object_selected = len(set(context.selected_objects) - {context.object}) > 0
        context.tool_settings.curve_paint_settings.use_project_only_selected = is_other_object_selected and tool_settings.use_project_only_selected

        # propagate some settings from custom tool
        props_list = ['use_pressure_radius',
                    'radius_taper_start',
                    'radius_taper_end',
                    'radius_min',
                    'radius_max',
                    'surface_offset',
                    'use_offset_absolute',]
        for prop in props_list:
            setattr(context.tool_settings.curve_paint_settings, prop, getattr(tool_settings, prop))

        return {'FINISHED'}

class BSBST_OT_post_process_brushstroke(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.post_process_brushstroke"
    bl_label = "Custom Draw Post Process"
    bl_options = {'REGISTER', 'UNDO'}

    ng_process = None
    gp = None

    def execute(self, context):
        if not self.ng_process:
            preserve_draw_settings(context, restore=True)
            return {'CANCELLED'}
        tool_settings = context.scene.BSBST_tool_settings

        self.ng_process.nodes['settings.color'].value = [*tool_settings.brush_color, 1.]
        self.ng_process.nodes['view_vector'].vector = context.space_data.region_3d.view_rotation @ Vector((0.0, 0.0, 1.0))
        self.ng_process.nodes['new_key'].boolean = context.scene.tool_settings.use_keyframe_insert_auto
        self.ng_process.nodes['deform'].boolean = utils.get_deformable(context.object)
        if 'BSBST_surface_object' in context.object.keys():
            if context.object['BSBST_surface_object']:
                self.ng_process.nodes['surface_object'].inputs[0].default_value = context.object['BSBST_surface_object']
        bpy.ops.geometry.execute_node_group(name="set_brush_stroke_color", session_uid=self.ng_process.session_uid)

        preserve_draw_settings(context, restore=True)
        return {'FINISHED'}

    def invoke(self, context, event):
        utils.ensure_resources()
        self.gp = None
        self.ng_process = bpy.data.node_groups['.brushstroke_tools.draw_processing']
        return self.execute(context)

def register_custom_draw_macro():
    op = BSBST_OT_draw.define("brushstroke_tools.pre_process_brushstroke")
    op = BSBST_OT_draw.define("curves.draw")
    op.properties.wait_for_input = False
    op = BSBST_OT_draw.define("brushstroke_tools.post_process_brushstroke")

class BrushstrokesCurves(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_CURVES'

    bl_idname = "brushstroke_tools.draw"
    bl_label = "Brushstroke Draw"
    bl_description = (
        "Brushstrokes on the visible surface"
    )
    bl_icon = "brush.sculpt.paint"
    bl_widget = None
    bl_keymap = (
        ("brushstroke_tools.draw", {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG'},
         {"properties": []}),
    )

    def draw_settings(context, layout, tool, *, extra=False):
        props = tool.operator_properties("brushstroke_tools.draw")
        tool_settings = context.scene.BSBST_tool_settings
        region_type = context.region.type

        if region_type == 'TOOL_HEADER':
            if not extra:
                layout.prop(tool_settings , "radius_max")
                layout.prop(tool_settings , "surface_offset")
                layout.prop(tool_settings, "brush_color")
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
                return
        
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=False)
        col.template_color_picker(tool_settings, 'brush_color', value_slider=True)
        col.prop(tool_settings, 'brush_color', text='')

        col = layout.column(align=True)
        col.prop(tool_settings, "radius_taper_start", text="Taper Start", slider=True)
        col.prop(tool_settings, "radius_taper_end", text="End", slider=True)
        col = layout.column(align=True)
        col.prop(tool_settings, "radius_min", text="Radius Min")
        col.prop(tool_settings, "radius_max", text="Max")
        col.prop(tool_settings, "use_pressure_radius", icon='STYLUS_PRESSURE', emboss=True)

        layout.separator()

        col = layout.column()
        col.prop(tool_settings, "use_project_only_selected")
        col.prop(tool_settings, "surface_offset")
        col.prop(tool_settings, "use_offset_absolute")

classes = [
    BSBST_tool_settings,
    BSBST_OT_pre_process_brushstroke,
    BSBST_OT_post_process_brushstroke,
    BSBST_OT_draw,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.BSBST_tool_settings = bpy.props.PointerProperty(type=BSBST_tool_settings)
    register_custom_draw_macro()
    bpy.utils.register_tool(BrushstrokesCurves, after={"builtin.draw"}, group=True)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    bpy.utils.unregister_tool(BrushstrokesCurves)
    del bpy.types.Scene.BSBST_tool_settings