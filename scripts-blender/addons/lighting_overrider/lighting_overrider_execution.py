# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import os
import json
import idprop
from pathlib import Path



def parse_rna_path_to_elements(rna_path, delimiter='.'):
    ''' Returns the element strings of an RNA path split by '.' delimiter, disregarding any delimiter in a string within the path.
    '''
    if not delimiter in rna_path:
        return [rna_path]
    
    parse = rna_path
    
    # replace escape chars with whitespaces
    parse_elements = parse.split(r'\\')
    parse = '  '.join(parse_elements)
        
    parse_elements = parse.split('\\')
    parse = parse_elements[0]
    for el in parse_elements[1:]:
        parse += '  '
        parse += el[1:]
    
    # replace strings within path with whitespaces
    parse_elements = parse.split('"')
    parse = parse_elements[0]
    for el1, el2 in zip(parse_elements[1::2], parse_elements[2::2]):
        parse += '"'+' '*len(el1)+'"'
        parse += el2
    
    parse_elements = parse.split(delimiter)
    
    elements = []
    for el in parse_elements:
        elements += [rna_path[:len(el)]]
        rna_path = rna_path[len(el)+len(delimiter):]
    
    return elements

def parse_rna_path_for_custom_property(rna_path):
    ''' Returns the rna path of the datablock and the name of the custom property for an rna path that describes a custom property. 
    '''
    if not '][' in rna_path:
        return False
    parse_elements = parse_rna_path_to_elements(rna_path, delimiter='][')
    return parse_elements[0]+']', '"'.join(parse_elements[1].split('"')[1:-1])

def mute_fcurve(db, path):
    if not db.animation_data:
        return
    if not db.animation_data.action:
        return
    
    fcurve = db.animation_data.action.fcurves.find(path)
    c = 0
    while fcurve or c<=4:
        if fcurve:
            fcurve.mute = True
        c += 1
        fcurve = db.animation_data.action.fcurves.find(path, index=c)
    return

def mute_driver(db, path):
    if not db.animation_data:
        return
    if not db.animation_data.drivers:
        return
    
    driver = db.animation_data.drivers.find(path)
    c = 0
    while driver or c<=4:
        if driver:
            driver.mute = True
        c += 1
        driver = db.animation_data.drivers.find(path, index=c)
    return

def mute_animation_on_rna_path(rna_path):
    path_elements = parse_rna_path_to_elements(rna_path)
    db_path = '.'.join(path_elements[:3])
    if 'session_uid' in dir(eval(db_path)):
        data_block = eval(db_path)
        path = '.'.join(path_elements[3:])
    else: # handle custom props
        db_path, c_prop = parse_rna_path_for_custom_property(rna_path)
        data_block = eval(db_path)
        path = f'["{c_prop}"]'

    if data_block.id_type in ['ACTION', 'BRUSH', 'COLLECTION', 'IMAGE', 'LIBRARY', 'PALETTE', 'PAINTCURVE', 'SCREEN', 'TEXT', 'WINDOWMANAGER', 'WORKSPACE']:
        return

    mute_fcurve(data_block, path)
    mute_driver(data_block, path)
    return

def split_by_suffix(list, sfx):
    with_suffix = [name[:-len(sfx)] for name in list if name.endswith(sfx)]
    without_suffix = [name for name in list if not name.endswith(sfx)]
    return without_suffix, with_suffix
def get_properties_bone(ob, prefix='Properties_'):
    
    if not ob.type == 'ARMATURE':
        return None
    
    for bone in ob.pose.bones:
        if not bone.name.startswith(prefix):
            continue
        return bone
    return None

def apply_variable_settings(data):
    ''' Applies settings to according nodes in the variables nodegroup.
    '''
    if not data:
        return
    
    for ng in bpy.data.node_groups:
        if not ng.name == 'VAR-settings':
            continue
        for name in data:
            node = ng.nodes.get(name)
            if node:
                node.outputs[0].default_value = data[name][0]
            else:
                print(f'Warning: Node {set} in variable settings nodegroup not found.')
    return

def apply_motion_blur_settings(data):
    ''' Deactivates deformation motion blur for objects in selected collections.
    '''
    if not data:
        return
    
    list_unique, list_all = split_by_suffix(data.keys(), ':all')
    
    if 'Master Collection' in data.keys() or 'Scene Collection' in data.keys():
        for ob in bpy.data.objects:
            if ob.type == 'CAMERA':
                continue
            ob.cycles.use_motion_blur = False
        return
        
    for col in bpy.data.collections:
        for name_col in list_all:
            if not col.name.startswith(name_col):
                continue
            for ob in col.all_objects:
                if ob.type == 'CAMERA':
                    continue
                ob.cycles.use_motion_blur = False
        # unique names
        if not col.name in list_unique:
            continue
        for ob in col.all_objects:
            if ob.type == 'CAMERA':
                continue
            ob.cycles.use_motion_blur = False
    return

def apply_shader_settings(data):
    ''' Assign shader setting properties to helper objects according to specified names.
    '''
    if not data:
        return
    
    list_unique, list_all = split_by_suffix(data.keys(), ':all')

    for ob in bpy.data.objects:
        # group names
        for name_ob in list_all:
            if not ob.name.startswith(name_ob):
                continue
            for name_set in data[name_ob+':all']:
                if not name_set in ob:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
                    continue
                ob[name_set] = data[name_ob+':all'][name_set][0]
        # unique names
        if ob.name in list_unique:
            for name_set in data[ob.name]:
                if name_set in ob:
                    ob[name_set] = data[ob.name][name_set][0]
                else:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
    return

