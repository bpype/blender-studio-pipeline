# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Modifier, Context, Collection, NodeTree, Operator, Object
from pathlib import Path
from typing import Any
from bpy.props import IntProperty, StringProperty, BoolProperty, FloatProperty
from .prefs import get_addon_prefs

NODETREE_NAME = "GN-shape_key"
COLLECTION_NAME = "GeoNode Shape Keys"


def geomod_get_identifier(modifier: Modifier, param_name: str) -> str:
    if hasattr(modifier.node_group, 'interface'):
        # 4.0
        input = modifier.node_group.interface.items_tree.get(param_name)
    else:
        # 3.6
        input = modifier.node_group.inputs.get(param_name)

    if input:
        return input.identifier


def geomod_get_data_path(modifier: Modifier, param_name: str) -> str:
    return f'modifiers["{modifier.name}"]["{geomod_get_identifier(modifier, param_name)}"]'


def geomod_set_param_value(modifier: Modifier, param_name: str, param_value: Any):
    input_id = geomod_get_identifier(modifier, param_name)
    # Note: Must use setattr, see T103865.
    setattr(modifier, f'["{input_id}"]', param_value)


def geomod_get_param_value(modifier: Modifier, param_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    return modifier[input_id]


def geomod_set_param_use_attribute(modifier: Modifier, param_name: str, use_attrib: bool):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id + "_use_attribute"] = use_attrib


def geomod_set_param_attribute(modifier: Modifier, param_name: str, attrib_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id + "_use_attribute"] = True
    modifier[input_id + "_attribute_name"] = attrib_name


def get_resource_blend_path(context) -> tuple[str, bool]:
    """Return the desired filepath to the .blend file containing the node set-up.
    Also return a boolean which indicates whether it should be linked or appended.
    """
    addon_prefs = get_addon_prefs(context)

    filepath = Path(addon_prefs.blend_path)
    if not filepath.exists():
        raise FileNotFoundError(
            f"Node tree file not found: '{filepath.as_posix()}'. Browse it in the add-on preferences."
        )

    return filepath.as_posix(), addon_prefs.node_import_type == 'LINK'


def link_shape_key_node_tree(context) -> NodeTree:
    # Load shape key node tree from a file.
    if NODETREE_NAME in bpy.data.node_groups:
        return bpy.data.node_groups[NODETREE_NAME]

    blend_path, do_link = get_resource_blend_path(context)

    with bpy.data.libraries.load(blend_path, link=do_link, relative=True) as (data_from, data_to):
        data_to.node_groups.append(NODETREE_NAME)

    return bpy.data.node_groups[NODETREE_NAME]


def ensure_shapekey_collection(context: Context) -> Collection:
    """Ensure and return a collection used for the objects created by the add-on."""
    scene = context.scene
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if not coll:
        coll = bpy.data.collections.new(COLLECTION_NAME)
        scene.collection.children.link(coll)
        coll.hide_render = True

    coll.hide_viewport = False
    if coll not in list(scene.collection.children):
        scene.collection.children.link(coll)

    context.view_layer.layer_collection.children[coll.name].exclude = False

    return coll


def get_gnsk_targets(gnsk):
    return gnsk.storage_object.geonode_shapekey_targets


def get_active_gnsk_targets(obj):
    active_gnsk = obj.geonode_shapekeys[obj.geonode_shapekey_index]
    return get_gnsk_targets(active_gnsk)


