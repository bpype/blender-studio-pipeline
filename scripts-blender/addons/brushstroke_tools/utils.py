import os, ast, fnmatch
from pathlib import Path
from zipfile import ZipFile
import bpy
from bpy.app.handlers import persistent
import math, shutil, errno, numpy
from bpy.app.handlers import persistent

addon_version = (0,0,0)

preview_name = '.BSBST-preview'

ng_list = [
    ".brushstroke_tools.draw_processing",
    ".brushstroke_tools.pre_processing",
    ".brushstroke_tools.animation",
    ".brushstroke_tools.surface_fill",
    ".brushstroke_tools.surface_draw",
    ".brushstroke_tools.geometry_input",
    ".brushstroke_tools.mask_surface",
]

linkable_sockets = [
    bpy.types.NodeTreeInterfaceSocketObject,
    bpy.types.NodeTreeInterfaceSocketMaterial,
    bpy.types.NodeTreeInterfaceSocketVector,
    bpy.types.NodeTreeInterfaceSocketFloat,
    bpy.types.NodeTreeInterfaceSocketInt,
    bpy.types.NodeTreeInterfaceSocketString,
]

asset_lib_name = 'Brushstroke Tools Library'

@persistent
def find_context_brushstrokes(dummy):
    context = bpy.context
    settings = context.scene.BSBST_settings

    edit_toggle = settings.edit_toggle
    settings.edit_toggle = False
    len_prev = len(settings.context_brushstrokes)
    name_prev = settings.context_brushstrokes[settings.active_context_brushstrokes_index].name if len_prev else ''
    idx = settings.active_context_brushstrokes_index
    # identify context brushstrokes
    for el in range(len(settings.context_brushstrokes)):
        settings.context_brushstrokes.remove(0)
    context_object = context.object
    if not is_brushstrokes_object(context_object):
        bs_ob = is_flow_object(context_object)
        if bs_ob:
            context_object = bs_ob
    else:
        bs_ob = context_object
    surf_ob = get_surface_object(context_object)
    if surf_ob:
        context_object = surf_ob
    for ob in bpy.data.objects:
        if not is_brushstrokes_object(ob):
            continue
        surf_ob = get_surface_object(ob)
        flow_ob = get_flow_object(ob)
        if not surf_ob:
            if not flow_ob:
                continue
        if not surf_ob == context_object:
            if not flow_ob == context_object:
                continue
        bs = settings.context_brushstrokes.add()
        bs.name = ob.name
        bs.method = ob['BSBST_method']
        bs.hide_viewport_base = ob.hide_get()
        if name_prev == ob.name:
            idx = len(settings.context_brushstrokes)-1
    if not settings.context_brushstrokes:
        settings.edit_toggle = edit_toggle
        return
    if bs_ob:
        for i, bs in enumerate(settings.context_brushstrokes):
            if bs.name == bs_ob.name:
                if name_prev != bs.name:
                    settings.ui_options = False

                settings.silent_switch = True
                settings.active_context_brushstrokes_index = i
                settings.silent_switch = False
    elif len_prev == len(settings.context_brushstrokes):
        settings.silent_switch = True
        settings.active_context_brushstrokes_index = idx
        settings.silent_switch = False

    settings.active_context_brushstrokes_index = max(min(settings.active_context_brushstrokes_index, len(settings.context_brushstrokes)-1), 0)
    settings.edit_toggle = edit_toggle

@persistent
def refresh_preset(dummy):
    context = bpy.context
    settings = context.scene.BSBST_settings
    if not settings:
        return
    for ob in [settings.preset_object, get_active_context_brushstrokes_object(context)]:
        if not ob:
            continue
        for mod in ob.modifiers:
            mod_info = ob.modifier_info.get(mod.name)
            if not mod_info:
                mod_info = ob.modifier_info.add()
                mod_info.name = mod.name
            if not mod.type == 'NODES':
                continue
            if not mod.node_group:
                continue
            for v in mod.node_group.interface.items_tree.values():
                if type(v) is bpy.types.NodeTreeInterfacePanel:
                    v_id = f'Panel_{v.index}' # TODO: replace with panel identifier once that is exposed in Blender 4.3
                else:
                    v_id = v.identifier
                if v_id in [s.name for s in mod_info.socket_info]:
                    continue
                n = mod_info.socket_info.add()
                n.name = v_id
                # TODO: clean up old settings

