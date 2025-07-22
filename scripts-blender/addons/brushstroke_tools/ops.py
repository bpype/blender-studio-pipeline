# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import random
from . import utils, settings
import mathutils

class BSBST_OT_new_brushstrokes(bpy.types.Operator):
    """ Create new object according to method and type.
    Link to correct collection.
    Attach to selection context if applicable.
    Assign selected modifier setup. Enter correct context for editing.
    """
    bl_idname = "brushstroke_tools.new_brushstrokes"
    bl_label = "New Brushstrokes"
    bl_description = "Create new brushstrokes object of selected type with all the necessary setup in place"
    bl_options = {"REGISTER", "UNDO"}

    method: bpy.props.StringProperty(default='SURFACE_FILL')

    @classmethod
    def poll(cls, context):
        surface_object = utils.get_active_context_surface_object(context)
        return bool(surface_object)

    def new_brushstrokes_object(self, context, name, surface_object):
        settings = context.scene.BSBST_settings
        settings.brushstroke_method = self.method

        if settings.curve_mode == 'GP':
            bpy.ops.object.grease_pencil_add(type='EMPTY')
            context.object.name = name
            context.object.data.name = name
            brushstrokes_object = context.object
            context.collection.objects.unlink(brushstrokes_object)
        else:
            if settings.curve_mode == 'CURVE':
                brushstrokes_data = bpy.data.curves.new(name, type='CURVE')
                brushstrokes_data.dimensions = '3D'
            elif settings.curve_mode == 'CURVES':
                brushstrokes_data = bpy.data.hair_curves.new(name)
            brushstrokes_object = bpy.data.objects.new(name, brushstrokes_data)

        # link to surface object's collections (fall back to active collection if all are linked data)
        utils.link_to_collections_by_ref(brushstrokes_object, surface_object, unlink=False)

        brushstrokes_object.visible_shadow = False
        brushstrokes_object['BSBST_version'] = utils.addon_version
        utils.set_deformable(brushstrokes_object, settings.deforming_surface)
        utils.set_animated(brushstrokes_object, settings.animated)
        return brushstrokes_object

    def new_flow_object(self, context, name, surface_object):
        settings = context.scene.BSBST_settings
        if settings.curve_mode == 'GP':
            bpy.ops.object.grease_pencil_add(type='EMPTY')
            context.object.name = name
            context.object.data.name = name
            flow_object = context.object
            context.collection.objects.unlink(flow_object)
        else:
            if settings.curve_mode == 'CURVE':
                flow_data = bpy.data.curves.new(name, type='CURVE')
                flow_data.dimensions = '3D'
            elif settings.curve_mode == 'CURVES':
                flow_data = bpy.data.hair_curves.new(name)
            flow_object = bpy.data.objects.new(name, flow_data)

        # link to surface object's collections (fall back to active collection if all are linked data)
        utils.link_to_collections_by_ref(flow_object, surface_object, unlink=False)
        
        visibility_options = [
            'visible_camera',
            'visible_diffuse',
            'visible_glossy',
            'visible_transmission',
            'visible_volume_scatter',
            'visible_shadow',
        ]
        for vis in visibility_options:
            setattr(flow_object, vis, False)

        ## add pre-processing modifier
        mod = flow_object.modifiers.new('Pre-Processing', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.pre_processing']

        mod_info = flow_object.modifier_info.add()
        mod_info.name = mod.name

        utils.mark_socket_context_type(mod_info, 'Socket_2', 'SURFACE_OBJECT')

        mod['Socket_2'] = surface_object
        mod['Socket_3'] = False

        utils.set_deformable(flow_object, settings.deforming_surface)
        utils.set_animated(flow_object, settings.animated)
        return flow_object

    def main(self, context):
        settings = context.scene.BSBST_settings
        
        utils.ensure_resources()
        if not context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        surface_object = utils.get_active_context_surface_object(context)
        flow_object = None

        if not surface_object.data.uv_layers.active:
            self.report({"ERROR"}, "Surface Object needs an available UV Map")
            return {"CANCELLED"}

        name = utils.bs_name(surface_object.name)
        brushstrokes_object = self.new_brushstrokes_object(context, name, surface_object)
        flow_is_required = settings.brushstroke_method == 'SURFACE_FILL'
        if flow_is_required:
            flow_object = None
            if settings.reuse_flow:
                if settings.context_brushstrokes:
                    bs = bpy.data.objects.get(settings.context_brushstrokes[settings.active_context_brushstrokes_index].name)
                    if 'BSBST_flow_object' in bs.keys():
                        flow_object = bs['BSBST_flow_object']
            if not flow_object:
                flow_object = self.new_flow_object(context, utils.flow_name(name), surface_object)

        # attach surface object pointer
        if surface_object:
            utils.set_surface_object(brushstrokes_object, surface_object)
        if flow_object:
            brushstrokes_object['BSBST_flow_object'] = flow_object
        brushstrokes_object['BSBST_active'] = True
        brushstrokes_object['BSBST_method'] = settings.brushstroke_method

        if surface_object:
            surface_object.add_rest_position_attribute = True # TODO report if library data
            brushstrokes_object.parent = surface_object
            if flow_object:
                flow_object.parent = surface_object

        if not settings.preset_object:
            bpy.ops.brushstroke_tools.init_preset()
        
        # assign preset material
        preset_material = getattr(settings.preset_object, '["BSBST_material"]', None)

        if preset_material:
            override = context.copy()
            override['object'] = brushstrokes_object
            with context.temp_override(**override):
                bpy.ops.object.material_slot_add()
                brushstrokes_object.material_slots[0].material = preset_material
        settings.context_material = preset_material
        brushstrokes_object['BSBST_material'] = settings.context_material

        # transfer preset modifiers to new brushstrokes TODO: refactor to deduplicate
        for mod in settings.preset_object.modifiers:
            utils.transfer_modifier(mod.name, brushstrokes_object, settings.preset_object)
            
            for v in mod.node_group.interface.items_tree.values():
                if type(v) not in utils.linkable_sockets:
                    continue
                if not settings.preset_object.modifier_info[mod.name].socket_info[v.identifier].link_context:
                    continue
                # initialize linked context parameters
                link_context_type = settings.preset_object.modifier_info[mod.name].socket_info[v.identifier].link_context_type
                if link_context_type=='SURFACE_OBJECT':
                    brushstrokes_object.modifiers[mod.name][f'{v.identifier}'] = surface_object
                elif link_context_type=='FLOW_OBJECT':
                    brushstrokes_object.modifiers[mod.name][f'{v.identifier}'] = flow_object
                elif link_context_type=='MATERIAL':
                    brushstrokes_object.modifiers[mod.name][f'{v.identifier}'] = settings.context_material
                elif link_context_type=='UVMAP':
                    if type(brushstrokes_object.modifiers[mod.name][f'{v.identifier}']) == str:
                        brushstrokes_object.modifiers[mod.name][f'{v.identifier}'] = surface_object.data.uv_layers.active.name
                    else:
                        brushstrokes_object.modifiers[mod.name][f'{v.identifier}_use_attribute'] = True
                        brushstrokes_object.modifiers[mod.name][f'{v.identifier}_attribute_name'] = surface_object.data.uv_layers.active.name
                elif link_context_type=='RANDOM':
                    vmin = v.min_value
                    vmax = v.max_value
                    val = vmin + random.random() * (vmax - vmin)
                    brushstrokes_object.modifiers[mod.name][f'{v.identifier}_use_attribute'] = False
                    brushstrokes_object.modifiers[mod.name][f'{v.identifier}'] = type(brushstrokes_object.modifiers[mod.name][f'{v.identifier}'])(val)
        
        # transfer modifier info data from preset to brush strokes
        utils.deep_copy_mod_info(settings.preset_object, brushstrokes_object)

        # estimate dimensions

        if settings.estimate_dimensions:
            bb_min = mathutils.Vector(surface_object.bound_box[0])
            bb_max = mathutils.Vector(surface_object.bound_box[6])
            bb_radius = mathutils.Vector([abs(co) for co in bb_max-bb_min]).length * 0.5

            surf_est = 4 * 3.142 * bb_radius**2

            mod = brushstrokes_object.modifiers['Brushstrokes']
            if settings.brushstroke_method == 'SURFACE_FILL':
                # set density
                mod['Socket_7'] = utils.round_n((1000 / surf_est) ** 0.5, 2)
                # set length
                mod['Socket_11'] = utils.round_n(bb_radius * 0.5, 2)
                # set width
                mod['Socket_13'] = utils.round_n(bb_radius * 0.05, 2)
            elif settings.brushstroke_method == 'SURFACE_DRAW':
                # set width
                mod['Socket_5'] = utils.round_n(bb_radius * 0.05, 2)

        # refresh UI
        for mod in brushstrokes_object.modifiers:
            mod.node_group.interface_update(context)

        if settings.assign_materials:
            for mod in brushstrokes_object.modifiers:
                for v in mod.node_group.interface.items_tree.values():
                    if type(v) != bpy.types.NodeTreeInterfaceSocketMaterial:
                        continue
                    mat = mod[v.identifier]
                    if not mat:
                        continue
                    if mat in [m_slot.material for m_slot in brushstrokes_object.material_slots]:
                        continue
                    override = context.copy()
                    override['object'] = brushstrokes_object
                    with context.temp_override(**override):
                        bpy.ops.object.material_slot_add()
                        brushstrokes_object.material_slots[-1].material = mat
        
        # set deformable
        set_brushstrokes_deformable(brushstrokes_object, settings.deforming_surface)
        
        # set animated
        set_brushstrokes_animated(brushstrokes_object, settings.animated)
        
        for mod in brushstrokes_object.modifiers:
            mod.show_group_selector = False

        # update brushstroke context
        utils.find_context_brushstrokes(context.scene, context.view_layer.depsgraph)
        for i, name in enumerate([bs.name for bs in settings.context_brushstrokes]):
            if name == brushstrokes_object.name:
                settings.active_context_brushstrokes_index = i
                break
        
        utils.edit_active_brushstrokes(context)
        return {"FINISHED"}

    def execute(self, context):
        settings = context.scene.BSBST_settings
        settings.silent_switch = True
        state = self.main(context)
    
        settings.silent_switch = False
        return state
    
class BSBST_OT_edit_brushstrokes(bpy.types.Operator):
    """
    Enter the editing context for the active context brushstrokes. 
    """
    bl_idname = "brushstroke_tools.edit_brushstrokes"
    bl_label = "Edit Brushstrokes"
    bl_description = " Enter the editing context for the active context brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings
        settings.silent_switch = True
        state = utils.edit_active_brushstrokes(context)
    
        settings.silent_switch = False
        return state
    
class BSBST_OT_delete_brushstrokes(bpy.types.Operator):
    """
    Delete the active context brushstrokes 
    """
    bl_idname = "brushstroke_tools.delete_brushstrokes"
    bl_label = "Delete Brushstrokes"
    bl_description = "Delete the active context brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings

        edit_toggle = settings.edit_toggle
        settings.edit_toggle = False

        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            settings.edit_toggle = edit_toggle
            return {"CANCELLED"}

        surface_object = utils.get_surface_object(bs_ob)
        flow_object = utils.get_flow_object(bs_ob)

        if context.active_object:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.objects.remove(bs_ob)
        settings.active_context_brushstrokes_index = max(0, settings.active_context_brushstrokes_index-1)

        if surface_object:
            context.view_layer.objects.active = surface_object
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if bs_ob:
            context.view_layer.objects.active = bs_ob
            bs_ob.select_set(True)

        if not flow_object:
            settings.edit_toggle = edit_toggle
            return {"FINISHED"}

        # delete controller objects
        if flow_object.users <= 1:
            bpy.data.objects.remove(flow_object)

        settings.edit_toggle = edit_toggle
        return {'FINISHED'}
    
class BSBST_OT_duplicate_brushstrokes(bpy.types.Operator):
    """
    Duplicate the active context brushstrokes 
    """
    bl_idname = "brushstroke_tools.duplicate_brushstrokes"
    bl_label = "Duplicate Brushstrokes"
    bl_description = "Duplicate the active context brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings

        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            return {"CANCELLED"}
        
        if not bs_ob.visible_get(view_layer=context.view_layer):
            self.report({"WARNING"}, f"Skipped Brushstroke layer '{bs_ob.name}' because it is invisible in this context")
            return {"CANCELLED"}

        flow_object = utils.get_flow_object(bs_ob)

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.context.view_layer.objects.active = bs_ob
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.data.objects:
            ob.select_set(False)
        bs_ob.select_set(True)
        if flow_object and not settings.reuse_flow:
            flow_object.select_set(True)
        bpy.ops.object.duplicate_move()

        # reshuffle seed
        for ob in context.selected_editable_objects:
            for mod in ob.modifiers:
                if not mod.type=='NODES':
                    continue
                if not mod.node_group:
                    continue            
                for v in mod.node_group.interface.items_tree.values():
                    if type(v) not in utils.linkable_sockets:
                        continue
                    if not ob.modifier_info[mod.name].socket_info[v.identifier].link_context:
                        continue
                    # initialize linked context parameters
                    link_context_type = ob.modifier_info[mod.name].socket_info[v.identifier].link_context_type
                    if link_context_type=='RANDOM':
                        vmin = v.min_value
                        vmax = v.max_value
                        val = vmin + random.random() * (vmax - vmin)
                        mod[f'{v.identifier}'] = type(ob.modifiers[mod.name][f'{v.identifier}'])(val)

        return {'FINISHED'}

class BSBST_OT_copy_brushstrokes(bpy.types.Operator):
    """
    Copy the active context brushstrokes to the selected surface objects 
    """
    bl_idname = "brushstroke_tools.copy_brushstrokes"
    bl_label = "Copy Brushstrokes to Selected"
    bl_description = "Copy the active context brushstrokes to the selected surface objects"
    bl_options = {"REGISTER", "UNDO"}

    copy_all: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings

        active_surface_object = utils.get_surface_object(utils.get_active_context_brushstrokes_object(context.scene))

        surface_objects = [ob for ob in context.selected_objects
                            if ob.type=='MESH'
                            and not utils.is_brushstrokes_object(ob)
                            and not ob==active_surface_object]
        if not surface_objects:
            return {"CANCELLED"}

        if self.copy_all:
            bs_objects = [bpy.data.objects.get(bs.name) for bs in settings.context_brushstrokes]
            bs_objects = [bs for bs in bs_objects if bs]
        else:
            bs_objects = [utils.get_active_context_brushstrokes_object(context.scene)]
        if not bs_objects:
            return {"CANCELLED"}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for surface_object in surface_objects:
            for ob in bpy.data.objects:
                ob.select_set(False)
            for bs_ob in bs_objects:
                if not bs_ob.visible_get(view_layer=context.view_layer):
                    self.report({"WARNING"}, f"Skipped Brushstroke layer '{bs_ob.name}' because it is invisible in this context")
                    continue
                bs_ob.select_set(True)
                flow_object = utils.get_flow_object(bs_ob)
                if not flow_object:
                    continue
                flow_object.select_set(True)

            all_obj = set(bpy.data.objects[:])
            context.view_layer.depsgraph.update()
            bpy.ops.object.duplicate_move()
            new_bs = list(set(bpy.data.objects[:]) - all_obj)
            del all_obj

            # remap surface pointers and context linked data TODO: refactor to deduplicate
            for ob in new_bs:
                utils.link_to_collections_by_ref(ob, surface_object)

                # if it's still using the default name initialize names again
                if utils.split_id_name(ob.name)[0] == utils.bs_name(active_surface_object.name):
                    if utils.is_flow_object(ob):
                        ob.name = utils.flow_name(utils.bs_name(surface_object.name))
                    else:
                        ob.name = utils.bs_name(surface_object.name)
                elif ob.name.startswith(active_surface_object.name):
                    ob.name = f"{surface_object.name}{ob.name[len(active_surface_object.name):]}"

                ob.parent = surface_object
                utils.set_surface_object(ob, surface_object)
                
                for mod in ob.modifiers:
                    if not mod.type:
                        continue
                    if not mod.node_group:
                        continue
                    mod_info = ob.modifier_info.get(mod.name)
                    if not mod_info:
                        continue
                    for v in mod.node_group.interface.items_tree.values():
                        if type(v) not in utils.linkable_sockets:
                            continue
                        if not mod_info.socket_info[v.identifier].link_context:
                            continue
                        # re-initialize linked context parameters
                        link_context_type = ob.modifier_info[mod.name].socket_info[v.identifier].link_context_type
                        if link_context_type=='SURFACE_OBJECT':
                            ob.modifiers[mod.name][f'{v.identifier}'] = surface_object
                        elif link_context_type=='UVMAP':
                            if type(ob.modifiers[mod.name][f'{v.identifier}']) == str:
                                ob.modifiers[mod.name][f'{v.identifier}'] = surface_object.data.uv_layers.active.name
                            else:
                                ob.modifiers[mod.name][f'{v.identifier}_use_attribute'] = True
                                ob.modifiers[mod.name][f'{v.identifier}_attribute_name'] = surface_object.data.uv_layers.active.name
                        elif link_context_type=='RANDOM':
                            vmin = v.min_value
                            vmax = v.max_value
                            val = vmin + random.random() * (vmax - vmin)
                            ob.modifiers[mod.name][f'{v.identifier}_use_attribute'] = False
                            ob.modifiers[mod.name][f'{v.identifier}'] = type(ob.modifiers[mod.name][f'{v.identifier}'])(val)
        

                # enable rest position
                surface_object.add_rest_position_attribute = True

        return {'FINISHED'}
    
class BSBST_OT_select_surface(bpy.types.Operator):
    """
    Select the surface object for the active context brushstrokes.
    """
    bl_idname = "brushstroke_tools.select_surface"
    bl_label = "Select Surface"
    bl_description = "Select the surface object for the active context brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            return {"CANCELLED"}
        surface_object = getattr(bs_ob, '["BSBST_surface_object"]', None)
        if not surface_object:
            return {"CANCELLED"}
        
        bpy.context.view_layer.objects.active = surface_object
        if not context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.data.objects:
            ob.select_set(False)
        surface_object.select_set(True)

        return {"FINISHED"}

class BSBST_OT_assign_surface(bpy.types.Operator):
    """
    Assign a surface object for the active context brushstrokes.
    """
    bl_idname = "brushstroke_tools.assign_surface"
    bl_label = "Assign Surface"
    bl_description = "Assign a surface object for the active context brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    surface_object: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            return {"CANCELLED"}
        
        surface_object = bpy.data.objects.get(self.surface_object)

        if not surface_object:
            return {"CANCELLED"}

        # TODO handle parenting with keep transform as default option
        utils.set_surface_object(bs_ob, surface_object)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'surface_object', bpy.data, 'objects')

    def invoke(self, context, event):
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        surf_ob = utils.get_surface_object(bs_ob)
        if surf_ob:
            self.surface_object = surf_ob.name
        return context.window_manager.invoke_props_dialog(self)

