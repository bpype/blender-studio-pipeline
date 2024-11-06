import bpy
from . import utils, icons

def update_active_brushstrokes(self, context):
    settings = context.scene.BSBST_settings
    for i, el in enumerate(settings.context_brushstrokes):
        ob = bpy.data.objects.get(el.name)
        if not ob:
            continue
        is_active = i == settings.active_context_brushstrokes_index
        ob['BSBST_active'] = is_active
        if 'BSBST_material' in ob.keys() and is_active:
            settings.context_material = ob['BSBST_material']

def update_brushstroke_method(self, context):
    settings = context.scene.BSBST_settings

    preset_name = f'BSBST-PRESET_{settings.brushstroke_method}'
    preset_object = bpy.data.objects.get(preset_name)
    settings.preset_object = preset_object

    style_object = utils.get_active_context_brushstrokes_object(context)
    if not style_object:
        style_object = preset_object

    if not style_object:
        settings.context_material = None
        return
    if 'BSBST_material' in style_object.keys():
        settings.context_material = style_object['BSBST_material']
    else:
        settings.context_material = None

def update_context_material(self, context):
    settings = context.scene.BSBST_settings

    style_object = utils.get_active_context_brushstrokes_object(context)
    if not style_object:
        style_object = settings.preset_object
    if not style_object:
        return
    utils.set_brushstroke_material(style_object, self.context_material)
    ng = bpy.data.node_groups.get(f'BSBST-BS.{self.context_material.brush_style}')
    if not ng:
        utils.set_preview(None)
        return
    if ng.preview:
        utils.set_preview(ng.preview.image_pixels_float, ng.preview.image_size[:], ng.name)
    else:
        utils.set_preview(None)

def update_link_context_type(self, context):
    self.link_context = True

def get_brushstroke_name(self):
    return self["name"]

def set_brushstroke_name(self, value):
    prev_name = self.get('name')
    self["name"] = value
    if not prev_name:
        return
    ob = bpy.data.objects.get(prev_name)
    if not ob:
        return
    ob.name = value
    ob.data.name = value
    flow_ob = utils.get_flow_object(ob)
    if flow_ob:
        flow_name = utils.flow_name(value)
        flow_ob.name = flow_name
        flow_ob.data.name = flow_name

def get_modifier_name(self):
    return self["name"]

def set_modifier_name(self, value):
    prev_name = self.get('name')
    if not prev_name:
        self["name"] = value
        return
    ob = self.id_data.modifiers.get(prev_name)
    ob.name = value
    self["name"] = ob.name

def get_hide_viewport_base(self):
    return self["hide_viewport_base"]

def set_hide_viewport_base(self, value):
    self["hide_viewport_base"] = value
    ob = bpy.data.objects.get(self.name)
    if not ob:
        return
    ob.hide_set(value)

def get_active_context_brushstrokes_index(self):
    if not self.get('active_context_brushstrokes_index'):
        return 0
    return self["active_context_brushstrokes_index"]

def set_active_context_brushstrokes_index(self, value):
    settings = bpy.context.scene.BSBST_settings
    if not settings.context_brushstrokes:
        if not settings.preset_object:
            return
        if 'BSBST_material' in settings.preset_object.keys():
            settings.context_material = settings.preset_object['BSBST_material']
    prev = self.get('active_context_brushstrokes_index')
    if prev == abs(value):
        return
    self["active_context_brushstrokes_index"] = abs(value)
    bs_ob = bpy.data.objects.get(self.context_brushstrokes[value].name)
    if settings.silent_switch:
        return
    if not bs_ob:
        return
    if not bpy.context.object:
        return
    view_layer = bpy.context.view_layer
    if bpy.context.object.visible_get(view_layer = view_layer):
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = bs_ob
    if bs_ob.visible_get(view_layer = view_layer):
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in bpy.data.objects:
        ob.select_set(False)
        if utils.is_brushstrokes_object(ob):
            ob['BSBST_active'] = False
    bs_ob.select_set(True)
    bs_ob['BSBST_active'] = True
    if settings.edit_toggle and bs_ob.visible_get(view_layer = view_layer):
        utils.edit_active_brushstrokes(bpy.context)
    if 'BSBST_material' in bs_ob.keys():
        settings.context_material = bs_ob['BSBST_material']