def mark_socket_context_type(mod_info, socket_name, link_type):
    socket_info = mod_info.socket_info.get(socket_name)
    if not socket_info:
        socket_info = mod_info.socket_info.add()
        socket_info.name = socket_name
    socket_info.link_context_type = link_type

def mark_socket_hidden(mod_info, socket_name, hide=True):
    socket_info = mod_info.socket_info.get(socket_name)
    if not socket_info:
        socket_info = mod_info.socket_info.add()
        socket_info.name = socket_name
    socket_info.hide_ui = hide

def mark_panel_hidden(mod_info, panel_name, hide=True):
    mod = mod_info.id_data.modifiers.get(mod_info.name)
    if not mod:
        return
    if not mod.type == 'NODES':
        return
    ng = mod.node_group
    if not ng:
        return
    v_id = ''
    for k, v in ng.interface.items_tree.items():
        if type(v) != bpy.types.NodeTreeInterfacePanel:
            continue
        if v.name == panel_name:
            v_id = f'Panel_{v.index}'
            break
    if not v_id:
        return
    socket_info = mod_info.socket_info.get(v_id)
    if not socket_info:
        socket_info = mod_info.socket_info.add()
        socket_info.name = v_id
    socket_info.hide_ui = hide

def set_brushstroke_material(ob, material):
    prev_mat = None
    if 'BSBST_material' in ob.keys():
        if ob['BSBST_material'] == material:
            return
        else:
            prev_mat = ob['BSBST_material']
    ob['BSBST_material'] = material
    for mod in ob.modifiers:
        mod_info = ob.modifier_info.get(mod.name)
        if not mod_info:
            continue
        for s in mod_info.socket_info:
            if not s.link_context:
                continue
            if not s.link_context_type == 'MATERIAL':
                continue
            mod[s.name] = material
    ob.update_tag()

    if ob.type == 'EMPTY':
        return
    if not ob.material_slots:
        override = bpy.context.copy()
        override['object'] = ob
        with bpy.context.temp_override(**override):
            bpy.ops.object.material_slot_add()
            ob.material_slots[0].material = material
    else:
        for m_slot in ob.material_slots:
            if m_slot.material == prev_mat:
                m_slot.material = material

def deep_copy_mod_info(source_object, target_object):
    for mod_info in source_object.modifier_info:
        mod_info_tgt = target_object.modifier_info.add()
        for attr in mod_info.keys():
            if attr == 'socket_info':
                continue
            setattr(mod_info_tgt, attr, getattr(mod_info, attr))
        for socket_info in mod_info.socket_info:
            socket_info_tgt = mod_info_tgt.socket_info.add()
            for attr in socket_info.keys():
                setattr(socket_info_tgt, attr, getattr(socket_info, attr))

def get_addon_directory() -> Path:
    """
    Returns the path of the addon directory.
    """
    path = os.path.dirname(os.path.realpath(__file__))
    abspath = bpy.path.abspath(path)
    return Path(abspath)

def get_resource_directory() -> Path:
    """
    Returns the path to be used to append resource data-blocks.
    """
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    resource_dir = addon_prefs.resource_path
    if resource_dir:
        return Path(resource_dir)
    else:
        return get_addon_directory().joinpath('assets')

def import_resources(ng_names = ng_list):
    """
    Imports the necessary blend data resources required by the addon.
    """
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    path = get_resource_directory()

    resource_path = str(path.joinpath('brushstroke_tools-resources.blend'))
    with bpy.data.libraries.load(resource_path, link=addon_prefs.import_method=='LINK', relative=addon_prefs.import_relative_path) as (data_src, data_dst):
        data_dst.node_groups = ng_names
    if addon_prefs.import_method=='APPEND':
        # pack imported resources
        for img in bpy.data.images:
            if not img.library_weak_reference:
                continue
            if img.packed_file:
                continue
            if 'brushstroke_tools-resources.blend' in img.library_weak_reference.filepath:
                img.pack()