def set_brushstrokes_deformable(bs_ob, deformable):
    flow_ob = utils.get_flow_object(bs_ob)

    for mod in bs_ob.modifiers:
        if not mod.type == 'NODES':
            continue
        if not mod.node_group:
            continue
        if mod.node_group.name == '.brushstroke_tools.pre_processing':
            mod['Socket_3'] = deformable
        elif mod.node_group.name == '.brushstroke_tools.surface_fill':
            mod['Socket_27'] = deformable
        elif mod.node_group.name == '.brushstroke_tools.surface_draw':
            mod['Socket_15'] = deformable

        mod.node_group.interface_update(bpy.context)
    utils.set_deformable(bs_ob, deformable)
    if not flow_ob:
        return
    utils.set_deformable(flow_ob, deformable)

def set_brushstrokes_animated(bs_ob, animated):
    flow_ob = utils.get_flow_object(bs_ob)

    if flow_ob:
        ob = flow_ob
    else:
        ob = bs_ob
    mod = ob.modifiers.get('Animation')
    if animated:
        if not mod:
            mod = ob.modifiers.new('Animation', 'NODES')
            mod.node_group = utils.ensure_node_group('.brushstroke_tools.animation')
        
            mod_info = ob.modifier_info.get(mod.name)
            if not mod_info:
                mod_info = ob.modifier_info.add()
                mod_info.name = mod.name

            # ui visibility settings
            mod_info.hide_ui = True
        else:
            mod['Socket_5'] = True
            mod.node_group.interface_update(bpy.context)
        with bpy.context.temp_override(object=ob):
            bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
    else:
        if mod:
            ob.modifiers.remove(mod)
    utils.set_animated(bs_ob, animated)
    if not flow_ob:
        return
    utils.set_animated(flow_ob, animated)