class OBJECT_OT_gnsk_add_shape(Operator):
    """Create a GeoNode modifier set-up and a duplicate object"""

    bl_idname = "object.add_geonode_shape_key"
    bl_label = "Add GeoNode Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    # TODO: Maybe add an option to keyframe this to only be active on this frame.
    shape_name: StringProperty(
        name="Shape Name",
        description="Name to identify this shape (used in the shape key and modifier names)",
    )
    uv_name: StringProperty(
        name="UVMap",
        description="UV Map to use for the deform space magic. All selected objects must have a map with this name, or the default will be used",
    )

    def invoke(self, context, _event):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue
            uvs = o.data.uv_layers
            if len(uvs) == 0:
                self.report({'ERROR'}, 'All selected mesh objects must have a UV Map!')
                return {'CANCELLED'}

        uvs = context.object.data.uv_layers
        self.uv_name = "GNSK" if "GNSK" in uvs else uvs[0].name

        self.shape_name = "ShapeKey: Frame " + str(context.scene.frame_current)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'uv_name', context.object.data, 'uv_layers', icon='GROUP_UVS')
        layout.prop(self, 'shape_name')

    def execute(self, context):
        try:
            get_resource_blend_path(context)
        except FileNotFoundError:
            self.report({'ERROR'}, "Node tree file not found. Check your Add-On preferences.")
            return {'CANCELLED'}

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                obj.select_set(False)

        mesh_objs = context.selected_objects
        for obj in mesh_objs:
            if self.uv_name not in obj.data.uv_layers:
                self.report({'ERROR'}, f'Object "{obj.name}" has no UV Map named "{self.uv_name}"!')
                return {'CANCELLED'}

        sk_ob = self.make_combined_sculpt_mesh(context, mesh_objs)

        for obj in mesh_objs:
            # Add GeoNode modifiers.
            gnsk = obj.geonode_shapekeys.add()
            gnsk.name = self.shape_name

            mod = obj.modifiers.new(gnsk.name, type='NODES')
            mod.node_group = link_shape_key_node_tree(context)

            # Find desired modifier index: After any other GNSK modifier, or if
            # none, before the SubSurf modifier.
            mod_index = self.get_desired_modifier_index(obj, mod)
            with context.temp_override(object=obj):
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=mod_index)
            gnsk.name = mod.name  # In case the modifier got a .001 suffix.

            gnsk.storage_object = sk_ob

            geomod_set_param_value(mod, 'Sculpt', sk_ob)
            uv_map = sk_ob.data.uv_layers.get(self.uv_name)
            if not uv_map:
                uv_map = sk_ob.data.uv_layers[0]
            geomod_set_param_attribute(mod, 'UVMap', uv_map.name)

            # Add references from the shape key object to the deformed objects.
            # This is used for the visibility switching operator.
            tgt = sk_ob.geonode_shapekey_targets.add()
            tgt.name = obj.name
            tgt.obj = obj

        # Change to Sculpt Mode.
        orig_ui = context.area.ui_type
        context.area.ui_type = 'VIEW_3D'
        bpy.ops.object.mode_set(mode='SCULPT')
        context.area.ui_type = orig_ui

        return {'FINISHED'}

    def make_combined_sculpt_mesh(
        self, context, mesh_objs: list[Object]
    ) -> Object:
        # Save evaluated objects into a new, combined object.
        for obj in mesh_objs:
            self.make_evaluated_object(context, obj)

        # Join all the shape key objects into one object...
        bpy.ops.object.join()
        sk_ob = context.active_object
        sk_ob.name = self.shape_name
        return sk_ob

    def get_desired_modifier_index(self, obj: Object, mod: Modifier) -> int:
        """Figure out the desired index to insert the next GeoNodes ShapeKey modifier at.
        If there are any other GNSK modifiers, we should insert after the last one.
        Otherwise, insert before any SubSurf modifiers, if any.
        Otherwise, insert at bottom of stack.
        """

        for i, m in reversed(list(enumerate(obj.modifiers))):
            if m == mod:
                continue
            if m.type == 'NODES' and m.node_group == mod.node_group:
                return i + 1

        for i, m in enumerate(obj.modifiers):
            if m.type == 'SUBSURF':
                return i

        return -1

    @staticmethod
    def disable_modifiers_after_subsurf(obj: Object) -> dict[str, dict[str, Any]]:
        """Disable modifiers that might cause the propagation of the sculpted shape to fail.
        This includes the Subsurf modifier and any subsequent modifiers.
        Possibly more in future.
        """
        modifier_states = {}
        found_subsurf = False
        for m in obj.modifiers:
            if m.type == 'SUBSURF':
                found_subsurf = True

            if found_subsurf:
                modifier_states[m.name] = {
                    'show_viewport': m.show_viewport,
                }

                # Mute driver, if any.
                if obj.animation_data:
                    fc = obj.animation_data.drivers.find(f'modifiers["{m.name}"].show_viewport')
                    if fc:
                        fc.mute = True
                m.show_viewport = False

        return modifier_states

    @staticmethod
    def restore_modifiers(obj: Object, modifier_states: dict[str, dict[str, Any]]):
        """Reset SubSurf and subsequent modifiers."""
        for mod_name, prop_dict in modifier_states.items():
            for key, value in prop_dict.items():
                setattr(obj.modifiers[mod_name], key, value)

                # Unmute driver, if any.
                if obj.animation_data:
                    fc = obj.animation_data.drivers.find(f'modifiers["{mod_name}"].{key}')
                    if fc:
                        fc.mute = False

    def make_evaluated_object(
        self, context: Context, obj: Object
    ) -> Object:

        obj.override_library.is_system_override = False

        # Disable the first SubSurf and all subsequent modifiers.
        # NOTE: Other generative modifiers beside SubSurf may have to trigger this too.
        modifier_states = self.disable_modifiers_after_subsurf(obj)
        eval_dg = context.evaluated_depsgraph_get()

        sk_mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(eval_dg))
        sk_ob = bpy.data.objects.new(obj.name + "." + self.shape_name, sk_mesh)
        sk_ob.data.name = sk_ob.name
        sk_coll = ensure_shapekey_collection(context)
        sk_coll.objects.link(sk_ob)

        # Add shape keys
        sk_ob.use_shape_key_edit_mode = True
        sk_ob.shape_key_add(name="Basis")
        sk_ob.hide_render = True
        adjust = sk_ob.shape_key_add(name="New Shape", from_mix=True)
        adjust.value = 1
        sk_ob.active_shape_key_index = 1
        sk_ob.add_rest_position_attribute = True

        sk_ob.matrix_world = obj.matrix_world

        self.restore_modifiers(obj, modifier_states)

        obj.hide_set(True)
        sk_ob.hide_set(False)
        sk_ob.select_set(True)
        context.view_layer.objects.active = sk_ob

        return sk_ob