def get_brush_style(self):
    name = self.node_tree.nodes['Brush Style'].node_tree.name
    return '.'.join(name.split('.')[1:])

def set_brush_style(self, value):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    ng_name = f'BSBST-BS.{value}'
    ng = utils.ensure_node_group(ng_name, [bs for bs in addon_prefs.brush_styles if bs.name==value][0].filepath)

    if ng.preview:
        utils.set_preview(ng.preview.image_pixels_float, ng.preview.image_size[:], ng.name)
    else:
        utils.set_preview(None)

    node = self.node_tree.nodes['Brush Style']
    node_prev_inputs = [input.name for input in node.inputs]
    node.node_tree = ng
    for in_new in node.inputs:
        if in_new.name in node_prev_inputs:
            continue
        in_new.default_value = ng.interface.items_tree[in_new.name].default_value
    self["brush_style"] = value

def link_context_type_items(self, context):
    items = [
        ('SURFACE_OBJECT', 'Surface Object', 'Link socket preset to context surface object', 'OUTLINER_OB_SURFACE', 1),\
        ('FLOW_OBJECT', 'Flow Object', 'Link socket preset to context flow object', 'FORCE_WIND', 11),
        ('MATERIAL', 'Material', 'Link socket preset to context material', 'MATERIAL', 101),
        ('UVMAP', 'UV Map', 'Link socket preset to active context UVMap', 'UV', 201),
        ('RANDOM', 'Random', 'Randomize input value', icons.icon_previews['main']["RANDOM"].icon_id, 501),
    ]
    return items

def icon_from_link_type(link_type):
    items = link_context_type_items(None, bpy.context)
    for enum_item in items:
        if enum_item[0]==link_type:
            icon = enum_item[3]
            if type(icon) == int:
                return icon
            else:
                return {k : i for i, k in enumerate(bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys())}[icon]

class BSBST_socket_info(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='')
    link_context: bpy.props.BoolProperty(default=False, name='Link to Context')
    link_context_type: bpy.props.EnumProperty(default=1, name='Link to Context', update=update_link_context_type,
                                       items=link_context_type_items)
    hide_ui: bpy.props.BoolProperty(default=False)

class BSBST_modifier_info(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_modifier_name, set=set_modifier_name)
    hide_ui: bpy.props.BoolProperty(default=False)
    default_closed: bpy.props.BoolProperty(default=False)
    socket_info: bpy.props.CollectionProperty(type=BSBST_socket_info)

class BSBST_context_brushstrokes(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='', get=get_brushstroke_name, set=set_brushstroke_name)
    method: bpy.props.StringProperty(default='')
    hide_viewport_base: bpy.props.BoolProperty(default=False, get=get_hide_viewport_base, set=set_hide_viewport_base)