class BSBST_OT_copy_flow(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.copy_flow"
    bl_label = "Copy Flow from Existing"
    bl_description = "Copy the flow object from another brushstroke layer."
    bl_options = {"REGISTER", "UNDO"}

    source_bs:  bpy.props.StringProperty(name="Brushstroke Layers")
    bs_list:    bpy.props.CollectionProperty(type=settings.BSBST_context_brushstrokes)
    
    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        flow_ob_old = utils.get_flow_object(bs_ob)
        if not bs_ob:
            return {"CANCELLED"}
        
        # get source

        source_ob = bpy.data.objects.get(self.source_bs)
        flow_ob = utils.get_flow_object(source_ob)
        if not source_ob or not flow_ob:
            return {"CANCELLED"}

        # set flow object

        utils.set_flow_object(bs_ob, flow_ob)

        # delete old flow if unused necessary

        if not flow_ob_old:
            return {"FINISHED"}
        for bs in self.bs_list:
            flow_ob = utils.get_flow_object(source_ob)
            if not flow_ob:
                continue
            if flow_ob.name == flow_ob_old.name:
                return {"FINISHED"}

        bpy.data.objects.remove(flow_ob_old)

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'source_bs', self, 'bs_list', icon='OUTLINER_OB_FORCE_FIELD')

    def invoke(self, context, event):
        settings = context.scene.BSBST_settings

        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)

        for i in range(len(self.bs_list)):
            self.bs_list.remove(0)

        for bs in settings.context_brushstrokes:
            if not bs.method=='SURFACE_FILL':
                continue
            if bs.name==bs_ob.name:
                continue
            bs_new = self.bs_list.add()
            bs_new.name = bs.name
            bs_new.hide_viewport_base = bs.hide_viewport_base

        if self.bs_list:
            self.source_bs = self.bs_list[0].name
        return context.window_manager.invoke_props_dialog(self)

