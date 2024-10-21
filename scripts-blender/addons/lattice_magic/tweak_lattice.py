# SPDX-License-Identifier: GPL-3.0-or-later

# Inspired by https://twitter.com/soyposmoderno/status/1307222594047758337

# This lets you create an empty hooked up to a Lattice to deform all selected 
# objects. A root empty is also created that can be (manually) parented to a 
# rig in order to use this for animation.

import bpy
from bpy.props import (
    FloatProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
    EnumProperty,
)
from bpy.types import (
    Operator,
    Object,
    Lattice,
    VertexGroup,
    Scene,
    Collection,
    Modifier,
    Panel,
    PropertyGroup,
)
from typing import List, Tuple

from mathutils import Matrix, Vector, kdtree
from math import *

from rna_prop_ui import rna_idprop_ui_create

from .utils import clamp, get_lattice_vertex_index, simple_driver, bounding_box_center_of_objects

TWEAKLAT_COLL_NAME = 'Tweak Lattices'

FALLOFF_TYPES = {
    # Since these expressions manipulate the shape of the lattice,
    # which then manipulates the shape of the mesh,
    # it's hard to come up with these functions in any meaningful way.
    # So, it was done more so with artistic trial and error.
    'LINEAR': lambda x: x + x * 0.1,
    'CONSTANT': lambda x: 1,
    'SHARP': lambda x: pow(x, 2) * 1.25,
    'ROOT': lambda x: pow(x, 0.5) * 1.05,
    'SMOOTH': lambda x: (1 - cos(x * pi)) / 2,
    'SPHERE': lambda x: sin(pow(x, 0.5)) * 1.25,
    'DONUT': lambda x: (sin(pow(x, 0.5)) - pow(x, 2)) * 2.5,
}