def read_lib_version():
    resource_dir = get_resource_directory()
    with open(resource_dir.joinpath(".version"), "r") as file:
        version = ast.literal_eval(file.read())
        return version

def write_lib_version():
    resource_dir = get_resource_directory()
    with open(resource_dir.joinpath(".version"), "w") as file:
        file.write(str(addon_version))

def copy_resources_to_dir(tgt_dir = ''):
    resource_dir = get_addon_directory().joinpath('assets')
    if not tgt_dir:
        tgt_dir = get_resource_directory()

    try:
        shutil.copytree(resource_dir, tgt_dir, dirs_exist_ok=True)
        write_lib_version()
    except OSError as err:
        # error caused if the source was not a directory
        if err.errno == errno.ENOTDIR:
            shutil.copy2(resource_dir, tgt_dir)
            write_lib_version()
        else:
            print("Error: % s" % err)
    refresh_brushstroke_styles()

def install_brush_style_pack(filepath, tgt_dir='', ot=None):

    if type(filepath) != Path:
        filepath = Path(filepath)

    filename, extension = os.path.splitext(filepath)

    if not tgt_dir:
        tgt_dir = get_resource_directory().joinpath('styles')
    elif type(tgt_dir) != Path:
        tgt_dir = Path(tgt_dir)

    if extension=='.zip':
        with ZipFile(filepath, 'r') as zip_object:
            zip_object.extractall( 
                path=tgt_dir)
    elif extension.startswith('.blend'):
        shutil.copy2(filepath, tgt_dir)
    else:
        if ot:
            ot.report({"ERROR"}, "Selected file has to be either .zip or .blend")
        else:
            print("ERROR: Selected file has to be either .zip or .blend")
        return False
    return True

def compare_versions(v1: tuple, v2: tuple):
    """ Returns n when v1 > v2, 0 when v1 == v2, -n when v1 < v2, while n = 'Index of first significant version tuple element' + 1.
    e.g. (0,2,0), (0,2,1) -> -3
    """
    c = 1
    for e1, e2 in zip(v1, v2):
        if e1 > e2:
            return c
        elif e1 < e2:
            return -c
        c += 1
    return 0

def import_brushstroke_material():
    name = 'Brush Material'
    path = str(get_resource_directory().joinpath('brushstroke_tools-resources.blend'))
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    mats_pre = set(bpy.data.materials)
    ng_pre = set(bpy.data.node_groups)
    with bpy.data.libraries.load(path, link=addon_prefs.import_method=='LINK', relative=addon_prefs.import_relative_path) as (data_src, data_dst):
        data_dst.materials = [name]
    mats_new = list(set(bpy.data.materials) - mats_pre)

    # de-duplicate imported node-groups
    ng_new = list(set(bpy.data.node_groups) - ng_pre)
    ng_remove = []
    for ng in ng_new:
        ng_name_elements = ng.name.split('.')
        if len(ng_name_elements) == 1:
            continue
        root_ng = bpy.data.node_groups.get('.'.join(ng_name_elements[:-1]))
        if not root_ng:
            continue
        ng.user_remap(root_ng)
        ng_remove += [ng]
    for ng in reversed(ng_remove):
        bpy.data.node_groups.remove(ng)

    # return imported material
    if mats_new:
        return mats_new[0]
    else:
        return bpy.data.materials.get(name)

def ensure_node_group(name, path=''):
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if not path:
        path=str(get_resource_directory().joinpath('brushstroke_tools-resources.blend'))

    with bpy.data.libraries.load(path, link=addon_prefs.import_method=='LINK', relative=addon_prefs.import_relative_path) as (data_src, data_dst):
        data_dst.node_groups = [name]
    if addon_prefs.import_method=='APPEND':
        # pack imported resources
        for img in bpy.data.images:
            if not img.library_weak_reference:
                continue
            if path in img.library_weak_reference.filepath:
                if len(img.packed_files) > 0:
                    continue
                img.pack()
    ng = bpy.data.node_groups.get(name)
    
    return ng