class BSBST_OT_switch_deformable(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.switch_deformable"
    bl_label = "Switch Deformable"
    bl_description = "Switch the deformable state of the brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    deformable: bpy.props.BoolProperty( default=True,
                                        name="Deformable",)
    switch_all: bpy.props.BoolProperty( default=False,
                                        name="All Brushstrokes",
                                        description="Switch all Brushstroke Layers of Current Surface Object.")

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings

        if self.deformable:
            surf_ob = utils.get_active_context_surface_object(context)
            if surf_ob:
                for mod in surf_ob.modifiers:
                    if mod.type == 'MIRROR':
                        self.report({"WARNING"}, "Surface Objects with mirror modifier cannot properly support stable deformation. Apply the mirror modifier to proceed.")

        if self.switch_all:
            bs_objects = [bpy.data.objects.get(bs.name) for bs in settings.context_brushstrokes]
            bs_objects = [bs for bs in bs_objects if bs]
        else:
            bs_objects = [utils.get_active_context_brushstrokes_object(context.scene)]
        if not bs_objects:
            return {"CANCELLED"}

        for ob in bs_objects:
            if self.deformable:
                if utils.compare_versions(bpy.app.version, (5,0,0)) < 0: # TODO adjust for when GP supports node tool execution
                    if ob.type == 'GREASEPENCIL':
                        self.report({"WARNING"}, "Grease Pencil does not currently support drawing on deformable surface geometry.")
            set_brushstrokes_deformable(ob, self.deformable)
        
        context.view_layer.depsgraph.update()

        return {"FINISHED"}