class OBJECT_OT_tweaklattice_create(Operator):
    """Create a lattice setup to deform selected objects"""

    bl_idname = "lattice.create_tweak_lattice"
    bl_label = "Create Tweak Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(
        name="Name",
        description="A unique name to identify this tweak lattice. Used in helper objects and modifiers",
        default="Tweak",
    )

    resolution: IntVectorProperty(name="Resolution", default=(25, 25, 25), min=6, max=64)

    location: EnumProperty(
        name="Location",
        items=[
            ('CURSOR', "3D Cursor", "Create at the location and orientation of the 3D cursor."),
            ('CENTER', "Center", "Create at the bounding box center of all selected objects."),
            ('PARENT', "Parent", "Create at the location of the parent object or bone."),
        ],
    )
    radius: FloatProperty(
        name="Radius",
        description="Radius of influence of this lattice. Can be changed later",
        default=0.1,
        min=0.0001,
        max=1000,
        soft_max=2,
    )

    parent_method: EnumProperty(
        name="Parent Method",
        description="How to parent the tweak lattice",
        items=[
            (
                'AUTO',
                'Automatic',
                "Parent using an Armature constraint which mimics the deformation of the nearest vertex to the cursor",
            ),
            (
                'MANUAL',
                'Manual',
                "Manually select a single object or bone as the tweak lattice parent",
            ),
        ],
        default='AUTO',
    )
    parent_bone: StringProperty(name="Bone", description="Bone to use as parent")

    @classmethod
    def poll(cls, context):
        for ob in context.selected_objects:
            if ob.type == 'MESH':
                return True
        
        cls.poll_message_set("No selected mesh objects.")
        return False

    def invoke(self, context, _event):
        parent_obj = context.object
        for m in parent_obj.modifiers:
            if m.type == 'ARMATURE' and m.object:
                parent_obj = m.object
                if self.parent_bone not in parent_obj.data.bones:
                    self.parent_bone = ""
                break

        context.scene.tweak_lattice_parent_ob = parent_obj

        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, 'name')
        layout.separator()

        layout.prop(self, 'location', expand=True)
        layout.prop(self, 'radius', slider=True)
        layout.separator()

        layout.prop(self, 'parent_method', expand=True)

        if self.parent_method == 'MANUAL':
            col = layout.column(align=True)
            col.prop(context.scene, 'tweak_lattice_parent_ob')

            scene = context.scene
            if scene.tweak_lattice_parent_ob and scene.tweak_lattice_parent_ob.type == 'ARMATURE':
                col.prop_search(self, 'parent_bone', scene.tweak_lattice_parent_ob.data, 'bones')

    def execute(self, context):
        scene = context.scene

        # Ensure a collection to organize all our objects in.
        coll = ensure_tweak_lattice_collection(context.scene)

        # Create a lattice object at the 3D cursor.
        lattice_name = f"LTC-{self.name}"
        lattice = bpy.data.lattices.new(lattice_name)
        lattice_ob = bpy.data.objects.new(lattice_name, lattice)
        coll.objects.link(lattice_ob)

        # Set resolution
        set_lattice_resolution(lattice_ob, *self.resolution)
        lattice_ob.hide_viewport = True

        # Create a falloff vertex group.
        vg = ensure_falloff_vgroup(lattice_ob, vg_name="Hook", func=FALLOFF_TYPES['SMOOTH'])

        # Create the Hook Empty.
        hook_name = "Hook_" + lattice_ob.name
        hook = bpy.data.objects.new(hook_name, None)
        hook.empty_display_type = 'SPHERE'
        hook.empty_display_size = 0.5
        coll.objects.link(hook)

        # Create some custom properties.
        hook['Lattice'] = lattice_ob
        lattice_ob['Hook'] = hook
        hook['Strength'] = 1.0

        rna_idprop_ui_create(
            hook,
            "Influence",
            default=1.0,
            min=0,
            max=1,
            description="Influence of this lattice on all of its target objects",
        )
        rna_idprop_ui_create(
            hook,
            "Radius",
            default=self.radius,
            min=0,
            soft_max=0.2,
            max=100,
            description="Size of the influenced area",
        )

        # Create a Root Empty to parent both the hook and the lattice to.
        # This will allow pressing Alt+G/R/S on the hook to reset its transforms.
        root_name = "Root_" + hook.name
        root = bpy.data.objects.new(root_name, None)
        root['Hook'] = hook
        root.empty_display_type = 'CUBE'
        root.empty_display_size = 0.5
        coll.objects.link(root)
        hook['Root'] = root

        self.set_parent_and_transform(context, root)

        # Disable the root from view.
        # NOTE: This must be done AFTER any reliance on view_layer.update() calls!
        #   They don't work when the object is disabled!
        root.hide_viewport = True

        # Parent lattice and hook to root.
        lattice_ob.parent = root
        hook.parent = root

        # Add Hook modifier to the lattice.
        hook_mod = lattice_ob.modifiers.new(name="Hook", type='HOOK')
        hook_mod.object = hook
        hook_mod.vertex_group = vg.name

        # Add Lattice modifier to the selected objects
        add_objects_to_lattice(hook, context.selected_objects)

        # Set up Radius control.
        add_radius_constraint(hook, hook, root)
        add_radius_constraint(lattice_ob, hook, root)

        root_drv = simple_driver(root, 'empty_display_size', hook, '["Radius"]')
        root_drv.expression = 'var/2'

        # Deselect everything, select the hook and make it active
        bpy.ops.object.select_all(action='DESELECT')
        hook.select_set(True)
        context.view_layer.objects.active = hook

        # Clear the parent selector helper property.
        scene.tweak_lattice_parent_ob = None
        return {'FINISHED'}

    def set_parent_and_transform(self, context, root):
        scene = context.scene
        depsgraph = context.evaluated_depsgraph_get()

        matrix_of_parent = self.get_lattice_parent_matrix(context)

        root.matrix_world = matrix_of_parent.copy()
        context.view_layer.update()
        mat_pre_arm_con = root.matrix_world.copy()

        if self.parent_method == 'AUTO':
            # Parent to the nearest deforming vertex.
            nearest_vertex = get_nearest_evaluated_vertex(
                dg=depsgraph,
                coord=matrix_of_parent.copy().to_translation(),
                objs=context.selected_objects,
            )
            obj, eval_obj, vert_idx, _vert_co = nearest_vertex

            root.parent = obj.find_armature() or obj
            weights = get_deforming_weights(obj, eval_obj, vert_idx)
        else:
            root.parent = scene.tweak_lattice_parent_ob
            weights = {}
            if self.parent_bone:
                weights = {self.parent_bone: 1.0}

        if weights:
            arm_con = root.constraints.new(type='ARMATURE')
            for bone_name, weight in weights.items():
                tgt = arm_con.targets.new()
                tgt.target = root.parent
                tgt.subtarget = bone_name
                tgt.weight = weight

            context.view_layer.update()
            mat_post_arm_con = root.matrix_world.copy()

            delta = mat_pre_arm_con.inverted() @ mat_post_arm_con

            root.matrix_world = matrix_of_parent @ delta.inverted()
        
        if self.parent_method != 'AUTO' or self.location != 'CURSOR':
            root.rotation_euler = 0, 0, 0

    def get_lattice_parent_matrix(self, context):
        location = self.location
        parent_bone = self.parent_bone
        scene = context.scene

        if location == 'CENTER':
            meshes = [o for o in context.selected_objects if o.type == 'MESH']
            mat = Matrix.Identity((4))
            mat.translation = bounding_box_center_of_objects(meshes)
            return mat
        elif location == 'CURSOR':
            return context.scene.cursor.matrix.copy()
        elif location == 'PARENT':
            ob_mat = scene.tweak_lattice_parent_ob.matrix_world
            if parent_bone:
                bone_mat = scene.tweak_lattice_parent_ob.pose.bones[parent_bone].matrix
                return ob_mat @ bone_mat
            else:
                return ob_mat