def ensure_resources():
    ng_missing = set()
    
    for n in ng_list:
        if not bpy.data.node_groups.get(n):
            ng_missing.add(n)
    
    if ng_missing:
        import_resources(list(ng_missing))

def register_asset_lib():
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    if asset_lib_name in [a.name for a in asset_libs]:
        return asset_libs[asset_lib_name]
    lib = asset_libs.new()
    lib.name = asset_lib_name
    lib.path = str(get_resource_directory())
    lib.use_relative_path = False

def unregister_asset_lib():
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    lib = asset_libs.get(asset_lib_name)
    if not lib:
        return
    asset_libs.remove(lib)

def update_asset_lib_path():
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    if asset_lib_name not in [a.name for a in asset_libs]:
        register_asset_lib()
        return
    lib = asset_libs[asset_lib_name]
    lib.path = str(get_resource_directory())
    refresh_brushstroke_styles()

def refresh_brushstroke_styles():
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    bs_list = addon_prefs.brush_styles

    for a in range(len(bs_list)):
        bs_list.remove(0)

    lib_path = get_resource_directory()
    add_brush_styles_from_directory(bs_list, lib_path)

    # find additional local brush styles
    add_brush_styles_from_names(bs_list, [ng.name for ng in bpy.data.node_groups], '', name_filter = [bs.name for bs in bs_list])

def add_brush_styles_from_names(bs_list, ng_names, filepath, name_filter = []):

    names = [name for name in ng_names if name.startswith('BSBST-BS')]

    for ng_name in names:
        name_elements = ng_name.split('.')
        if name_elements[-1] in name_filter:
            continue
        b_style = bs_list.add()
        b_style.name = name_elements[-1]
        b_style.id_name = ng_name
        b_style.filepath = filepath
        if len(name_elements) >= 4:
            b_style.category = name_elements[1]
        b_style.type = name_elements[-2]

def add_brush_styles_from_directory(bs_list, path):
    subdirs = [f.path for f in os.scandir(path) if f.is_dir()]
    files = [f.path for f in os.scandir(path) if not f.is_dir()]

    for filepath in files:
        if not filepath.endswith('.blend'):
            continue

        names = []
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            add_brush_styles_from_names(bs_list, data_from.node_groups, filepath)

    for dir in subdirs:
        add_brush_styles_from_directory(bs_list, dir)

def find_brush_style_by_name(name: str):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    for brush_style in addon_prefs.brush_styles:
        if name == brush_style.name:
            return brush_style
    return None

def copy_collection_property(col_target, col_source):

    for i in range(len(col_target)):
        col_target.remove(0)
    
    for i in range(len(col_source)):
        element_source = col_source[i]
        element_target = col_target.add()
        for k, v in element_source.items():
            element_target[k] = v
    
def update_filtered_brush_styles(self, context):
    addon_prefs = context.preferences.addons[__package__].preferences

    active_bs_name = ''
    if self.brush_styles_filtered:
        active_bs_name = self.brush_styles_filtered[self.brush_styles_filtered_active_index].name
    
    copy_collection_property(self.brush_styles_filtered, addon_prefs.brush_styles)

    # filter by type
    if self.brush_type != 'ALL':
        bs_count = len(self.brush_styles_filtered)
        for i, bs in enumerate(reversed(self.brush_styles_filtered[:])):
            if bs.type.upper() != self.brush_type:
                self.brush_styles_filtered.remove(bs_count-i-1)
    
    # filter by category
    if self.brush_category != 'ALL':
        bs_count = len(self.brush_styles_filtered)
        for i, bs in enumerate(reversed(self.brush_styles_filtered[:])):
            if bs.category.upper() != self.brush_category:
                self.brush_styles_filtered.remove(bs_count-i-1)

    # filter by name
    filtered_list = fnmatch.filter([bs.name.lower() for bs in self.brush_styles_filtered], f'*{self.name_filter}*'.lower())
    bs_count = len(self.brush_styles_filtered)
    for i, bs in enumerate(reversed(self.brush_styles_filtered[:])):
        if bs.name.lower() not in filtered_list:
            self.brush_styles_filtered.remove(bs_count-i-1)

    self.brush_styles_filtered_active_index = 0
    for i, bs in enumerate(self.brush_styles_filtered):
        if bs.name == active_bs_name:
            self.brush_styles_filtered_active_index = i
            break

    return