class BSBST_OT_switch_animated(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.switch_animated"
    bl_label = "Switch Animated"
    bl_description = "Switch the atnimated state of the brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    animated: bpy.props.BoolProperty( default=True,
                                        name="Animated",)
    switch_all: bpy.props.BoolProperty( default=False,
                                        name="All Brushstrokes",
                                        description="Switch all Brushstroke Layers of Current Surface Object.")

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return bool(settings.context_brushstrokes)

    def execute(self, context):
        settings = context.scene.BSBST_settings

        if self.switch_all:
            bs_objects = [bpy.data.objects.get(bs.name) for bs in settings.context_brushstrokes]
            bs_objects = [bs for bs in bs_objects if bs]
        else:
            bs_objects = [utils.get_active_context_brushstrokes_object(context.scene)]
        if not bs_objects:
            return {"CANCELLED"}

        for ob in bs_objects:
            set_brushstrokes_animated(ob, self.animated)
        
        context.view_layer.depsgraph.update()

        return {"FINISHED"}
        
class BSBST_OT_init_preset(bpy.types.Operator):
    """
    Initialize the preset to define a modifier stack applied to new brushstrokess.
    """
    bl_idname = "brushstroke_tools.init_preset"
    bl_label = "Initialize Preset"
    bl_description = "Initialize the preset environment to setup a predefined modifier stack for new brushstrokess"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return settings.preset_object is None
    
    def init_fill(self, context):
        settings = context.scene.BSBST_settings

        preset_object = settings.preset_object

        # add modifiers
        ## input
        mod = preset_object.modifiers.new('Surface Input', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.geometry_input']
        
        mod_info = settings.preset_object.modifier_info.get(mod.name)
        if not mod_info:
            mod_info = settings.preset_object.modifier_info.add()
            mod_info.name = mod.name

        # context link settings
        utils.mark_socket_context_type(mod_info, 'Socket_2', 'SURFACE_OBJECT')

        # ui visibility settings
        mod_info.hide_ui = True

        mod_info.default_closed = True

        ## masking
        mod = preset_object.modifiers.new('Masking', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.mask_surface']
        
        mod_info = settings.preset_object.modifier_info.get(mod.name)
        if not mod_info:
            mod_info = settings.preset_object.modifier_info.add()
            mod_info.name = mod.name

        mod_info.default_closed = True

        # ui visibility settings
        hide_sockets =[
            'Socket_5',
        ]
        for s in hide_sockets:
            utils.mark_socket_hidden(mod_info, s)

        ## brushstrokes
        mod = preset_object.modifiers.new('Brushstrokes', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.surface_fill']
        
        mod_info = settings.preset_object.modifier_info.get(mod.name)
        if not mod_info:
            mod_info = settings.preset_object.modifier_info.add()
            mod_info.name = mod.name

        # set fill custom defaults

        mod['Socket_59'] = 1 # color method: curves

        # context link settings
        utils.mark_socket_context_type(mod_info, 'Socket_2', 'FLOW_OBJECT')
        utils.mark_socket_context_type(mod_info, 'Socket_3', 'UVMAP')
        utils.mark_socket_context_type(mod_info, 'Socket_9', 'RANDOM')
        utils.mark_socket_context_type(mod_info, 'Socket_12', 'MATERIAL')
        utils.mark_socket_context_type(mod_info, 'Socket_60', 'FLOW_OBJECT')

        # ui visibility settings
        hide_sockets =[
            'Socket_2',
            'Socket_3',
            #'Socket_9', # seed
            'Socket_12',
            'Socket_15',
            'Socket_27',
            'Socket_37',
            'Socket_40',
            'Socket_62',
            'Socket_67', # mesh loops
        ]
        for s in hide_sockets:
            utils.mark_socket_hidden(mod_info, s)

        hide_panels = [
            'Stroke Culling',
            'Lighting Influence',
            'Offset Override',
            'Debug',
        ]
        for p in hide_panels:
            utils.mark_panel_hidden(mod_info, p)
    
    def init_draw(self, context):
        settings = context.scene.BSBST_settings

        preset_object = settings.preset_object

        # add modifiers
        ## add pre-processing modifier
        mod = preset_object.modifiers.new('Pre-Processing', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.pre_processing']
        
        mod_info = settings.preset_object.modifier_info.get(mod.name)
        if not mod_info:
            mod_info = settings.preset_object.modifier_info.add()
            mod_info.name = mod.name

        utils.mark_socket_context_type(mod_info, 'Socket_2', 'SURFACE_OBJECT')

        # ui visibility settings
        mod_info.hide_ui = True

        ## brushstrokes
        mod = preset_object.modifiers.new('Brushstrokes', 'NODES')
        mod.node_group = bpy.data.node_groups['.brushstroke_tools.surface_draw']
        
        mod_info = settings.preset_object.modifier_info.get(mod.name)
        if not mod_info:
            mod_info = settings.preset_object.modifier_info.add()
            mod_info.name = mod.name

        utils.mark_socket_context_type(mod_info, 'Socket_2', 'SURFACE_OBJECT')
        utils.mark_socket_context_type(mod_info, 'Socket_4', 'MATERIAL')
        utils.mark_socket_context_type(mod_info, 'Socket_6', 'RANDOM')
        utils.mark_socket_context_type(mod_info, 'Socket_12', 'UVMAP')

        # ui visibility settings
        hide_sockets =[
            'Socket_2',
            'Socket_3',
            'Socket_4',
            #'Socket_6', # seed
            'Socket_12',
            'Socket_15',
            'Socket_24',
            'Socket_35', # mesh loops
        ]
        for s in hide_sockets:
            utils.mark_socket_hidden(mod_info, s)

        hide_panels = [
            'Debug',
        ]
        for p in hide_panels:
            utils.mark_panel_hidden(mod_info, p)

    def execute(self, context):

        settings = context.scene.BSBST_settings
        
        utils.ensure_resources()
        preset_name = f'BSBST-PRESET_{settings.brushstroke_method}'
        preset_object = bpy.data.objects.new(preset_name, bpy.data.hair_curves.new(preset_name))
        settings.preset_object = preset_object

        if settings.brushstroke_method == "SURFACE_FILL":
            self.init_fill(context)
        elif settings.brushstroke_method == "SURFACE_DRAW":
            self.init_draw(context)
        
        # select preset material
        mat = bpy.data.materials.get('Brush Material')
        if not mat:
            mat = utils.import_brushstroke_material()
        settings.silent_switch = True
        settings.context_material = mat
        settings.silent_switch = False
        preset_object['BSBST_material'] = settings.context_material

        return {"FINISHED"}

class BSBST_OT_make_preset(bpy.types.Operator):
    """
    Make the current brushstrokes style specification the active preset.
    """
    bl_idname = "brushstroke_tools.make_preset"
    bl_label = "Make Preset"
    bl_description = "Make the current brushstrokes style specification the active preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(utils.get_active_context_brushstrokes_object(context.scene))

    def execute(self, context):

        settings = context.scene.BSBST_settings

        if not settings.preset_object:
            preset_name = f'BSBST-PRESET_{settings.brushstroke_method}'
            settings.preset_object = bpy.data.objects.new(preset_name, bpy.data.hair_curves.new(preset_name))
        else:
            for mod in settings.preset_object.modifiers[:]:
                settings.preset_object.modifiers.remove(mod)
            
        # transfer brushstrokes modifiers to preset
        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            return {"CANCELLED"}
        for mod in bs_ob.modifiers:
            utils.transfer_modifier(mod.name, settings.preset_object, bs_ob)
        utils.refresh_preset(None)

        for mod in settings.preset_object.modifiers:
            # refresh UI
            mod.node_group.interface_update(context)
            
            # identify linked sockets
            for v in mod.node_group.interface.items_tree.values():
                if type(v) not in utils.linkable_sockets:
                    continue
                if not settings.preset_object.modifier_info[mod.name].socket_info[v.identifier]:
                    continue
                if type(v) == bpy.types.NodeTreeInterfaceSocketObject:
                    if bs_ob['BSBST_surface_object']==mod[v.identifier]:
                        mod[v.identifier] = None
                        settings.preset_object.modifier_info[mod.name].socket_info[v.identifier].link_context = True
                elif type(v) == bpy.types.NodeTreeInterfaceSocketMaterial:
                    pass # TODO: figure out material preset linking
        return {"FINISHED"}

class BSBST_OT_preset_add_mod(bpy.types.Operator):
    """
    Add a modifier to the preset stack. 
    """
    bl_idname = "brushstroke_tools.preset_add_mod"
    bl_label = "Add Preset Modifier"
    bl_description = "Add a modifier to the preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return settings.preset_object

    def execute(self, context):

        settings = context.scene.BSBST_settings
        settings.preset_object.modifiers.new('Brushstrokes Style', type='NODES')

        return {"FINISHED"}

class BSBST_OT_preset_remove_mod(bpy.types.Operator):
    """
    Remove a modifier from the preset stack. 
    """
    bl_idname = "brushstroke_tools.preset_remove_mod"
    bl_label = "Remove Preset Modifier"
    bl_description = "Remove a modifier from the preset"
    bl_options = {"REGISTER", "UNDO"}

    modifier: bpy.props.StringProperty(default='')

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return settings.preset_object

    def execute(self, context):

        settings = context.scene.BSBST_settings
        with context.temp_override(object=settings.preset_object):
            bpy.ops.object.modifier_remove(modifier=self.modifier)

        return {"FINISHED"}

class BSBST_OT_preset_toggle_attribute(bpy.types.Operator):
    """
    Toggle use_attribute property for a socket on a specific object's modifier.
    (Workaround due to how these are actually stored as integer in Blender)
    """
    bl_idname = "brushstroke_tools.preset_toggle_attribute"
    bl_label = "Toggle Attribute"
    bl_description = "Toggle using a named attribute for this input"
    bl_options = {"REGISTER", "UNDO"}

    modifier_name: bpy.props.StringProperty(default='GeometryNodes')
    input_name: bpy.props.StringProperty(default='Socket_2')

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return settings.preset_object

    def execute(self, context):
        settings = context.scene.BSBST_settings
        override = context.copy()
        override['object'] = settings.preset_object
        with context.temp_override(**override):
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name=self.input_name,
                                                                 modifier_name=self.modifier_name)
        return {"FINISHED"}

class BSBST_OT_brushstrokes_toggle_attribute(bpy.types.Operator):
    """
    Toggle use_attribute property for a socket on a specific object's modifier.
    (Workaround due to how these are actually stored as integer in Blender)
    """
    bl_idname = "brushstroke_tools.brushstrokes_toggle_attribute"
    bl_label = "Toggle Attribute"
    bl_description = "Toggle using a named attribute for this input"
    bl_options = {"REGISTER", "UNDO"}

    modifier_name: bpy.props.StringProperty(default='GeometryNodes')
    input_name: bpy.props.StringProperty(default='Socket_2')

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        return settings.preset_object

    def execute(self, context):
        settings = context.scene.BSBST_settings

        edit_toggle = settings.edit_toggle
        settings.edit_toggle = False

        bs_ob = utils.get_active_context_brushstrokes_object(context.scene)
        if not bs_ob:
            settings.edit_toggle = edit_toggle
            return {"CANCELLED"}
        
        override = context.copy()
        override['object'] = bs_ob
        with context.temp_override(**override):
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name=self.input_name,
                                                                 modifier_name=self.modifier_name)
        return {"FINISHED"}
        
class BSBST_OT_render_setup(bpy.types.Operator):
    """
    Set up render settings. 
    """
    bl_idname = "brushstroke_tools.render_setup"
    bl_label = "Render Setup"
    bl_description = "Set up render settings"
    bl_options = {"REGISTER", "UNDO"}

    render_engine: bpy.props.EnumProperty(name='Render Engine',
        items = [
            ('ALL', 'All', 'Set up for all available render engines', '', 0),
            ('CYCLES', 'Cycles', 'Set up for Cycles', '', 1),
            ('EEVEE', 'Eevee', 'Set up for Eevee', '', 2),
        ]
    )
    trans_pass_toggle: bpy.props.BoolProperty(default=True)
    trans_pass: bpy.props.IntProperty(name='Transparency Passes', default=256, min=0, soft_max=1024)

    prop_map = {
        'CYCLES':['trans_pass',
        ],
        'EEVEE':[
        ]
    }

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'render_engine', text='')
        for k, v in self.prop_map.items():
            if self.render_engine not in [k, 'ALL']:
                continue
            layout.label(text=k.capitalize())
            for prop in v:
                split = layout.split(factor=.1)
                split.prop(self, f'{prop}_toggle', icon_only=True)
                split.active = getattr(self, f'{prop}_toggle', False)
                split.prop(self, prop)

    def execute(self, context):
        settings = context.scene.BSBST_settings
        if self.render_engine in ['CYCLES', 'ALL']:
            if self.trans_pass_toggle:
                context.scene.cycles.transparent_max_bounces = self.trans_pass
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
        
class BSBST_OT_view_all(bpy.types.Operator):
    """
    Enable/disable all brushstrokes for the viewport. 
    """
    bl_idname = "brushstroke_tools.view_all"
    bl_label = "Enable/Disable All"
    bl_description = "Enable/disable all brushstrokes for the viewport"
    bl_options = {"REGISTER", "UNDO"}

    disable: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        for ob in bpy.data.objects:
            if not utils.is_brushstrokes_object(ob):
                continue
            if ob.hide_viewport == self.disable:
                continue
            else:
                ob.hide_viewport = self.disable
        return {"FINISHED"}

def brush_style_category_items(self, context):
    addon_prefs = context.preferences.addons[__package__].preferences

    items = [
        ('ALL', 'All', '', '', 0),
    ]
    available_categories = set(bs.category for bs in addon_prefs.brush_styles)
    for category_name in available_categories:
        if not category_name:
            continue
        items.append((category_name.upper(), category_name, '', '', len(items)))
    return items

def brush_style_type_items(self, context):
    addon_prefs = context.preferences.addons[__package__].preferences

    items = [
        ('ALL', 'All', '', '', 0),
    ]
    available_types = set(bs.type for bs in addon_prefs.brush_styles)
    for type_name in available_types:
        if not type_name:
            continue
        items.append((type_name.upper(), type_name, '', '', len(items)))
    return items


class BSBST_UL_brush_styles_filtered(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        resource_dir = utils.get_resource_directory()
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            if not item.filepath:
                split.label(text=item.name, icon='FILE_BLEND')
            else:
                split.label(text=item.name, icon='BRUSHES_ALL')

            row = split.row()
            row.label(text=item.category)

            row = split.row()
            row.label(text=item.type)
        elif self.layout_type == 'GRID':
            layout.label(text=item.name)

    def draw_filter(self, context, layout):
        return
class BSBST_OT_select_brush_style(bpy.types.Operator):
    """
    Select Brush Style for context material. 
    """
    bl_idname = "brushstroke_tools.select_brush_style"
    bl_label = "Select Brush Style"
    bl_description = "Select Brush Style"
    bl_options = {"REGISTER", "UNDO"}

    name_filter: bpy.props.StringProperty(name='Name Filter', default='', update=utils.update_filtered_brush_styles)

    brush_category: bpy.props.EnumProperty(name='Category', items=brush_style_category_items, update=utils.update_filtered_brush_styles)
    brush_type: bpy.props.EnumProperty(name='Type', items=brush_style_type_items, update=utils.update_filtered_brush_styles)

    brush_styles_filtered: bpy.props.CollectionProperty(type=utils.BSBST_brush_style)
    brush_styles_filtered_active_index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        settings = context.scene.BSBST_settings
        if not settings.context_material:
            return False
        if settings.context_material.library:
            return False
        return True

    def draw(self, context):
        settings = context.scene.BSBST_settings

        layout = self.layout

        row = layout.row()
        split = row.split(factor=.45)
        split.label(text='Name')
        split = split.split(factor=.45)
        split.label(text='Category')
        split.label(text='Type')

        row = layout.row(align=True)
        split = row.split(factor=.45)
        split.prop(self, 'name_filter', text='', icon='FILTER')
        split = split.split(factor=.45)
        split.prop(self, 'brush_category', text='')
        split.prop(self, 'brush_type', text='')

        layout.template_list("BSBST_UL_brush_styles_filtered", "", self, "brush_styles_filtered",
                        self, "brush_styles_filtered_active_index", rows=3, maxrows=5, sort_lock=True)

    def execute(self, context):
        settings = context.scene.BSBST_settings
        if len(self.brush_styles_filtered) == 0:
            return {"CANCELLED"}
        settings.context_material.brush_style = self.brush_styles_filtered[self.brush_styles_filtered_active_index].name
        return {"FINISHED"}

    def invoke(self, context, event):
        settings = context.scene.BSBST_settings

        utils.refresh_brushstroke_styles()

        utils.update_filtered_brush_styles(self, context)
        for i, bs in enumerate(self.brush_styles_filtered):
            if bs.name == settings.context_material.brush_style:
                self.brush_styles_filtered_active_index = i
                break
        
        self.name_filter = ''

        return context.window_manager.invoke_props_dialog(self, width=450)
    
class BSBST_OT_upgrade_resources(bpy.types.Operator):
    """ Upgrade all local BST assets to available addon resources.
    """
    bl_idname = "brushstroke_tools.upgrade_resources"
    bl_label = "Upgrade Resources"
    bl_description = "Upgrade local BST assets to available addon resources."
    bl_options = {"REGISTER", "UNDO"}

    upgrade_shape_modifiers: bpy.props.BoolProperty(name='Shape Modifiers', default=True)
    upgrade_materials: bpy.props.BoolProperty(name='Materials', default=True)
    upgrade_brush_styles: bpy.props.BoolProperty(name='Brush Styles', default=True)

    modifier_id_count = 0
    modifier_user_count = 0

    material_id_count = 0
    material_user_count = 0

    brush_style_id_count = 0
    brush_style_user_count = 0

    def draw(self, context):
        settings = context.scene.BSBST_settings

        layout = self.layout

        split = layout.split(factor=.6)
        
        col = split.column()
        col.prop(self, 'upgrade_shape_modifiers', icon='MODIFIER')
        col.prop(self, 'upgrade_materials', icon='MATERIAL')
        col.prop(self, 'upgrade_brush_styles', icon='BRUSHES_ALL')
        
        col = split.column()
        row = col.row()
        row.active = self.upgrade_shape_modifiers
        row.label(text=f'({self.modifier_id_count} IDs, {self.modifier_user_count} users)')
        row = col.row()
        row.active = self.upgrade_materials
        row.label(text=f'({self.material_id_count} IDs, {self.material_user_count} users)')
        row = col.row()
        row.active = self.upgrade_brush_styles
        row.label(text=f'({self.brush_style_id_count} IDs, {self.brush_style_user_count} users)')

    def execute(self, context):
        settings = context.scene.BSBST_settings

        if self.upgrade_shape_modifiers and self.modifier_id_count:
            utils.upgrade_geonodes_from_library()
        if self.upgrade_materials and self.material_id_count:
            utils.upgrade_materials_from_library()
        if self.upgrade_brush_styles and self.brush_style_id_count:
            utils.upgrade_brush_styles_from_library()

        return {"FINISHED"}

    def invoke(self, context, event):
        settings = context.scene.BSBST_settings

        mod_map = utils.find_local_geonodes_resources()
        self.modifier_id_count = len(mod_map)
        self.modifier_user_count = sum([len(v) for k,v in mod_map.items()])

        mat_map = utils.find_local_material_resources()
        self.material_id_count = len(mat_map)
        self.material_user_count = sum([len(v) for k,v in mat_map.items()])

        bs_map = utils.find_local_brush_style_resources()
        self.brush_style_id_count = len(bs_map)
        self.brush_style_user_count = sum([len(v) for k,v in bs_map.items()])

        return context.window_manager.invoke_props_dialog(self)

class BSBST_OT_new_material(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.new_material"
    bl_label = "New Brushstrokes Material"
    bl_description = "Create new material for the current brushstrokes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(utils.context_brushstrokes(context))

    def execute(self, context):
        settings = context.scene.BSBST_settings
        mat = utils.import_brushstroke_material()
        settings.context_material = mat
        return {"FINISHED"}

classes = [
    BSBST_OT_new_brushstrokes,
    BSBST_OT_edit_brushstrokes,
    BSBST_OT_delete_brushstrokes,
    BSBST_OT_duplicate_brushstrokes,
    BSBST_OT_copy_brushstrokes,
    BSBST_OT_copy_flow,
    BSBST_OT_switch_deformable,
    BSBST_OT_switch_animated,
    BSBST_OT_select_surface,
    BSBST_OT_assign_surface,
    BSBST_OT_init_preset,
    BSBST_OT_make_preset,
    BSBST_OT_preset_add_mod,
    BSBST_OT_preset_remove_mod,
    BSBST_OT_preset_toggle_attribute,
    BSBST_OT_brushstrokes_toggle_attribute,
    BSBST_OT_view_all,
    BSBST_OT_render_setup,
    BSBST_UL_brush_styles_filtered,
    BSBST_OT_select_brush_style,
    BSBST_OT_upgrade_resources,
    BSBST_OT_new_material,
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c) 

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)