class OBJECT_OT_gnsk_remove_shape(Operator):
    """Create a GeoNode modifier set-up and a duplicate object"""

    bl_idname = "object.remove_geonode_shape_key"
    bl_label = "Add GeoNode Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    remove_from_all: BoolProperty(
        name="Remove From All",
        description="Remove this shape from all affected objects, and delete the local object",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj = context.object

        if not obj:
            cls.poll_message_set("No active object.")
            return False

        if len(obj.geonode_shapekeys) == 0:
            cls.poll_message_set("Nothing to remove.")
            return False

        if 0 > obj.geonode_shapekey_index or obj.geonode_shapekey_index > len(obj.geonode_shapekeys):
            cls.poll_message_set("No active element.")
            return False

        return True

    def invoke(self, context, _event):
        if len(get_active_gnsk_targets(context.object)) > 1:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'remove_from_all')

        targets = get_active_gnsk_targets(context.object)
        if len(targets) > 1 and self.remove_from_all:
            layout.label(text="Shape will be removed from:")
            for target in targets:
                row = layout.row()
                row.enabled = False
                row.prop(target, 'obj', text="")

    def execute(self, context):
        ob = context.object
        active_gnsk = ob.geonode_shapekeys[ob.geonode_shapekey_index]

        objs = [ob]
        storage_ob = active_gnsk.storage_object
        delete_storage = False
        if self.remove_from_all:
            delete_storage = True
            if not storage_ob:
                self.report({'WARNING'}, f'Storage object was not found.')
            else:
                objs = [target.obj for target in storage_ob.geonode_shapekey_targets]

        for ob in objs:
            mod_removed = False

            for gnsk_idx, gnsk in enumerate(ob.geonode_shapekeys):
                if gnsk.storage_object == storage_ob:
                    break

            mod = gnsk.modifier
            if mod:
                ob.modifiers.remove(mod)
                mod_removed = True

            # Remove the GNSK slot
            ob.geonode_shapekeys.remove(gnsk_idx)

            # Fix the active index
            ob.geonode_shapekey_index = min(gnsk_idx, len(ob.geonode_shapekeys) - 1)

            # Remove the target reference from the storage object
            for i, target in enumerate(storage_ob.geonode_shapekey_targets):
                if target.obj == ob:
                    break
            storage_ob.geonode_shapekey_targets.remove(i)
            if len(storage_ob.geonode_shapekey_targets) == 0:
                delete_storage = True

            # Give feedback
            if mod_removed:
                self.report({'INFO'}, f'{ob.name}: Successfully deleted Object and Modifier.')
            else:
                self.report(
                    {'WARNING'}, f'{ob.name}: Modifier for "{active_gnsk.name}" was not found.'
                )

        if delete_storage:
            # Remove the storage object.
            bpy.data.objects.remove(storage_ob)
            # Remove collection if it's empty.
            coll = ensure_shapekey_collection(context)
            if len(coll.all_objects) == 0:
                bpy.data.collections.remove(coll)

        return {'FINISHED'}


