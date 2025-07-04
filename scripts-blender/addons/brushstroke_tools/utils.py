# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os, ast, fnmatch, platform, subprocess
from pathlib import Path
from zipfile import ZipFile
import bpy
from bpy.app.handlers import persistent
import math, shutil, errno, numpy
from bpy.app.handlers import persistent
from mathutils import Vector

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

def get_default_resource_directory() -> Path:
    path = Path.home().joinpath('Blender Studio Tools/Brushstroke Tools/')
    if platform.system() == "Windows":
        path = Path.home().joinpath('AppData/Roaming/Blender Studio Tools/Brushstroke Tools/')
    elif platform.system() == "Darwin":
        path = Path.home().joinpath('Library/Application Support/Blender Studio Tools/Brushstroke Tools/')
    else:
        path = Path.home().joinpath('.config/blender_studio_tools/brushstroke_tools/')
    return path

def get_resource_directory() -> Path:
    """
    Returns the path to be used to append resource data-blocks.
    """
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    resource_dir = addon_prefs.resource_path
    if resource_dir:
        return Path(resource_dir)
    else:
        return get_default_resource_directory()

def check_resources_valid():
    path = get_resource_directory()
    if not path.exists:
        return False
    
    check_paths = [
        "core/brushstroke_tools-resources.blend",
        "blender_assets.cats.txt",
        ".version"
    ]

    for s in check_paths:
        if not path.joinpath(s).exists():
            return False
    return True

def unpack_resources():
    if check_resources_valid():
        lib_version = read_lib_version()
        if compare_versions(addon_version, lib_version)<=0:
            return
        addon_prefs = bpy.context.preferences.addons[__package__].preferences
        if addon_prefs.resource_path != '': #TODO: more options for auto-update or popup
            return
    copy_resources_to_dir()
    update_asset_lib_path()

def import_resources(ng_names = ng_list, filepath = ''):
    """
    Imports the necessary blend data resources required by the addon.
    """
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    if not filepath:
        filepath = get_resource_directory()

    data_pre = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_pre |= set(getattr(bpy.data, attr))

    resource_path = str(filepath.joinpath('core/brushstroke_tools-resources.blend'))
    with bpy.data.libraries.load(resource_path, link=addon_prefs.import_method=='LINK', relative=addon_prefs.import_relative_path) as (data_src, data_dst):
        data_dst.node_groups = ng_names[:]
    if addon_prefs.import_method=='APPEND':
        # pack imported resources
        for img in bpy.data.images:
            if not img.library_weak_reference:
                continue
            if img.packed_file:
                continue
            if 'brushstroke_tools-resources.blend' in img.library_weak_reference.filepath:
                img.pack()

    data_post = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_post |= set(getattr(bpy.data, attr))
    
    return data_post - data_pre

def read_lib_version(dir: Path = None):
    if not dir:
        dir = get_resource_directory()
    with open(dir.joinpath(".version"), "r") as file:
        version = ast.literal_eval(file.read())
        return version

def write_lib_version(dir: Path = None):
    if not dir:
        dir = get_resource_directory()
    with open(dir.joinpath(".version"), "w") as file:
        file.write(str(addon_version))

def copy_resources_to_dir(tgt_dir = ''):
    source_dir = get_addon_directory().joinpath('assets')
    if not tgt_dir:
        tgt_dir = get_resource_directory()

    try:
        shutil.copytree(source_dir, tgt_dir, dirs_exist_ok=True)
        write_lib_version()
    except OSError as err:
        # error caused if the source was not a directory
        if err.errno == errno.ENOTDIR:
            shutil.copy2(source_dir, tgt_dir)
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

def split_id_name(name):
    if not '.'in name:
        return (name, None)
    name_el = name.split('.')
    extension = name_el[-1]
    if not extension.isdigit():
        return (name, None)
    name_string = '.'.join(name_el[:-1])
    return (name_string, extension)

def import_brushstroke_material():
    name = 'Brush Material'
    path = str(get_resource_directory().joinpath('core/brushstroke_tools-resources.blend'))
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

def import_node_group(name, path):
    ng_pre = set(bpy.data.node_groups)

    addon_prefs = bpy.context.preferences.addons[__package__].preferences

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

    new_ids = set(bpy.data.node_groups) - ng_pre

    for ng in new_ids:
        if ng.name == name:
            return ng
        
    for ng in new_ids:
        if split_id_name(name)[0] == split_id_name(ng.name)[0]:
            return ng
    return None