class OBJECT_OT_tweaklattice_duplicate(Operator):
    """Duplicate this Tweak Lattice set-up"""

    bl_idname = "lattice.duplicate_tweak_setup"
    bl_label = "Duplicate Tweak Lattice"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        hook, lattice, root = get_tweak_setup(context.object)
        bpy.ops.object.select_all(action='DESELECT')

        affected_objects = get_objects_of_lattice(hook)

        visibilities = {}
        for ob in [hook, lattice, root]:
            ob.hide_set(False)
            visibilities[ob] = ob.hide_viewport
            ob.hide_viewport = False
            if not ob.visible_get():
                self.report({'ERROR'}, f'Object "{ob.name}" could not be made visible, cancelling.')
                return {'CANCELLED'}
            ob.select_set(True)

        context.view_layer.objects.active = hook

        bpy.ops.object.duplicate()
        new_hook, new_lattice, new_root = get_tweak_setup(context.object)

        for key, value in list(new_hook.items()):
            if key.startswith("object_"):
                del new_hook[key]

        add_objects_to_lattice(new_hook, affected_objects)

        # Restore visibilities
        for ob, new_ob in zip((hook, lattice, root), (new_hook, new_lattice, new_root)):
            ob.hide_viewport = new_ob.hide_viewport = visibilities[ob]

        return {'FINISHED'}


class TweakLatticeProperties(PropertyGroup):
    def update_falloff(self, context):
        falloff_func = FALLOFF_TYPES[self.falloff_type]

        hook, lattice, _root = get_tweak_setup(context.active_object)
        ensure_falloff_vgroup(lattice, 'Hook', multiplier=self.strength, func=falloff_func)
        hook['Strength'] = self.strength

    strength: FloatProperty(
        name="Strength",
        description="A multiplier on the weight values",
        default=1,
        update=update_falloff,
        min=0,
        soft_max=2,
    )
    falloff_type: EnumProperty(
        name="Falloff Shape",
        description="Choose shape of influence for this lattice",
        items=[
            ('LINEAR', 'Linear', 'Linear'),
            ('CONSTANT', 'Constant', 'Constant'),
            ('SHARP', 'Sharp', 'Sharp'),
            ('ROOT', 'Root', 'Root'),
            ('SMOOTH', 'Smooth', 'Smooth'),
            ('SPHERE', 'Sphere', 'Sphere'),
            ('DONUT', 'Donut', 'Donut'),
        ],
        default='SMOOTH',
        update=update_falloff,
    )