class OBJECT_OT_gnsk_toggle_object(Operator):
    """Swap between the sculpt and overridden objects"""

    bl_idname = "object.geonode_shapekey_switch_focus"
    bl_label = "Switch to Render Objects"
    bl_options = {'REGISTER', 'UNDO'}

    gnsk_index: IntProperty(default=-1)

    @classmethod
    def poll(cls, context):

        obj = context.object
        if not obj:
            cls.poll_message_set("No active object.")
            return False

        if obj.geonode_shapekey_targets:
            return True

        if len(obj.geonode_shapekeys) == 0:
            cls.poll_message_set("Nothing to switch to.")
            return False

        if 0 > obj.geonode_shapekey_index or obj.geonode_shapekey_index > len(obj.geonode_shapekeys):
            cls.poll_message_set("No active element.")
            return False

        return True

    def execute(self, context):
        ob = context.object
        targets = ob.geonode_shapekey_targets

        if self.gnsk_index > -1:
            ob.geonode_shapekey_index = self.gnsk_index

        if targets:
            for target in targets:
                # Make sure to leave sculpt/edit mode, otherwise, sometimes
                # Blender can end up in a weird state, where the LINKED object
                # is in Sculpt mode (WTF?!) and you can't leave or do anything.
                bpy.ops.object.mode_set(mode='OBJECT')
                obs = [ob]
                collection = bpy.data.collections.get(COLLECTION_NAME)
                if collection:
                    obs = collection.all_objects
                for ob in obs:
                    ob.select_set(False)
                    ob.hide_set(True)

                target_ob = target.obj
                target_ob.hide_set(False)
                target_ob.select_set(True)
                context.view_layer.objects.active = target_ob

                # Trigger an update... otherwise, since we insert the modifier
                # somewhere other than the bottom of the stack, it sometimes
                # doesn't update live.
                target_ob.name = target_ob.name

        elif len(ob.geonode_shapekeys) > 0:
            storage = ob.geonode_shapekeys[ob.geonode_shapekey_index].storage_object
            if not storage:
                self.report({'ERROR'}, "No storage object to swap to.")
                return {'CANCELLED'}

            ob.select_set(False)
            ob.hide_set(True)

            storage.hide_set(False)
            storage.select_set(True)
            context.view_layer.objects.active = storage

            orig_ui = context.area.ui_type
            context.area.ui_type = 'VIEW_3D'
            bpy.ops.object.mode_set(mode='SCULPT')
            context.area.ui_type = orig_ui

        else:
            self.report({'ERROR'}, "No storage or target to swap to.")
            return {'CANCELLED'}

        return {'FINISHED'}