def ensure_node_group(name, path=''):
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    
    if not path:
        path=str(get_resource_directory().joinpath('core/brushstroke_tools-resources.blend'))

    ng = import_node_group(name, path)
    
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
    if not 'node_groups' in dir(bpy.data):
        return
    add_brush_styles_from_names(bs_list, [ng.name for ng in bpy.data.node_groups], '', name_filter = [bs.name for bs in bs_list])

def add_brush_styles_from_names(bs_list, ng_names, filepath, name_filter = []):

    names = [name for name in ng_names if name.startswith('BSBST-BS')]

    for ng_name in names:
        name, extension = split_id_name(ng_name)
        name_elements = name.split('.')
        if extension:
            name_elements = name_elements[:-1]+[f'{name_elements[-1]}.{extension}']
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
    if not 'libraries' in dir(bpy.data):
        return
    subdirs = [f.path for f in os.scandir(path) if f.is_dir()]
    files = [f.path for f in os.scandir(path) if not f.is_dir()]

    for filepath in files:
        if not filepath.endswith('.blend'):
            continue

        names = []
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            add_brush_styles_from_names(bs_list, data_from.node_groups, filepath)

    for d in subdirs:
        add_brush_styles_from_directory(bs_list, d)

def find_brush_style_by_name(name: str):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    for brush_style in addon_prefs.brush_styles:
        if name == brush_style.name:
            return brush_style
    return None

def link_to_collections_by_ref(obj, ref_obj):
        col_list = []
        for col in ref_obj.users_collection:
            if col.library:
                continue
            col_list += [col]
        
        if col_list:
            for col in col_list:
                col.objects.link(obj)
        else:
            if bpy.context.collection.library:
                bpy.context.scene.collection.objects.link(obj)
            else:
                bpy.context.collection.objects.link(obj)

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
    Core taken from https://projects.blender.org/studio/blender-studio-tools
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

def find_local_geonodes_resources():
    ids = dict()
    for ob in bpy.data.objects:
        if ob.library:
            continue
        if not is_brushstrokes_object(ob):
            continue
        for mod in ob.modifiers:
            if mod.type != 'NODES':
                continue
            if fnmatch.filter(ng_list, split_id_name(mod.node_group.name)[0]):
                if mod.node_group not in ids.keys():
                    ids[mod.node_group] = [ob]
                else:
                    ids[mod.node_group] += [ob]
    return ids

def find_local_material_resources():
    ids = dict()
    for mat in bpy.data.materials:
        if mat.library:
            continue
        if 'BSBST' in mat.keys():
            ids[mat] = []

    for ob in bpy.data.objects:
        if ob.library:
            continue
        if not is_brushstrokes_object(ob):
            continue
        for m_slot in ob.material_slots:
            if not m_slot.material:
                continue
            mat = m_slot.material
            if mat in ids.keys():
                ids[mat] += [ob]
    return ids

def find_local_brush_style_resources():
    ids = dict()
    for ng in bpy.data.node_groups:
        if ng.library:
            continue
        if ng.name.startswith('BSBST-BS'):
            ids[ng] = []

    for mat in bpy.data.materials:
        if mat.library:
            continue
        if not mat.node_tree:
            continue
        node = mat.node_tree.nodes.get('Brush Style')
        if node is None:
            continue
        ng = node.node_tree
        if not ng:
            continue
        if ng in ids.keys():
            ids[ng] += [mat]
    return ids

def blend_data_from_id(id):
    for attr in dir(bpy.data):
        data = getattr(bpy.data, attr)
        if not data:
            continue
        if not type(data) == type(bpy.data.scenes):
            continue
        if id.id_type == data[0].id_type:
            return data
    return None

def force_cleanup_ids_recursive(ids):
    flag = False
    for id in list(ids)[:]:
        if id.users == id.use_fake_user:
            ids.remove(id)
            blend_data_from_id(id).remove(id)
            flag = True
    if flag:
        force_cleanup_ids_recursive(ids)

def force_remove_id_and_dependencies(id_remove):
    data = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data |= set(getattr(bpy.data, attr))
        
    for id in list(data)[:]:
        if id == id_remove:
            continue
        if id.users == id.use_fake_user:
            data.remove(id)
    
    if id_remove not in data:
        blend_data_from_id(id_remove).remove(id_remove)
        return
    else:
        data.remove(id_remove)
        blend_data_from_id(id_remove).remove(id_remove)
    
    force_cleanup_ids_recursive(data)