class BSBST_Settings(bpy.types.PropertyGroup):
    attach_to_active_selection: bpy.props.BoolProperty(default=True)
    preset_object: bpy.props.PointerProperty(type=bpy.types.Object, name="Default/Preset Object")
    assign_materials: bpy.props.BoolProperty(name='Assign Modifier Materials', default=True)
    brushstroke_method: bpy.props.EnumProperty(default='SURFACE_FILL', update=update_brushstroke_method,
                                       items= [('SURFACE_FILL', 'Fill', 'Use surface fill method for new brushstroke object', 'OUTLINER_OB_FORCE_FIELD', 0),\
                                               ('SURFACE_DRAW', 'Draw', 'Use surface draw method for new brushstroke object', 'LINE_DATA', 1),
                                               ])
    style_context: bpy.props.EnumProperty(default='BRUSHSTROKES',
                                          name='Context',
                                          items= [
                                            ('PRESET', 'Default', 'Specify the style of the current default used for new brushstrokes', 'SETTINGS', 0),\
                                            ('BRUSHSTROKES', 'Brushstrokes', 'Specify the style of the currently active brushstrokes', 'BRUSH_DATA', 1),
                                            ('AUTO', 'Auto', 'Specify the style of either the active brushstrokes or the preset depending on the context', 'AUTO', 2),
                                          ])
    view_tab: bpy.props.EnumProperty(default='SHAPE',
                                          name='Context',
                                          items= [
                                            ('SHAPE', 'Shape', 'View Modifiers Settings', 'MODIFIER', 0),
                                            ('MATERIAL', 'Material', 'View Material Settings', 'MATERIAL', 1),
                                            ('SETTINGS', 'Settings', 'View Additional Settings', 'PREFERENCES', 2),
                                          ])

    try:
        gpv3 = bpy.context.preferences.experimental.use_grease_pencil_version3
    except:
        v0, v1, v3 = bpy.app.version
        gpv3 = v0 >= 4 and v1 >= 3
    curve_mode: bpy.props.EnumProperty(default='CURVES',
                                       items= [('CURVE', 'Legacy', 'Use legacy curve type (Limited Support)', 'CURVE_DATA', 0),\
                                               ('CURVES', 'Curves', 'Use hair curves (Fully supported)', 'CURVES_DATA', 1),
                                               ('GP', 'Grease Pencil', 'Use Grease Pencil (Limited Support)', 'OUTLINER_OB_GREASEPENCIL', 2),
                                               ] if gpv3 else 
                                               [('CURVE', 'Legacy', 'Use legacy curve type (Limited Support)', 'CURVE_DATA', 0),\
                                               ('CURVES', 'Curves', 'Use hair curves (Full Support)', 'CURVES_DATA', 1),
                                               ])
    context_brushstrokes: bpy.props.CollectionProperty(type=BSBST_context_brushstrokes)
    context_material: bpy.props.PointerProperty(type=bpy.types.Material, name="Material", update=update_context_material)
    active_context_brushstrokes_index: bpy.props.IntProperty(   default = 0,
                                                                update=update_active_brushstrokes,
                                                                get=get_active_context_brushstrokes_index,
                                                                set=set_active_context_brushstrokes_index)
    ui_options: bpy.props.BoolProperty(default=False,
                                       name='UI Options',
                                       description="Show advanced UI options to customize exposed parameters")
    reuse_flow: bpy.props.BoolProperty(default=False,
                                       name='Re-use Flow Object',
                                       description="Re-use flow object from active brushstrokes when creating new brushstrokes")
    deforming_surface: bpy.props.BoolProperty(default=False,
                                        name='Deforming Surface',
                                        description='Create brushstrokes layer for a deforming surface')
    animated: bpy.props.BoolProperty(default=False,
                                        name='Animated',
                                        description='Create brushstrokes layer for animated brushstrokes/flow')
    edit_toggle: bpy.props.BoolProperty(default=False,
                                       name='Edit on Selection',
                                       description="Jump into the corresponding edit mode when selecting a brushstrokes layer")
    estimate_dimensions: bpy.props.BoolProperty(default=True,
                                       name='Estimate Dimensions',
                                       description="Estimate the length, width and distribution density of the brush strokes based on the bounding box to provide a reasonable starting point regardless of scale")

    silent_switch: bpy.props.BoolProperty(default=False)
    preview_texture: bpy.props.PointerProperty(type=bpy.types.Texture)

classes = [
    BSBST_socket_info,
    BSBST_modifier_info,
    BSBST_context_brushstrokes,
    BSBST_Settings,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.BSBST_settings = bpy.props.PointerProperty(type=BSBST_Settings)
    bpy.types.Object.modifier_info = bpy.props.CollectionProperty(type=BSBST_modifier_info)
    bpy.types.Material.brush_style = bpy.props.StringProperty(get=get_brush_style, set=set_brush_style, search_options={'SORT'})

    bpy.app.handlers.depsgraph_update_post.append(utils.find_context_brushstrokes)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.BSBST_settings
    del bpy.types.Object.modifier_info

    bpy.app.handlers.depsgraph_update_post.remove(utils.find_context_brushstrokes)