import bpy
from . import utils
from . import settings as settings_py

warning_icons_dict = {
    'ERROR': 'CANCEL',
    'WARNING': 'ERROR',
    'INFO': 'INFO',
}

def draw_panel_ui_recursive(panel, panel_name, mod, items, display_mode, hide_panel=False):

    scene = bpy.context.scene
    settings = scene.BSBST_settings

    is_preset = mod.id_data == settings.preset_object and mod.id_data

    if not panel:
        return
    
    mod_info = mod.id_data.modifier_info.get(mod.name)
    
    icon_dict = {
        bpy.types.NodeTreeInterfaceSocketObject: 'OBJECT_DATA',
        bpy.types.NodeTreeInterfaceSocketMaterial: 'MATERIAL',
        bpy.types.NodeTreeInterfaceSocketImage: 'IMAGE_DATA',
        bpy.types.NodeTreeInterfaceSocketCollection: 'OUTLINER_COLLECTION',
    }

    data_dict = {
        bpy.types.NodeTreeInterfaceSocketMaterial: 'materials',
        bpy.types.NodeTreeInterfaceSocketImage: 'images',
        bpy.types.NodeTreeInterfaceSocketCollection: 'collections',
    }

    mode_compare = []
    for k, v in items:
        if type(v) == bpy.types.NodeTreeInterfacePanel:

            v_id = f'Panel_{v.index}' # TODO: replace with panel identifier once that is exposed in Blender 4.3

            if not mod_info:
                continue
            s = mod_info.socket_info.get(v_id)
            if not s:
                continue
            if display_mode == 0:
                if s.hide_ui:
                    continue

            subpanel_header, subpanel = panel.panel(k, default_closed = v.default_closed)
            subpanel_header.label(text=k)
            if display_mode != 0:
                col = subpanel_header.column()
                col.active = not (mod_info.hide_ui or hide_panel)
                col.prop(s, 'hide_ui', icon_only=True, icon='UNPINNED' if s.hide_ui else 'PINNED', emboss=False)
            draw_panel_ui_recursive(subpanel, k, mod, v.interface_items.items(), display_mode, s.hide_ui)
            mode_compare = []
        else:
            if v.parent.name != panel_name:
                continue
            if f'{v.identifier}' not in mod.keys():
                continue
            if not mod_info:
                continue

            if type(v) == bpy.types.NodeTreeInterfaceSocketMenu:
                for item in mod.id_properties_ui(f'{v.identifier}').as_dict()['items']:
                    if item[4] == mod[f'{v.identifier}']:
                        continue
                    mode_compare += [item[0]]

            s = mod_info.socket_info.get(v.identifier)
            if not s:
                continue
            if display_mode == 0:
                comp_match = False
                for c in mode_compare:
                    comp_match = c in v.name
                    if comp_match:
                        break
                if comp_match:
                    continue
                if s.hide_ui:
                    continue
            row = panel.row(align=True)
            row.active = not (mod_info.hide_ui or hide_panel or s.hide_ui)

            col = row.column()
            input_row = col.row(align=True)
            attribute_toggle = False
            if f'{v.identifier}_use_attribute' in mod.keys() and not v.force_non_field:
                attribute_toggle = mod[f'{v.identifier}_use_attribute']
                if attribute_toggle:
                    input_row.prop(mod, f'["{v.identifier}_attribute_name"]', text=k)
                else:
                    input_row.prop(mod, f'["{v.identifier}"]', text=k)
                if is_preset:
                    toggle = input_row.operator('brushstroke_tools.preset_toggle_attribute',
                                                text='',
                                                depress=mod[f'{v.identifier}_use_attribute'],
                                                icon='SPREADSHEET')
                else:
                    toggle = input_row.operator('brushstroke_tools.brushstrokes_toggle_attribute',
                                                text='',
                                                depress=mod[f'{v.identifier}_use_attribute'],
                                                icon='SPREADSHEET')
                toggle.modifier_name = mod.name
                toggle.input_name = v.identifier
            else:
                if type(v) in icon_dict.keys():
                    icon = icon_dict[type(v)]
                else:
                    icon='NONE'
                if type(v) in data_dict.keys():
                    input_row.prop_search(mod, f'["{v.identifier}"]', bpy.data, data_dict[type(v)], text=k, icon=icon)
                else:
                    input_row.prop(mod, f'["{v.identifier}"]', text=k, icon=icon)
            if type(v) in utils.linkable_sockets:
                col.active = not s.link_context
                icon = settings_py.icon_from_link_type(s.link_context_type)
                row.alignment = 'EXPAND'
                if s.link_context:
                    row.prop(s, 'link_context', text='', icon_value=icon)
                else:
                    if display_mode == -1:
                        row.prop(s, 'link_context_type', text='', emboss=True, icon='LINKED', icon_only=True)
            if display_mode != 0:
                col = row.column()
                col.active = not (mod_info.hide_ui or hide_panel)
                col.prop(s, 'hide_ui', icon_only=True, icon='UNPINNED' if s.hide_ui else 'PINNED', emboss=False)