def version_modifiers(object):

    version_prev = object['BSBST_version']

    for mod in object.modifiers:
        if not mod.type == 'NODES':
            continue
    
        ng = mod.node_group
        if not ng:
            continue

    object['BSBST_version'] = addon_version

    return

def upgrade_geonodes_from_library():
    del_id = set()
    
    data_pre = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_pre |= set(getattr(bpy.data, attr))

    id_new = import_resources()

    for id in id_new:
        id_name, id_extension = split_id_name(id.name)
        if id_name not in ng_list:
            continue
        for id_local in blend_data_from_id(id):
            if id_local == id:
                continue
            ng_local_name, ng_local_extension = split_id_name(id_local.name)
            if not ng_local_name == id_name:
                continue
            id_local.user_remap(id)
            # check and remove old id
            if id_local.users == id_local.use_fake_user:
                del_id.add(id_local)

    for id in del_id:
        force_remove_id_and_dependencies(id)

    # rename new ids
    for id in id_new:
        if id.library:
            continue
        id_name, id_extension = split_id_name(id.name)
        if id_extension:
            id.name = id_name

    data_post = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_post |= set(getattr(bpy.data, attr))

    new_ids = data_post - data_pre

    force_cleanup_ids_recursive(new_ids)

    for ob in bpy.data.objects:
        if not is_brushstrokes_object(ob):
            continue
        version_modifiers(ob)

    return

def copy_curve_mapping(tgt_mapping, src_mapping):
    for tgt_curve, src_curve in zip(tgt_mapping.curves, src_mapping.curves):
        for i in range(len(tgt_curve.points)-2):
            tgt_curve.points.remove(tgt_curve.points[0])
        
        for i in range(len(src_curve.points)-2):
            tgt_p = tgt_curve.points.new(0,0)
        
        for i in range(len(src_curve.points)):
            src_p = src_curve.points[i]
            tgt_p = tgt_curve.points[i]
            for el in dir(src_p):
                try:
                    setattr(tgt_p, el, getattr(src_p, el))
                except:
                    pass
    tgt_mapping.update()
    return

def match_mat(tgt_mat, src_mat):
    """ Retain settings of brushstroke material to upgrade node-tree version.
    """
    path_list = [
        "brush_style",
        "diffuse_color",
        "node_tree.nodes['Color Attribute'].mute",
        "node_tree.nodes['Color Texture'].mute",
        "node_tree.nodes['Color'].outputs[0].default_value",
        "node_tree.nodes['Image Texture'].image",
        "node_tree.nodes['UV Map'].uv_map",
        "node_tree.nodes['Color Variation'].inputs[0].default_value",
        "node_tree.nodes['Variation Scale'].outputs[0].default_value",
        "node_tree.nodes['Variation Hue'].inputs[0].default_value",
        "node_tree.nodes['Variation Saturation'].inputs[0].default_value",
        "node_tree.nodes['Variation Luminance'].inputs[0].default_value",
        "node_tree.nodes['Use Strength'].mute",
        "node_tree.nodes['Opacity'].inputs[0].default_value",
        "node_tree.nodes['Backface Culling'].mute",
        "node_tree.nodes['Principled BSDF'].inputs[1].default_value",
        "node_tree.nodes['Principled BSDF'].inputs[2].default_value",
        "node_tree.nodes['Bump'].mute",
        "node_tree.nodes['Bump'].inputs[0].default_value",
        "node_tree.nodes['Translucency Add'].mute",
        "node_tree.nodes['Translucency Strength'].inputs[0].default_value",
        "node_tree.nodes['Translucency Tint'].inputs[7].default_value",
        "node_tree.nodes['Brush Style'].node_group",
    ]

    for attr_path in path_list:
        try:
            exec(f'tgt_mat.{attr_path} = src_mat.{attr_path}')
        except:
            pass
    
    tgt_curve_node = tgt_mat.node_tree.nodes.get('Brush Curve')
    src_curve_node = src_mat.node_tree.nodes.get('Brush Curve')

    copy_curve_mapping(tgt_curve_node.mapping, src_curve_node.mapping)
    
    tgt_bs_node = tgt_mat.node_tree.nodes.get('Brush Style')
    src_bs_node = src_mat.node_tree.nodes.get('Brush Style')

    if not tgt_bs_node or not src_bs_node:
        print("ERROR: Could not find Brush Style node in material!")
        return

    for i, input in enumerate(src_bs_node.inputs):
        tgt_bs_node.inputs[i].default_value = input.default_value

    return