class OBJECT_OT_gnsk_influence_slider(Operator):
    """Change the influence on all affected meshes"""

    bl_idname = "object.geonode_shapekey_influence_slider"
    bl_label = "Change Influence of All Selected"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    gnsk_index: IntProperty(default=0)
    # TODO: If one day, Library Overrides support adding drivers (and saving and reloading the file),
    # this should be changed to instead allow assigning the active object's influence as the
    # driver for all others.
    insert_keyframe: BoolProperty(
        name="Insert Keyframe",
        description="Insert a keyframe on all affected values",
        default=False,
    )

    def update_slider(self, context):
        ob = context.object
        gnsk = ob.geonode_shapekeys[self.gnsk_index]
        for target in get_gnsk_targets(gnsk):
            obj = target.obj
            for obj_gnsk in obj.geonode_shapekeys:
                if obj_gnsk.storage_object == gnsk.storage_object:
                    geomod_set_param_value(obj_gnsk.modifier, 'Factor', self.slider_value)
                    if self.insert_keyframe:
                        obj.keyframe_insert(geomod_get_data_path(obj_gnsk.modifier, 'Factor'))
                    break

    slider_value: FloatProperty(
        name="Influence",
        description="Influence to set on all affected objects",
        update=update_slider,
        min=0,
        max=1,
    )

    def invoke(self, context, _event):
        self.insert_keyframe = context.scene.tool_settings.use_keyframe_insert_auto
        wm = context.window_manager
        self.slider_value = geomod_get_param_value(
            context.object.geonode_shapekeys[self.gnsk_index].modifier, 'Factor'
        )
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, 'slider_value', slider=True)
        layout.prop(self, 'insert_keyframe')

        ob = context.object
        gnsk = ob.geonode_shapekeys[self.gnsk_index]
        targets = get_gnsk_targets(gnsk)
        layout.label(text="Affected objects:")
        for target in targets:
            row = layout.row()
            row.enabled = False
            row.prop(target, 'obj', text="")

    def execute(self, context):
        return {'FINISHED'}


class OBJECT_OT_gnsk_select_objects(Operator):
    """Select objects that share a sculpt object with this GeoNode ShapeKey"""

    bl_idname = "object.geonode_shapekey_select_objects"
    bl_label = "Select Objects"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    gnsk_index: IntProperty(default=0)

    def execute(self, context):
        obj = context.object
        gnsk = obj.geonode_shapekeys[self.gnsk_index]

        count_hidden = 0
        count_selected = 0
        for target in gnsk.storage_object.geonode_shapekey_targets:
            target_ob = target.obj
            if target_ob.visible_get():
                target_ob.select_set(True)
                count_selected += 1
            else:
                count_hidden += 1

        if count_hidden > 0:
            self.report({'WARNING'}, f"{count_hidden} hidden objects were not selected.")
        else:
            self.report({'INFO'}, f"All {count_selected} objects were selected.")

        return {'FINISHED'}


class OBJECT_OT_gnsk_setup_uvs(Operator):
    """Ensure a set of non-overlapping UVs in a UVMap across all selected meshes"""

    bl_idname = "object.geonode_shapekey_ensure_uvmap"
    bl_label = "Ensure GNSK UVMap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_layers_bkp = {}

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            active_layers_bkp[obj] = obj.data.uv_layers.active.name
            if "GNSK" not in obj.data.uv_layers:
                obj.data.uv_layers.new(name="GNSK")
            obj.data.uv_layers.active = obj.data.uv_layers['GNSK']

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Restore active UV Layer
        for obj, layer in active_layers_bkp.items():
            obj.data.uv_layers.active = obj.data.uv_layers.get(layer)

        return {'FINISHED'}


registry = [
    OBJECT_OT_gnsk_add_shape,
    OBJECT_OT_gnsk_remove_shape,
    OBJECT_OT_gnsk_toggle_object,
    OBJECT_OT_gnsk_influence_slider,
    OBJECT_OT_gnsk_select_objects,
    OBJECT_OT_gnsk_setup_uvs,
]