class OBJECT_OT_tweaklattice_delete(Operator):
    """Delete a tweak lattice setup with all its helper objects, drivers, etc"""

    bl_idname = "lattice.delete_tweak_lattice"
    bl_label = "Delete Tweak Lattice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        hook, lattice, root = get_tweak_setup(context.object)
        if hook and lattice and root:
            return True

        cls.poll_message_set("Tweak Lattice set-up is incomplete. Some objects were manually deleted.")
        return False

    def execute(self, context):
        hook, lattice, root = get_tweak_setup(context.object)

        # Remove Lattice modifiers and their drivers.
        remove_all_objects_from_lattice(hook)

        # Remove hook Action if exists.
        if hook.animation_data and hook.animation_data.action:
            bpy.data.actions.remove(hook.animation_data.action)

        # Remove objects and Lattice datablock.
        bpy.data.objects.remove(hook)
        lattice_data = lattice.data
        bpy.data.objects.remove(lattice)
        bpy.data.lattices.remove(lattice_data)
        bpy.data.objects.remove(root)

        # Remove the collection if it's empty.
        coll = bpy.data.collections.get(TWEAKLAT_COLL_NAME)
        if coll and len(coll.all_objects) == 0:
            bpy.data.collections.remove(coll)

        return {'FINISHED'}


class OBJECT_OT_tweaklattice_objects_add(Operator):
    """Add selected objects to this tweak lattice"""

    bl_idname = "lattice.add_selected_objects"
    bl_label = "Add Selected Objects"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        hook, _lattice, _root = get_tweak_setup(context.object)
        if not hook:
            cls.poll_message_set("Cannot find hook object of this Tweak Lattice set-up. Perhaps it was deleted?")
            return False

        values = hook.values()
        for sel_o in context.selected_objects:
            if sel_o == hook or sel_o.type != 'MESH':
                continue
            if sel_o not in values:
                return True
        
        cls.poll_message_set("No selected objects to add to this Tweak Lattice.")
        return False

    def execute(self, context):
        hook, _lattice, _root = get_tweak_setup(context.object)

        # Add Lattice modifier to the selected objects
        add_objects_to_lattice(hook, context.selected_objects)

        return {'FINISHED'}


class OBJECT_OT_tweaklattice_objects_remove(Operator):
    """Remove selected objects from this tweak lattice"""

    bl_idname = "lattice.remove_selected_objects"
    bl_label = "Remove Selected Objects"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        hook, _lattice, _root = get_tweak_setup(context.object)
        if not hook:
            cls.poll_message_set("Cannot find hook object of this Tweak Lattice set-up. Perhaps it was deleted?")
            return False

        values = hook.values()
        for sel_o in context.selected_objects:
            if sel_o == hook or sel_o.type != 'MESH':
                continue
            if sel_o in values:
                return True
            
        cls.poll_message_set("No selected objects to remove from this Tweak Lattice.")
        return False

    def execute(self, context):
        hook, _lattice, _root = get_tweak_setup(context.object)

        # Add Lattice modifier to the selected objects
        remove_objects_from_lattice(hook, context.selected_objects)

        return {'FINISHED'}