def clear_FX_nodes(nt):
    # clear target FX nodes
    del_nodes = []
    node = nt.nodes.get('Effects In')
    while True:
        if not node.outputs:
            break
        s = node.outputs.get('Value')
        if not s:
            s = node.outputs[0]
        if not s.links:
            break
        node = s.links[0].to_node
        if not node:
            break
        if node.name == 'Effects Out':
            break
        del_nodes += [node]
    for n in del_nodes:
        nt.nodes.remove(n)

def transfer_FX_nodes(new_mat, old_mat):

    tgt_nt = new_mat.node_tree
    src_nt = old_mat.node_tree

    clear_FX_nodes(tgt_nt)

    # insert new nodes
    src_FX_nodes = []
    node = src_nt.nodes.get('Effects In')
    while True:
        if not node.outputs:
            break
        s = node.outputs.get('Value')
        if not s:
            s = node.outputs[0]
        if not s.links:
            break
        node = s.links[0].to_node
        if not node:
            break
        if node.name == 'Effects Out':
            break
        src_FX_nodes += [node]

    attr_list = [
        'name',
        'label',
        'node_tree',
        'location',
        'mute',
    ]

    tgt_FX_nodes = []
    for n in src_FX_nodes:
        n_new = tgt_nt.nodes.new(n.bl_idname)
        tgt_FX_nodes += [n_new]

        for attr in attr_list:
            if not attr in dir(n):
                continue
            setattr(n_new, attr, getattr(n, attr))
        
        if n.parent:
            new_parent = tgt_nt.nodes.get(n.parent.name)
            if new_parent:
                n_new.parent = new_parent
                n_new.location = Vector(n_new.location) + Vector(new_parent.location)

        # link inputs
        for tgt_in, src_in in zip(n_new.inputs, n.inputs):
            for l in src_in.links:
                n_out = tgt_nt.nodes.get(l.from_node.name)
                if not n_out:
                    continue
                s_out = n_out.outputs.get(l.from_socket.name)
                if not s_out:
                    continue
                l_new = tgt_nt.links.new(s_out, tgt_in)

        # link outputs
        for tgt_out, src_out in zip(n_new.outputs, n.outputs):
            for l in src_out.links:
                n_in = tgt_nt.nodes.get(l.to_node.name)
                if not n_in:
                    continue
                s_in = n_in.inputs.get(l.to_socket.name)
                if not s_in:
                    continue
                l_new = tgt_nt.links.new(tgt_out, s_in)
        
        # copy values
        for tgt_in, src_in in zip(n_new.inputs, n.inputs):
            tgt_in.default_value = src_in.default_value

    # offset location by effects in
    offset = Vector(src_nt.nodes.get('Effects In').location - tgt_nt.nodes.get('Effects In').location)
    for tgt_n in tgt_FX_nodes:
        tgt_n.location = Vector(tgt_n.location) + offset

    return

def upgrade_materials_from_library():

    mats = find_local_material_resources().keys()
    
    data_pre = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_pre |= set(getattr(bpy.data, attr))

    base_mat = import_brushstroke_material()

    for old_mat in mats:
        new_mat = base_mat.copy()
        match_mat(new_mat, old_mat)
        old_mat.user_remap(new_mat)
        transfer_FX_nodes(new_mat, old_mat)
        name = old_mat.name
        bpy.data.materials.remove(old_mat)
        new_mat.name = name

    bpy.data.materials.remove(base_mat)

    data_post = set()
    for attr in dir(bpy.data):
        if not type(getattr(bpy.data, attr)) == type(bpy.data.scenes):
            continue
        data_post |= set(getattr(bpy.data, attr))

    new_ids = data_post - data_pre

    force_cleanup_ids_recursive(new_ids)

    return

def upgrade_brush_styles_from_library():
    
    refresh_brushstroke_styles()

    for mat in bpy.data.materials:
        if 'BSBST' not in mat.keys():
            continue
        if not mat.brush_style:
            continue

        brush_style = find_brush_style_by_name(mat.brush_style)
        if not brush_style.filepath:
            continue

        ng_old = bpy.data.node_groups.get(brush_style.id_name)
        if not ng_old:
            continue

        ng_new = import_node_group(brush_style.id_name, brush_style.filepath)
        if not ng_new:
            continue

        ng_old.user_remap(ng_new)
        bpy.data.node_groups.remove(ng_old)
        ng_new.name = brush_style.id_name

    return

def open_in_file_manager(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

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