def draw_material_settings(layout, material, surface_object=None):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    settings = bpy.context.scene.BSBST_settings

    material_row = layout.row(align=True)
    material_row.template_ID(settings, 'context_material')

    material_header, material_panel = layout.panel("brushstrokes_material", default_closed=False)
    material_header.label(text='Properties', icon='MATERIAL')
    if material_panel:
        # draw color options
        try:
            n1 = material.node_tree.nodes['Color Attribute']
            n2 = material.node_tree.nodes['Color Texture']
            n3 = material.node_tree.nodes['Color']
            n4 = material.node_tree.nodes['Image Texture']
            n5 = material.node_tree.nodes['UV Map']
            n6 = material.node_tree.nodes['Color Variation']

            box = material_panel.box()
            box.prop(n1, 'mute', text='Use Brush Color', invert_checkbox=True)
            if n1.mute:
                row = box.row(align=True)
                if n2.mute:
                    row.prop(n3.outputs[0], 'default_value', text ='')
                else:
                    col = row.column()
                    col.template_node_inputs(n4)
                row.prop(n2, 'mute', icon_only=True, invert_checkbox=True, icon='IMAGE')
                if not n2.mute:
                    if not surface_object:
                        box.prop(n5, 'uv_map', icon='UV')
                    else:
                        box.prop_search(n5, 'uv_map', surface_object.data, 'uv_layers', icon='UV')
            box.prop(n6.inputs[0], 'default_value', text='Color Variation')
        except:
            pass

        # draw opacity options
        try:
            n1 = material.node_tree.nodes.get('Use Strength')
            n2 = material.node_tree.nodes.get('Opacity')
            n3 = material.node_tree.nodes.get('Backface Culling')

            box = material_panel.box()
            if n1:
                box.prop(n1, 'mute', text='Use Brush Strength', invert_checkbox=True)
            if n2:
                box.prop(n2.inputs[0], 'default_value', text='Opacity')
            if n3:
                box.prop(n3, 'mute', text='Backface Culling', invert_checkbox=True)
        except:
            pass

        # draw BSDF options
        try:
            n1 = material.node_tree.nodes['Principled BSDF']
            n2 = material.node_tree.nodes['Bump']

            box = material_panel.box()
            box.prop(n1.inputs[1], 'default_value', text='Metallic')
            box.prop(n1.inputs[2], 'default_value', text='Roughness')
            box.prop(n2, 'mute', text='Bump', invert_checkbox=True)
            row = box.row()
            if n2.mute:
                row.active = False
            row.prop(n2.inputs[0], 'default_value', text='Bump Strength')
        except:
            pass

        # draw translucency options
        try:
            n1 = material.node_tree.nodes['Translucency Add']
            n2 = material.node_tree.nodes['Translucency Strength']
            n3 = material.node_tree.nodes['Translucency Tint']

            box = material_panel.box()
            box.prop(n1, 'mute', text='Translucency', invert_checkbox=True)
            box.prop(n2.inputs[0], 'default_value', text='Translucency Strength')
            box.prop(n3.inputs[7], 'default_value', text='Translucency Tint')
        except:
            pass

        material_panel.prop(material, 'diffuse_color', text='Viewport Color')

    # draw brush style options
    try:
        n1 = material.node_tree.nodes['Brush Style']
        n2 = material.node_tree.nodes['Brush Curve']

        brush_header, brush_panel = layout.panel('brush_panel', default_closed = True)
        brush_header.label(text='Brush Style', icon='BRUSHES_ALL')
        if brush_panel:
            if settings.preview_texture:
                row = brush_panel.row(align=True)
                row.template_preview(settings.preview_texture, show_buttons=False, preview_id='brushstroke_preview')

            row = brush_panel.row(align=True)
            row.prop_search(material, 'brush_style', addon_prefs, 'brush_styles', text='', icon='BRUSHES_ALL')
            row.operator('brushstroke_tools.refresh_styles', text='', icon='FILE_REFRESH')
            if n1.inputs:
                for in_s in n1.inputs:
                    brush_panel.prop(in_s, 'default_value', text=f"{in_s.name}")
            brush_panel.template_node_inputs(n2)
    except:
        pass

    # draw effects options
    try:
        n1 = material.node_tree.nodes['Effects In']

        effects_header, effects_panel = layout.panel('effects_panel', default_closed = True)
        effects_header.label(text='Effects', icon='SHADERFX')
        if effects_panel:
            draw_effect_panel_recursive(effects_panel, material, n1)
    except:
        pass