class OBJECT_OT_tweaklattice_object_remove_single(Operator):
    """Remove this object from the tweak lattice"""

    bl_idname = "lattice.remove_object"
    bl_label = "Remove Object"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    ob_pointer_prop_name: StringProperty(
        description="Name of the custom property that references the object that should be removed"
    )

    def execute(self, context):
        hook, _lattice, _root = get_tweak_setup(context.object)
        target = hook[self.ob_pointer_prop_name]

        # Add Lattice modifier to the selected objects
        remove_objects_from_lattice(hook, [target])

        return {'FINISHED'}


class VIEW3D_PT_tweak_lattice(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Lattice Magic'
    bl_label = "Tweak Lattice"

    @classmethod
    def poll(cls, context):
        hook, _lattice, _root = get_tweak_setup(context.object)

        return context.object and context.object.type == 'MESH' or hook

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        hook, lattice, root = get_tweak_setup(context.object)

        layout = layout.column()
        if not hook:
            layout.operator(OBJECT_OT_tweaklattice_create.bl_idname, icon='OUTLINER_OB_LATTICE')
            return

        layout.prop(hook, '["Influence"]', slider=True, text="Influence")
        layout.prop(hook["Lattice"].data.lattice_magic, 'strength')
        layout.separator()

        layout.prop(hook["Lattice"].data.lattice_magic, 'falloff_type')
        layout.prop(hook, '["Radius"]', slider=True)

        layout.separator()
        layout.operator(
            OBJECT_OT_tweaklattice_delete.bl_idname, text='Delete Tweak Lattice', icon='TRASH'
        )
        layout.operator(
            OBJECT_OT_tweaklattice_duplicate.bl_idname,
            text='Duplicate Tweak Lattice',
            icon='DUPLICATE',
        )

        layout.separator()
        layout.label(text="Helper Objects")
        lattice_row = layout.row()
        lattice_row.prop(hook, '["Lattice"]', text="Lattice")
        lattice_row.prop(lattice, 'hide_viewport', text="", emboss=False)

        root_row = layout.row()
        root_row.prop(hook, '["Root"]', text="Root")
        root_row.prop(root, 'hide_viewport', text="", emboss=False)

        layout.separator()
        layout.label(text="Parenting")
        col = layout.column()
        col.enabled = False
        col.prop(root, 'parent')
        if root.parent and root.parent.type == 'ARMATURE':
            col.prop(root, 'parent_bone', icon='BONE_DATA')

        layout.separator()
        layout.label(text="Affected Objects")

        num_to_add = 0
        for o in context.selected_objects:
            if o == hook or o.type != 'MESH':
                continue
            if o in hook.values():
                continue
            num_to_add += 1
            if num_to_add == 1:
                text = f"Add {o.name}"
        if num_to_add:
            if num_to_add > 1:
                text = f"Add {num_to_add} Objects"
            layout.operator(OBJECT_OT_tweaklattice_objects_add.bl_idname, icon='ADD', text=text)

        layout.separator()
        num_to_remove = False
        for o in context.selected_objects:
            if o == hook or o.type != 'MESH':
                continue
            if o not in hook.values():
                continue
            num_to_remove += 1
            if num_to_remove == 1:
                text = f"Remove {o.name}"
        if num_to_remove:
            if num_to_remove > 1:
                text = f"Remove {num_to_remove} Objects"
            layout.operator(
                OBJECT_OT_tweaklattice_objects_remove.bl_idname, icon='REMOVE', text=text
            )

        objects_and_keys = [(hook[key], key) for key in hook.keys() if "object_" in key]
        objects_and_keys.sort(key=lambda o_and_k: o_and_k[1])
        for ob, key in objects_and_keys:
            row = layout.row(align=True)
            row.prop(hook, f'["{key}"]', text="")
            mod = get_lattice_modifier_of_object(ob, lattice)
            if not mod:
                continue
            row.prop_search(mod, 'vertex_group', ob, 'vertex_groups', text="", icon='GROUP_VERTEX')
            op = row.operator(
                OBJECT_OT_tweaklattice_object_remove_single.bl_idname, text="", icon='X'
            )
            op.ob_pointer_prop_name = key


def set_lattice_resolution(lat_ob: Object, res_u, res_v=None, res_w=None):
    assert lat_ob.type == 'LATTICE', f"This isn't a lattice object: {lat_ob.name}"

    if not res_v:
        res_v = res_u
    if not res_w:
        res_w = res_u

    lat_ob.data.points_u = res_u
    lat_ob.data.points_v = res_v
    lat_ob.data.points_w = res_w


def build_kdtree(obj):
    # Get the vertices of the mesh in world coordinates
    vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]

    # Build KD-Tree from the vertices
    size = len(vertices)
    kd = kdtree.KDTree(size)

    for i, vertex in enumerate(vertices):
        kd.insert(vertex, i)

    kd.balance()
    return kd