def transfer_modifier(modifier_name, target_obj, source_obj):
    """
    Core taken from https://projects.blender.org/studio/blender-studio-pipeline
    """

    # create target mod
    source_mod = source_obj.modifiers.get(modifier_name)
    target_mod = target_obj.modifiers.new(source_mod.name, source_mod.type)
    props = [p.identifier for p in source_mod.bl_rna.properties if not p.is_readonly]
    for prop in props:
        value = getattr(source_mod, prop)
        setattr(target_mod, prop, value)

    if source_mod.type == 'NODES':
        # Transfer geo node attributes
        for key, value in source_mod.items():
            try:
                target_mod[key] = value
            except (TypeError, ValueError) as e:
                target_mod[key] = type(target_mod[key])(value)

        # Transfer geo node bake settings
        target_mod.bake_directory = source_mod.bake_directory
        for index, target_bake in enumerate(target_mod.bakes):
            source_bake = source_mod.bakes[index]
            props = [p.identifier for p in source_bake.bl_rna.properties if not p.is_readonly]
            for prop in props:
                value = getattr(source_bake, prop)
                setattr(target_bake, prop, value)

def is_brushstrokes_object(object):
    if not object:
        return False
    return 'BSBST_active' in object.keys()

def is_surface_object(object):
    if not object:
        return False
    for ob in bpy.data.objects:
        if 'BSBST_surface_object' not in ob.keys():
            continue
        if ob['BSBST_surface_object'] == object:
            return True
    return False

def is_flow_object(object):
    if not object:
        return False
    for ob in bpy.data.objects:
        if 'BSBST_flow_object' not in ob.keys():
            continue
        if ob['BSBST_flow_object'] == object:
            return ob
    return False

def get_deformable(object):
    if not object:
        return False
    if 'BSBST_deformable' in object.keys():
        return object['BSBST_deformable']
    return False

def get_animated(object):
    if not object:
        return False
    if 'BSBST_animated' in object.keys():
        return object['BSBST_animated']
    return False

def set_deformable(object, deformable=True):
    if not object:
        return
    object['BSBST_deformable'] = bool(deformable)

def set_animated(object, animated=True):
    if not object:
        return
    object['BSBST_animated'] = bool(animated)

def get_surface_object(bs):
    if not bs:
        return None
    if 'BSBST_surface_object' not in bs.keys():
        return None
    return bs['BSBST_surface_object']

def set_surface_object(bs, surf_ob):
    if not bs:
        return
    objects = [bs]
    flow_ob = get_flow_object(bs)
    if flow_ob:
        objects += [flow_ob]
    # assign surface pointer
    for ob in objects:
        for mod in bs.modifiers:
            mod_info = bs.modifier_info.get(mod.name)
            if not mod_info:
                continue
            for s in mod_info.socket_info:
                if not s.link_context:
                    continue
                if not s.link_context_type == 'SURFACE_OBJECT':
                    continue
                mod[s.name] = surf_ob
        ob.parent = surf_ob
        ob.parent_type = 'OBJECT'
    surf_ob.update_tag()

    if bs.type == 'CURVES':
        bs.data.surface = surf_ob
        bs.data.surface_uv_map = surf_ob.data.uv_layers.active.name

    bs['BSBST_surface_object'] = surf_ob

def get_flow_object(bs):
    if not bs:
        return None
    if 'BSBST_flow_object' not in bs.keys():
        return None
    return bs['BSBST_flow_object']