def draw_effect_panel_recursive(effects_panel, material, prev_node):
    if not prev_node:
        return
    if not prev_node.outputs[0].links:
        return
    node = prev_node.outputs[0].links[0].to_node
    if node.name == 'Effects Out':
        return
    header, panel = effects_panel.panel(f'{node.name}_panel', default_closed = True)
    header.alignment = 'LEFT'
    header.prop(node, 'mute', invert_checkbox=True, icon_only=True)
    header.label(text=node.label if node.label else node.name)
    if panel:
        if node.mute:
            panel.active = False
        for input in node.inputs[1:]:
            panel.prop(input, 'default_value', text=input.name)
    
    draw_effect_panel_recursive(effects_panel, material, node)

def draw_advanced_settings(layout, settings):
    new_advanced_header, new_advanced_panel = layout.panel("new_advanced", default_closed=True)
    new_advanced_header.label(text='Advanced')
    if not new_advanced_panel:
        return
    new_advanced_panel.row().prop(settings, 'curve_mode', expand=True)
    if settings.curve_mode in ['CURVE', 'GP']:
        new_advanced_panel.label(text='Curve mode does not support drawing on deformed geometry', icon='ERROR')
    
    new_advanced_panel.prop(settings, 'animated')
    new_advanced_panel.prop(settings, 'deforming_surface')
    new_advanced_panel.prop(settings, 'assign_materials')
    new_advanced_panel.prop(settings, 'reuse_flow')
    new_advanced_panel.prop(settings, 'estimate_dimensions')
    new_advanced_panel.prop(settings, 'style_context')
    new_advanced_panel.operator('brushstroke_tools.render_setup')

def draw_shape_properties(layout, settings, style_object, is_preset, display_mode):
    if not style_object:
        return
    for mod in style_object.modifiers:
        mod_info = mod.id_data.modifier_info.get(mod.name)
        if not mod_info:
            continue
        if display_mode == 0:
            if mod_info.hide_ui:
                continue
        
        mod_header, mod_panel = layout.panel(mod.name, default_closed = mod_info.default_closed)
        row = mod_header.row(align=True)
        row.label(text='', icon='GEOMETRY_NODES')
        row.prop(mod_info, 'name', text='', emboss=False)

        if display_mode != 0:
            mod_header.prop(mod_info, 'hide_ui', icon_only=True, icon='UNPINNED' if mod_info.hide_ui else 'PINNED', emboss=False)
            if is_preset:
                op = row.operator('brushstroke_tools.preset_remove_mod', text='', icon='X')
            else:
                op = row.operator('object.modifier_remove', text='', icon='X')
                # TODO Implement operator to remove modifier on brushstroke object, even when not active
            op.modifier = mod.name

        if not mod_panel:
            continue

        if not mod.type == 'NODES':
            mod_panel.label(text="Only 'Nodes' modifiers supported")
            continue

        # show settings for nodes modifiers
        if mod.show_group_selector:
            mod_panel.prop(mod, 'node_group')
        if not mod.node_group:
            continue

        draw_panel_ui_recursive(mod_panel,
                                '',
                                mod,
                                mod.node_group.interface.items_tree.items(),
                                display_mode)
        
        draw_mod_warnings(layout, mod)

def draw_material_properties(layout, settings, surface_object):
    if settings.context_material:
        draw_material_settings(layout, settings.context_material, surface_object=surface_object)
    else:
        material_row = layout.row(align=True)
        material_row.template_ID(settings, 'context_material', new='brushstroke_tools.new_material')

def draw_settings_properties(layout, settings, style_object):
    deform = utils.get_deformable(style_object)
    op = layout.operator('brushstroke_tools.switch_deformable', text='Deforming Surface', depress=deform, icon='MOD_SIMPLEDEFORM')
    op.deformable = not deform

    anim = utils.get_animated(style_object)
    op = layout.operator('brushstroke_tools.switch_animated', text='Animated Strokes', depress=anim, icon='GP_MULTIFRAME_EDITING')
    op.animated = not anim

    layout.prop(style_object, 'visible_shadow', icon='LIGHT', emboss=True)