def get_nearest_evaluated_vertex(
    dg, coord: Vector, objs: list[Object]
) -> tuple[Object, int, Vector]:
    """Get nearest EVALUATED vertex to a coordinate out of a list of passed mesh objects.
    Return the original object, and the evaluated object, vertex index, and coordinate.
    """
    nearest_vertex = None
    nearest_distance = float('inf')

    for obj in objs:
        if obj.type != 'MESH':
            continue

        eval_ob = obj.evaluated_get(dg)

        kd = build_kdtree(eval_ob)

        # Find the nearest vertex to the 3D cursor

        eval_co, eval_idx, dist = kd.find(coord)

        # If this vertex is closer than any previously found, store it
        if dist < nearest_distance:
            nearest_distance = dist
            nearest_vertex = (obj, eval_ob, eval_idx, eval_co)

    return nearest_vertex


def get_deforming_weights(obj: Object, eval_obj, vert_idx: int) -> dict[str, float] | None:
    armature = obj.find_armature()

    if not armature:
        return

    vertex = eval_obj.data.vertices[vert_idx]

    weights = {}

    # Loop through the vertex groups the vertex belongs to
    for group in vertex.groups:
        group_index = group.group
        group_weight = group.weight
        group_name = obj.vertex_groups[group_index].name
        pbone = armature.pose.bones.get(group_name)
        if pbone and pbone.bone.use_deform:
            weights[group_name] = group_weight

    return weights


def get_tweak_setup(obj: Object) -> Tuple[Object, Object, Object]:
    """Based on either the hook, lattice or root, return all three."""
    if not obj:
        return [None, None, None]

    if obj.type == 'EMPTY':
        if 'Root' and 'Lattice' in obj:
            return obj, obj['Lattice'], obj['Root']
        elif 'Hook' in obj:
            return obj['Hook'], obj['Hook']['Lattice'], obj
    elif obj.type == 'LATTICE' and 'Hook' in obj:
        return obj['Hook'], obj, obj['Hook']['Root']

    return [None, None, None]


def ensure_tweak_lattice_collection(scene: Scene) -> Collection:
    coll = bpy.data.collections.get(TWEAKLAT_COLL_NAME)
    if not coll:
        coll = bpy.data.collections.new(TWEAKLAT_COLL_NAME)
        scene.collection.children.link(coll)

    return coll


def ensure_falloff_vgroup(
    lattice_ob: Object, vg_name="Group", multiplier=1, func=lambda x: x
) -> VertexGroup:
    lattice = lattice_ob.data
    res_x, res_y, res_z = lattice.points_u, lattice.points_v, lattice.points_w

    vg = lattice_ob.vertex_groups.get(vg_name)

    center = Vector((res_x - 1, res_y - 1, res_z - 1)) / 2
    max_res = max(res_x, res_y, res_z)

    if not vg:
        vg = lattice_ob.vertex_groups.new(name=vg_name)
    for x in range(res_x - 4):
        for y in range(res_y - 4):
            for z in range(res_z - 4):
                index = get_lattice_vertex_index(lattice, (x + 2, y + 2, z + 2))

                coord = Vector((x + 2, y + 2, z + 2))
                distance_from_center = (coord - center).length
                distance_factor = clamp(1 - (distance_from_center / max_res * 2), 0, 1)
                influence = func(distance_factor)

                vg.add([index], influence * multiplier, 'REPLACE')
    return vg