def set_flow_object(bs, ob):
    if not bs:
        return
    # assign flow pointer
    for mod in bs.modifiers:
        mod_info = bs.modifier_info.get(mod.name)
        if not mod_info:
            continue
        for s in mod_info.socket_info:
            if not s.link_context:
                continue
            if not s.link_context_type == 'FLOW_OBJECT':
                continue
            mod[s.name] = ob
    ob.update_tag()

    bs['BSBST_flow_object'] = ob

def context_brushstrokes(context):
    settings = context.scene.BSBST_settings
    return settings.context_brushstrokes

def get_active_context_brushstrokes_object(context):
    settings = context.scene.BSBST_settings
    if not settings.context_brushstrokes:
        return None
    bs = settings.context_brushstrokes[settings.active_context_brushstrokes_index]
    bs_ob = bpy.data.objects.get(bs.name)
    return bs_ob

def get_active_context_surface_object(context):
    if not context.object:
        return None
    bs_ob = get_active_context_brushstrokes_object(context)
    if bs_ob:
        return get_surface_object(bs_ob)
    if context.object.type == 'MESH':
        return context.object

def flow_name(name):
    return f'{name}-FLOW'

def edit_active_brushstrokes(context):
    context.view_layer.depsgraph.update()

    bs_ob = get_active_context_brushstrokes_object(context)
    if not bs_ob:
        return {"CANCELLED"}
    
    flow_object = get_flow_object(bs_ob)
    surface_object = get_surface_object(bs_ob)
    active_object = bs_ob
    if flow_object:
        active_object = flow_object
    if not active_object:
        return {"CANCELLED"}

    context.view_layer.objects.active = active_object
    for ob in bpy.data.objects:
        ob.select_set(False)
    surface_object.select_set(True)
    active_object.select_set(True)

    # enter mode and tool context
    if active_object.type=='GREASEPENCIL':
        bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        context.scene.tool_settings.gpencil_stroke_placement_view3d = 'SURFACE'
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="brushstroke_tools.draw")
    return {'FINISHED'}

def round_n(val, n):
    """ Round value to n number of significant digits.
    """
    return round(val, n-int(math.floor(math.log10(abs(val))))-1)

def clear_preview():
    preview_img = bpy.data.images.get(preview_name)
    preview_texture = bpy.data.textures.get(preview_name)
    if preview_img:
        bpy.data.images.remove(preview_img)
    if preview_texture:
        bpy.data.textures.remove(preview_texture)

def set_preview(pixels, size = (256, 256), id=''):
    preview_img = bpy.data.images.get(preview_name)
    preview_texture = bpy.data.textures.get(preview_name)
    if not pixels or compare_versions(bpy.app.version, (4,2,4)) < 0:
        clear_preview()
        return
    if preview_img:
        if id and id == preview_img['BSBST-id']:
            return
        if not len(preview_img.pixels) == len(pixels):
            bpy.data.images.remove(preview_img)
            preview_img = None
    if not preview_img:
        preview_img = bpy.data.images.new(preview_name, width=size[0], height=size[1])

    if not preview_texture:
        preview_texture = bpy.data.textures.new(name=preview_name, type="IMAGE")
        settings = bpy.context.scene.BSBST_settings
        settings.preview_texture = preview_texture
    preview_texture.extension = 'EXTEND'
    preview_texture.crop_max_x = size[1]/size[0]
    preview_texture.image = preview_img
    
    preview_img.pixels.foreach_set(numpy.array(pixels, dtype=numpy.float32))
    preview_img['BSBST-id'] = id

    preview_img.pack()

    # TODO delete pre-save
    # TODO set height of preview region

class BSBST_brush_style(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='')
    id_name: bpy.props.StringProperty(default='')
    filepath: bpy.props.StringProperty(default='')
    category: bpy.props.StringProperty(default='')
    type: bpy.props.StringProperty(default='')

classes = [
    BSBST_brush_style,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.app.handlers.depsgraph_update_post.append(refresh_preset)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.app.handlers.depsgraph_update_post.remove(refresh_preset)