def draw_properties_panel(layout, settings, style_object, surface_object, is_preset, display_mode):

    layout.separator(type='LINE')
    row = layout.row(align=True)
    row.prop(settings, 'view_tab', expand=True)
    layout.separator(factor=.0, type='SPACE')

    if settings.view_tab == 'MATERIAL':
        draw_material_properties(layout, settings, surface_object)
    elif settings.view_tab == 'SHAPE':
        draw_shape_properties(layout, settings, style_object, is_preset, display_mode)

        # expose add modifier operator for preset context
        if is_preset:
            layout.operator('brushstroke_tools.preset_add_mod', icon='ADD')
    elif settings.view_tab == 'SETTINGS':
        draw_settings_properties(layout, settings, style_object)

def draw_mod_warnings(layout, mod):
    if utils.compare_versions(bpy.app.version, (4,3,0)) < 0:
        return
    if mod.node_warnings:
        warnings_header, warnings_panel = layout.panel(mod.name+'_warnings', default_closed = True)
        warnings_header.label(text=f'Warnings ({len(mod.node_warnings)})')
        if warnings_panel:
            for warning in mod.node_warnings: # TODO sort warnings by type and alphabet
                warnings_panel.label(text=warning.message,icon=warning_icons_dict[warning.type])

class BSBST_UL_brushstroke_objects(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        settings = data
        context_brushstroke = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if context_brushstroke:
                method_icon = 'BRUSH_DATA'
                method_icon = settings.bl_rna.properties['brushstroke_method'].enum_items[context_brushstroke.method].icon
                col = layout.column()
                row = col.row(align=True)
                row.prop(context_brushstroke, 'name', text='', emboss=False, icon=method_icon)
                bs_ob = bpy.data.objects.get(item.name)
                if not bs_ob:
                    return
                row.prop(context_brushstroke, 'hide_viewport_base', icon_only=True, emboss=False, icon='HIDE_ON' if context_brushstroke.hide_viewport_base else 'HIDE_OFF')
                row.prop(bs_ob, 'hide_viewport', icon_only=True, emboss=False)
                row.prop(bs_ob, 'hide_render', icon_only=True, emboss=False)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        return

class BSBST_MT_bs_context_menu(bpy.types.Menu):
    bl_label = "Brushstroke Specials"

    def draw(self, _context):
        layout = self.layout
        
        op = layout.operator('brushstroke_tools.copy_brushstrokes', text='Copy to Selected Objects')
        op.copy_all = False

        op = layout.operator('brushstroke_tools.copy_brushstrokes', text='Copy All to Selected Objects')
        op.copy_all = True

        op = layout.operator('brushstroke_tools.switch_deformable')
        op.switch_all = False

        op = layout.operator('brushstroke_tools.copy_flow')

        op = layout.operator("brushstroke_tools.assign_surface")

class BSBST_PT_brushstroke_tools_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Brushstroke Tools"
    bl_category = "Brushstroke Tools"

    def draw_header_preset(self,context):
        layout = self.layout
        row = layout.row(align=True)

        op = row.operator('brushstroke_tools.view_all', icon='RESTRICT_VIEW_OFF', text='')
        op.disable = False
        op = row.operator('brushstroke_tools.view_all', icon='RESTRICT_VIEW_ON', text='')
        op.disable = True

    def draw(self, context):
        layout = self.layout

        settings = context.scene.BSBST_settings
        surface_object = utils.get_active_context_surface_object(context)

        surface_row = layout.row()
        if surface_object:
            surface_row.label(text=f'{surface_object.name}', icon='OUTLINER_OB_SURFACE')
        else:
            surface_row.alert = True
            surface_row.label(text='No Valid Surface Object', icon='OUTLINER_OB_SURFACE')

        row = layout.row(align=True)
        op = row.operator("brushstroke_tools.new_brushstrokes", text='Fill', icon='OUTLINER_OB_FORCE_FIELD')
        op.method = 'SURFACE_FILL'
        op = row.operator("brushstroke_tools.new_brushstrokes", text='Draw', icon='LINE_DATA')
        op.method = 'SURFACE_DRAW'

        draw_advanced_settings(layout, settings)

        # identify style context
        style_object = context.object if settings.style_context=='BRUSHSTROKES' else settings.preset_object
        if settings.style_context=='PRESET':
            style_object = settings.preset_object
        else:
            if utils.is_brushstrokes_object(context.object):
                style_object = context.object
            else:
                if settings.context_brushstrokes:
                    bs_name = settings.context_brushstrokes[settings.active_context_brushstrokes_index].name
                    context_bs = bpy.data.objects.get(bs_name)
                    if context_bs:
                        style_object = context_bs

        is_preset = style_object == settings.preset_object

        display_mode = settings.ui_options
        if is_preset:
            display_mode = -1

        style_header, style_panel = layout.panel("brushstrokes_style", default_closed=False)

        if is_preset:
            style_header.label(text="Default Settings", icon='SETTINGS')
        else:
            style_header.label(text="Brushstroke Settings", icon='BRUSH_DATA')
            #style_header.operator('brushstroke_tools.make_preset', text='', icon='DECORATE_OVERRIDE')
            style_header.row().prop(settings, 'ui_options', icon='OPTIONS', icon_only=True)

        if style_panel:
            if settings.style_context=='BRUSHSTROKES' and not utils.is_brushstrokes_object(style_object):
                style_panel.label(text='No Brushstroke Context Found')
                return
            if not is_preset and len(settings.context_brushstrokes)>0:
                row = style_panel.row()
                row.template_list("BSBST_UL_brushstroke_objects", "", settings, "context_brushstrokes",
                             settings, "active_context_brushstrokes_index", rows=3, maxrows=5, sort_lock=True)
                column = row.column(align=True)
                column.operator('brushstroke_tools.duplicate_brushstrokes', text='', icon='DUPLICATE')
                column.operator('brushstroke_tools.delete_brushstrokes', text='', icon='TRASH')
                column.menu('BSBST_MT_bs_context_menu', text='', icon = 'DOWNARROW_HLT')

                row = style_panel.row()
                row_edit = row.row(align=True)
                row_edit.operator('brushstroke_tools.select_surface', icon='OUTLINER_OB_SURFACE', text='')
                bs_ob = utils.get_active_context_brushstrokes_object(context)
                text = 'Edit Flow' if getattr(bs_ob, '["BSBST_method"]', None)=='SURFACE_FILL' else 'Edit Brushstrokes'
                row_edit.operator('brushstroke_tools.edit_brushstrokes', icon='GREASEPENCIL', text = text)
                row_edit.prop(settings, 'edit_toggle', icon='RESTRICT_SELECT_OFF' if settings.edit_toggle else 'RESTRICT_SELECT_ON', icon_only=True)


            if not settings.preset_object and is_preset:
                layout.operator("brushstroke_tools.init_preset", icon='MODIFIER')
            else:
                draw_properties_panel(style_panel, settings, style_object, surface_object, is_preset, display_mode)       

class BSBST_MT_PIE_brushstroke_data_marking(bpy.types.Menu):
    bl_idname= "BSBST_MT_PIE_brushstroke_data_marking"
    bl_label = "Mark Brushstroke Flow"

    items = {
        "Brush Flow - Mark": ['FORCE_WIND'],
        "Brush Flow - Clear": ['NONE'],
        "Brush Break - Mark": ['MOD_PHYSICS'],
        "Brush Break - Clear": ['NONE'],
        "Brush Ignore - Mark": ['X'],
        "Brush Ignore - Clear": ['NONE'],
    }

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        for name, info in self.items.items():
            pie.alert=True
            op = pie.operator("geometry.execute_node_group", text=name, icon=info[0])
            op.asset_library_type='CUSTOM'
            op.asset_library_identifier=utils.asset_lib_name
            op.relative_asset_identifier=f"brushstroke_tools-resources.blend/NodeTree/{name}"
    
class BSBST_OT_brushstroke_data_marking(bpy.types.Operator):
    """
    Call pie menu for operators to mark brushstroke data on the surface mesh
    """
    bl_idname = "brushstroke_tools.data_marking"
    bl_label = "Mark Brushstroke Data"
    bl_description = " Call pie menu for operators to mark brushstroke data on the surface mesh"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name=BSBST_MT_PIE_brushstroke_data_marking.bl_idname)
        return {'FINISHED'}

classes = [
    BSBST_UL_brushstroke_objects,
    BSBST_MT_bs_context_menu,
    BSBST_PT_brushstroke_tools_panel,
    BSBST_MT_PIE_brushstroke_data_marking,
    BSBST_OT_brushstroke_data_marking,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    # Register UI shortcuts
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon is not None:
        km = wm.keyconfigs.addon.keymaps.new(name="Mesh")
        kmi = km.keymap_items.new("brushstroke_tools.data_marking","F", "PRESS",shift=False, ctrl=True, alt=True)   

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