def apply_rig_settings(data):
    ''' Assign rig setting properties to property bones according to specified names. Mutes fcurves from evaluation on those overriden properties.
    '''
    if not data:
        return
    
    list_unique, list_all = split_by_suffix(data.keys(), ':all')
    
    for ob in bpy.data.objects:
        # find properties bone (first posebone that starts with 'Properties_')
        if not ob.type == 'ARMATURE':
            continue
        bone_prop = get_properties_bone(ob)
        if not bone_prop:
            continue
        
        # group names
        for name_ob in list_all:
            if not ob.name.startswith(name_ob):
                continue
            for name_set in data[name_ob+':all']:
                if not name_set in bone_prop:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
                    continue
                data_path = f'pose.bones["{bone_prop.name}"]["{name_set}"]'
                mute_fcurve(ob, data_path)
                bone_prop[name_set] = data[name_ob+':all'][name_set][0]
                
        # unique names
        if ob.name in list_unique:
            for name_set in data[ob.name]:
                if name_set in bone_prop:
                    data_path = f'pose.bones["{bone_prop.name}"]["{name_set}"]'
                    mute_fcurve(ob, data_path)
                    bone_prop[name_set] = data[ob.name][name_set][0]
                else:
                    print(f'Warning: Property {name_set} on object {ob.name} not found.')
    return

def apply_rna_overrides(data):
    ''' Applies custom overrides on specified rna data paths.
    '''
    if not data:
        return

    for path in data:
        try:
            mute_animation_on_rna_path(path)
            if data[path][1] == 'STRING':
                exec(path+f" = '{data[path][0]}'")
            elif type(eval(path)) == idprop.types.IDPropertyArray:
                exec(path+f'[:] = {data[path][0]}') # workaround for Blender not retaining UI data of property (see https://projects.blender.org/blender/blender/pulls/109203)
            else:
                exec(path+f' = {data[path][0]}')
        except:
            print(f'Warning: Failed to assign property {data[path][2]} at {path}')
    return

def apply_settings(data):
    ''' Applies settings by categories using the specified category name and apply function.
    '''
    categories = {
        'variable_settings': apply_variable_settings,
        'motion_blur_settings': apply_motion_blur_settings,
        'shader_settings': apply_shader_settings,
        'rig_settings': apply_rig_settings,
        'rna_overrides': apply_rna_overrides,
        }
    
    for cat in categories:
        cat_data = data.get(cat)
        if cat_data:
            categories[cat](cat_data)
    return

def settings_from_datablock(datablock):
    ''' Return the settings dict from the text data-block.
    '''
    settings = {}
    if not datablock:
        return None
    if not datablock.as_string():
        return settings
    settings = json.loads(datablock.as_string())
    return settings

def force_reload_external(context, text):
    ''' Reloads text datablock from disk.
    '''
    if not text:
        return
    if text.is_in_memory:
        return
    if not (text.is_dirty or text.is_modified):
        return
    path = text.filepath
    path = bpy.path.abspath(path)
    if not os.path.isfile(path):
        return
    new_string = open(path, 'r').read()
    if not text.as_string() == new_string:
        text.from_string(new_string)
    return

def load_settings(context, name, path=None):
    ''' Return text datablock of the settings specified with a name. If a filepath is specified (re)load from disk.
    '''
    if path:
        path += f'/{name}.settings.json'
    
    settings_db = bpy.data.texts.get(f'{name}.settings.json')
    
    if settings_db:
        force_reload_external(context, settings_db)
        return settings_from_datablock(settings_db)
    
    if path:
        if not os.path.isfile(path):
            open(path, 'a').close()
        bpy.ops.text.open(filepath=bpy.path.relpath(path))
        settings_db = bpy.data.texts.get(f'{name}.settings.json')
    else:
        settings_db = bpy.data.texts.new(f'{name}.settings.json')
    return settings_from_datablock(settings_db)

if __name__=="__main__" or __name__=="lighting_overrider.execution":
    # Execution
    context = bpy.context

    sequence_settings = None
    shot_settings = None
    
    try:
        sequence_db = context.scene['LOR_sequence_settings']
        force_reload_external(context, sequence_db)
    except:
        sequence_db = None
        
    try:
        shot_db = context.scene['LOR_shot_settings']
        force_reload_external(context, shot_db)
    except:
        shot_db = None
        
    sequence_settings = settings_from_datablock(sequence_db)
    shot_settings = settings_from_datablock(shot_db)
    
    filepath = Path(bpy.context.blend_data.filepath)
    
    sequence_name, shot_name = filepath.parts[-3:-1]
    
    sequence_settings_path = filepath.parents[1].as_posix()
    
    if not sequence_settings:
        sequence_settings = load_settings(context, sequence_name, sequence_settings_path)
    if not shot_settings:
        shot_settings = load_settings(context, shot_name)

    apply_settings(sequence_settings)
    apply_settings(shot_settings)
    
    # kick re-evaluation
    for ob in bpy.data.objects:
        ob.update_tag()