def add_radius_constraint(obj, hook, target):
    trans_con = obj.constraints.new(type='TRANSFORM')
    trans_con.name += " (Radius Scaling)"
    trans_con.target = target
    trans_con.map_to = 'SCALE'
    trans_con.mix_mode_scale = 'MULTIPLY'
    for prop in ['to_min_x_scale', 'to_min_y_scale', 'to_min_z_scale']:
        simple_driver(trans_con, prop, hook, '["Radius"]')
    return trans_con


def get_objects_of_lattice(hook: Object) -> List[Object]:
    objs = []
    for key, value in hook.items():
        if key.startswith("object_") and value:
            objs.append(value)

    return objs


def get_lattice_modifier_of_object(obj, lattice) -> Modifier:
    """Find the lattice modifier on the object that uses this lattice"""
    if not obj:
        return
    for m in obj.modifiers:
        if m.type == 'LATTICE' and m.object == lattice:
            return m


def add_objects_to_lattice(hook: Object, objects: List[Object]):
    lattice_ob = hook['Lattice']

    for i, obj in enumerate(objects):
        obj.select_set(False)
        if obj.type != 'MESH' or obj in hook.values():
            continue

        # Make sure overridden object is editable.
        if obj.override_library:
            obj.override_library.is_system_override = False

        mod = obj.modifiers.new(name=lattice_ob.name, type='LATTICE')
        mod.object = lattice_ob

        # Make sure the property name is available.
        offset = 0
        while "object_" + str(offset) in hook:
            offset += 1
        hook["object_" + str(i + offset)] = obj

        # Add driver to the modifier influence.
        simple_driver(mod, 'strength', hook, '["Influence"]')


def remove_object_from_lattice(hook: Object, obj: Object):
    """Cleanly remove an object from a Tweak Lattice set-up's influence."""
    hook, lattice, root = get_tweak_setup(hook)

    # Remove the custom property pointing from the Hook to the Object.
    for key, value in list(hook.items()):
        if value == obj:
            del hook[key]
            break

    # Remove the Lattice modifier (and its driver) deforming the Object.
    for m in obj.modifiers:
        if m.type != 'LATTICE':
            continue
        if m.object == lattice:
            m.driver_remove('strength')
            obj.modifiers.remove(m)
            break


def remove_objects_from_lattice(hook: Object, objects_to_remove: List[Object]) -> List[Object]:
    """Cleanly remove several objects from a Tweak Lattice set-up's influence."""
    objs_removed = []
    for key, value in list(hook.items()):
        if value in objects_to_remove:
            remove_object_from_lattice(hook, value)
            objs_removed.append(value)

    return objs_removed


def remove_all_objects_from_lattice(hook: Object) -> List[Object]:
    """Cleanly remove all objects from a Tweak Lattice set-up's influence."""
    objs_to_remove = []
    for key, value in list(hook.items()):
        if key.startswith("object_"):
            objs_to_remove.append(value)

    return remove_objects_from_lattice(hook, objs_to_remove)


registry = [
    OBJECT_OT_tweaklattice_create,
    OBJECT_OT_tweaklattice_duplicate,
    OBJECT_OT_tweaklattice_delete,
    OBJECT_OT_tweaklattice_objects_add,
    OBJECT_OT_tweaklattice_objects_remove,
    OBJECT_OT_tweaklattice_object_remove_single,
    VIEW3D_PT_tweak_lattice,
    TweakLatticeProperties,
]


def register():
    Scene.tweak_lattice_parent_ob = PointerProperty(type=Object, name="Parent")
    Lattice.lattice_magic = PointerProperty(type=TweakLatticeProperties)


def unregister():
    del Scene.tweak_lattice_parent_ob
    del Lattice.lattice_magic
