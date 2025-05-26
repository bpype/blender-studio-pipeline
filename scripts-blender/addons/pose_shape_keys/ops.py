# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, re
from bpy.types import Object, Operator
from bpy.props import StringProperty, BoolProperty
from mathutils import Vector, Quaternion
from math import sqrt
from collections import OrderedDict

from .symmetrize_shape_key import mirror_mesh
from .prefs import get_addon_prefs
from .ui_list import UILIST_OT_Entry_Add, UILIST_OT_Entry_Remove
from .naming import side_is_left

# When saving or pushing shapes, disable any modifier NOT in this list.
DEFORM_MODIFIERS = [
    'ARMATURE',
    'CAST',
    'CURVE',
    'DISPLACE',
    'HOOK',
    'LAPLACIANDEFORM',
    'LATTICE',
    'MESH_DEFORM',
    'SHRINKWRAP',
    'SIMPLE_DEFORM',
    'SMOOTH',
    'CORRECTIVE_SMOOTH',
    'LAPLACIANSMOOTH',
    'SURFACE_DEFORM',
    'WARP',
    'WAVE',
]
GOOD_MODIFIERS = ['ARMATURE']


class OBJECT_OT_pose_key_add(UILIST_OT_Entry_Add, Operator):
    """Add Pose Shape Key"""

    bl_idname = "object.posekey_add"
    bl_label = "Add Pose Shape Key"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}
    bl_property = "pose_key_name"  # Focus the text input box

    list_context_path: StringProperty()
    active_idx_context_path: StringProperty()

    pose_key_name: StringProperty(name="Name", default="Pose Key")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout.column()
        layout.use_property_split = True

        layout.prop(self, 'pose_key_name')
        if self.pose_key_name.strip() == "":
            layout.alert = True
            layout.label(text="Name cannot be empty.", icon='ERROR')

    def execute(self, context):
        if self.pose_key_name.strip() == "":
            self.report({'ERROR'}, "Must specify a name.")
            return {'CANCELLED'}

        my_list = self.get_list(context)
        active_index = self.get_active_index(context)

        to_index = active_index + 1
        if len(my_list) == 0:
            to_index = 0

        psk = my_list.add()
        psk.name = self.pose_key_name
        my_list.move(len(my_list) - 1, to_index)
        self.set_active_index(context, to_index)

        return {'FINISHED'}


class OBJECT_OT_pose_key_auto_init(Operator):
    """Assign the current Action and scene frame number to this pose key"""

    bl_idname = "object.posekey_auto_init"
    bl_label = "Initialize From Context"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        arm_ob = get_deforming_armature(obj)
        if not arm_ob:
            cls.poll_message_set("No deforming armature.")
            return False
        if not (arm_ob.animation_data and arm_ob.animation_data.action):
            cls.poll_message_set("Armature has no Action assigned.")
            return False
        obj = context.object
        pose_key = get_active_pose_key(obj)
        if (
            pose_key.action == arm_ob.animation_data.action
            and pose_key.frame == context.scene.frame_current
        ):
            cls.poll_message_set("Action and frame number are already set.")
            return False
        return True

    def execute(self, context):
        # Set action and frame number to the current ones.
        obj = context.object
        pose_key = get_active_pose_key(obj)
        arm_ob = get_deforming_armature(obj)
        pose_key.action = arm_ob.animation_data.action
        pose_key.frame = context.scene.frame_current
        self.report({'INFO'}, "Initialized Pose Key data.")
        return {'FINISHED'}


class OBJECT_OT_pose_key_set_pose(Operator):
    """Reset the rig, then set the above Action and frame number"""

    bl_idname = "object.posekey_set_pose"
    bl_label = "Set Pose"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return poll_correct_pose_key_pose(cls, context, demand_pose=False)

    def execute(self, context):
        set_pose_of_active_pose_key(context)
        return {'FINISHED'}


class SaveAndRestoreState:
    def disable_non_deform_modifiers(self, storage_ob: Object, rigged_ob: Object):
        # Disable non-deforming modifiers
        self.disabled_mods_storage = []
        self.disabled_mods_rigged = []
        self.disabled_fcurves = []
        for obj, lst in zip(
            [storage_ob, rigged_ob], [self.disabled_mods_storage, self.disabled_mods_rigged]
        ):
            if not obj:
                continue
            for mod in obj.modifiers:
                if mod.type not in GOOD_MODIFIERS and mod.show_viewport:
                    lst.append(mod.name)
                    mod.show_viewport = False
                    if mod.show_viewport:
                        data_path = f'modifiers["{mod.name}"].show_viewport'
                        fc = obj.animation_data.drivers.find(data_path)
                        if fc:
                            fc.mute = True
                            self.disabled_fcurves.append(data_path)
                            mod.show_viewport = False

    def restore_non_deform_modifiers(self, storage_ob: Object, rigged_ob: Object):
        # Re-enable non-deforming modifiers
        for obj, mod_list in zip(
            [storage_ob, rigged_ob], [self.disabled_mods_storage, self.disabled_mods_rigged]
        ):
            if not obj:
                continue
            for mod_namee in mod_list:
                obj.modifiers[mod_namee].show_viewport = True
        for data_path in self.disabled_fcurves:
            fc = obj.animation_data.drivers.find(data_path)
            if fc:
                fc.mute = False

    def save_state(self, context):
        rigged_ob = context.object

        pose_key = rigged_ob.data.pose_keys[rigged_ob.data.active_pose_key_index]
        storage_ob = pose_key.storage_object

        # Non-Deforming modifiers
        self.disable_non_deform_modifiers(storage_ob, rigged_ob)

        # Active Shape Key Index
        self.orig_sk_index = rigged_ob.active_shape_key_index
        rigged_ob.active_shape_key_index = 0

        # Shape Keys
        self.org_sk_toggles = {}
        for target_shape in pose_key.target_shapes:
            key_block = target_shape.key_block
            if not key_block:
                self.report({'ERROR'}, f"Shape key not found: {key_block.name}")
                return {'CANCELLED'}
            self.org_sk_toggles[key_block.name] = key_block.mute
            key_block.mute = True

    def restore_state(self, context):
        rigged_ob = context.object
        pose_key = rigged_ob.data.pose_keys[rigged_ob.data.active_pose_key_index]
        storage_ob = pose_key.storage_object
        self.restore_non_deform_modifiers(storage_ob, rigged_ob)

        rigged_ob.active_shape_key_index = self.orig_sk_index
        for kb_name, kb_value in self.org_sk_toggles.items():
            rigged_ob.data.shape_keys.key_blocks[kb_name].mute = kb_value


class OperatorWithWarning:
    def invoke(self, context, event):
        addon_prefs = get_addon_prefs(context)
        if addon_prefs.no_warning:
            return self.execute(context)

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout.column(align=True)

        warning = self.get_warning_text(context)
        for line in warning.split("\n"):
            row = layout.row()
            row.alert = True
            row.label(text=line)

        addon_prefs = get_addon_prefs(context)
        col = layout.column(align=True)
        col.prop(addon_prefs, 'no_warning', text="Disable Warnings (Can be reset in Preferences)")

    def get_warning_text(self, context):
        raise NotImplemented


class OBJECT_OT_pose_key_save(Operator, OperatorWithWarning, SaveAndRestoreState):
    """Save the deformed mesh vertex positions of the current pose into the Storage Object"""

    bl_idname = "object.posekey_save"
    bl_label = "Overwrite Storage Object"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return poll_correct_pose_key_pose(cls, context)

    def invoke(self, context, event):
        obj = context.object
        pose_key = get_active_pose_key(obj)
        if pose_key.storage_object:
            return super().invoke(context, event)
        return self.execute(context)

    def get_warning_text(self, context):
        obj = context.object
        pose_key = get_active_pose_key(obj)
        return f'Overwrite storage object "{pose_key.storage_object.name}"?'

    def execute(self, context):
        rigged_ob = context.object

        pose_key = rigged_ob.data.pose_keys[rigged_ob.data.active_pose_key_index]
        storage_ob = pose_key.storage_object
        already_existed = storage_ob != None
        self.disable_non_deform_modifiers(storage_ob, rigged_ob)

        depsgraph = context.evaluated_depsgraph_get()
        rigged_ob_eval = rigged_ob.evaluated_get(depsgraph)
        rigged_ob_eval_mesh = rigged_ob_eval.data

        storage_ob_name = rigged_ob.name + "-" + pose_key.name
        storage_ob_mesh = bpy.data.meshes.new_from_object(rigged_ob)
        storage_ob_mesh.name = storage_ob_name

        if not already_existed:
            storage_ob = bpy.data.objects.new(storage_ob_name, storage_ob_mesh)
            context.scene.collection.objects.link(storage_ob)
            pose_key.storage_object = storage_ob
            storage_ob.location = rigged_ob.location
            storage_ob.location.x -= rigged_ob.dimensions.x * 1.1
        else:
            old_mesh = storage_ob.data
            storage_ob.data = storage_ob_mesh
            bpy.data.meshes.remove(old_mesh)

        if len(storage_ob.data.vertices) != len(rigged_ob.data.vertices):
            self.report(
                {'WARNING'},
                f'Vertex Count did not match between storage object {storage_ob.name}({len(storage_ob.data.vertices)}) and current ({len(rigged_ob.data.vertices)})!',
            )
            storage_ob_mesh = bpy.data.meshes.new_from_object(rigged_ob_eval)
            storage_ob.data = storage_ob_mesh
            storage_ob.data.name = storage_ob_name

        storage_ob.use_shape_key_edit_mode = True
        storage_ob.shape_key_add(name="Basis")
        target = storage_ob.shape_key_add(name="Morph Target")
        adjust = storage_ob.shape_key_add(name="New Changes", from_mix=True)
        target.value = 1
        adjust.value = 1
        storage_ob.active_shape_key_index = 2

        # Fix material assignments in case any material slots are linked to the
        # object instead of the mesh.
        for i, ms in enumerate(rigged_ob.material_slots):
            if ms.link == 'OBJECT':
                storage_ob.material_slots[i].link = 'OBJECT'
                storage_ob.material_slots[i].material = ms.material

        # Set the target shape to be the evaluated mesh.
        for target_v, eval_v in zip(target.data, rigged_ob_eval_mesh.vertices):
            target_v.co = eval_v.co

        # Copy some symmetry settings from the original
        storage_ob.data.use_mirror_x = rigged_ob.data.use_mirror_x

        # Nuke vertex groups, since we don't need them.
        storage_ob.vertex_groups.clear()

        self.restore_non_deform_modifiers(storage_ob, rigged_ob)

        # If new shape is visible and it already existed, set it as active.
        if already_existed and storage_ob.visible_get():
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = storage_ob
            storage_ob.select_set(True)

        self.report({'INFO'}, f'The deformed mesh has been stored in "{storage_ob.name}".')
        return {'FINISHED'}


class OBJECT_OT_pose_key_push(Operator, OperatorWithWarning, SaveAndRestoreState):
    """Let the below shape keys blend the current deformed shape into the shape of the Storage Object"""

    bl_idname = "object.posekey_push"
    bl_label = "Load Vertex Position Data into Shape Keys"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if not poll_correct_pose_key_pose(cls, context):
            return False

        # No shape keys to push into.
        obj = context.object
        pose_key = get_active_pose_key(obj)
        for target_shape in pose_key.target_shapes:
            if target_shape.key_block:
                return True

        cls.poll_message_set(
            "This Pose Key doesn't have any target shape keys to push into. Add some in the Shape Key Slots list below."
        )
        return False

    def get_warning_text(self, context):
        obj = context.object
        pose_key = get_active_pose_key(obj)
        target_shape_names = [target.name for target in pose_key.target_shapes if target]
        return (
            "This will overwrite the following Shape Keys: \n    "
            + "\n    ".join(target_shape_names)
            + "\n Are you sure?"
        )

    def execute(self, context):
        """
        Load the active PoseShapeKey's mesh data into its corresponding shape key,
        such that the shape key will blend from whatever state the mesh is currently in,
        into the shape stored in the PoseShapeKey.
        """

        self.save_state(context)

        try:
            self.push_active_pose_key(context, set_pose=False)
        except:
            return {'CANCELLED'}

        self.restore_state(context)

        return {'FINISHED'}

    def push_active_pose_key(self, context, set_pose=False):
        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene

        rigged_ob = context.object

        pose_key = rigged_ob.data.pose_keys[rigged_ob.data.active_pose_key_index]

        storage_object = pose_key.storage_object
        if storage_object.name not in context.view_layer.objects:
            self.report({'ERROR'}, f'Storage object "{storage_object.name}" must be in view layer!')
            raise Exception

        if set_pose:
            set_pose_of_active_pose_key(context)

        # The Pose Key stores the vertex positions of a previous evaluated mesh.
        # This, and the current vertex positions of the mesh are subtracted
        # from each other to get the difference in their shape.
        storage_eval_verts = pose_key.storage_object.evaluated_get(depsgraph).data.vertices
        rigged_eval_verts = rigged_ob.evaluated_get(depsgraph).data.vertices

        # Shape keys are relative to the base shape of the mesh, so that delta
        # will be added to the base mesh to get the final shape key vertex positions.
        rigged_base_verts = rigged_ob.data.vertices

        # The CrazySpace provides us the matrix by which each vertex has been
        # deformed by modifiers and shape keys. This matrix is necessary to
        # calculate the correct delta.
        rigged_ob.crazyspace_eval(depsgraph, scene)

        for i, v in enumerate(storage_eval_verts):
            if i > len(rigged_base_verts) - 1:
                break
            storage_eval_co = Vector(v.co)
            rigged_eval_co = rigged_eval_verts[i].co

            delta = storage_eval_co - rigged_eval_co

            delta = rigged_ob.crazyspace_displacement_to_original(
                vertex_index=i, displacement=delta
            )

            base_v = rigged_base_verts[i].co
            for target_shape in pose_key.target_shapes:
                key_block = target_shape.key_block
                if not key_block:
                    continue
                key_block.data[i].co = base_v + delta

        # Mirror shapes if needed
        for target_shape in pose_key.target_shapes:
            if target_shape.mirror_x:
                key_block = target_shape.key_block
                if not key_block:
                    continue
                mirror_mesh(
                    reference_verts=rigged_ob.data.vertices,
                    vertices=key_block.data,
                    axis='X',
                    symmetrize=False,
                )

        rigged_ob.crazyspace_eval_clear()

        if len(storage_eval_verts) != len(rigged_eval_verts):
            self.report(
                {'WARNING'},
                f'Mismatching topology: Stored shape "{pose_key.storage_object.name}" had {len(storage_eval_verts)} vertices instead of {len(rigged_eval_verts)}',
            )


class OBJECT_OT_pose_key_push_all(Operator, OperatorWithWarning, SaveAndRestoreState):
    """Go through all Pose Keys, set their pose and overwrite the shape keys to match the storage object shapes"""

    bl_idname = "object.posekey_push_all"
    bl_label = "Push ALL Pose Keys into Shape Keys"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            cls.poll_message_set("No active mesh object.")
            return False
        if len(obj.data.pose_keys) == 0:
            cls.poll_message_set("No Pose Shape Keys to push.")
            return False
        return True

    def get_warning_text(self, context):
        obj = context.object
        target_shape_names = []
        for pk in obj.data.pose_keys:
            target_shape_names.extend([t.name for t in pk.target_shapes if t])
        return (
            "This will overwrite the following Shape Keys: \n    "
            + "\n    ".join(target_shape_names)
            + "\n Are you sure?"
        )

    def execute(self, context):
        rigged_ob = context.object
        for i, pk in enumerate(rigged_ob.data.pose_keys):
            rigged_ob.data.active_pose_key_index = i
            bpy.ops.object.posekey_set_pose()
            bpy.ops.object.posekey_push()

        return {'FINISHED'}


class OBJECT_OT_pose_key_clamp_influence(Operator):
    """Clamp the influence of this pose key's shape keys to 1.0 for each vertex, by normalizing the vertex weight mask values of vertices where the total influence is greater than 1"""

    bl_idname = "object.posekey_clamp_influence"
    bl_label = "Clamp Vertex Influences"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @staticmethod
    def get_affected_vertex_group_names(object: Object) -> list[str]:
        pose_key = object.data.pose_keys[object.data.active_pose_key_index]

        vg_names = []
        for target_shape in pose_key.target_shapes:
            kb = target_shape.key_block
            if not kb:
                continue
            if kb.vertex_group and kb.vertex_group in object.vertex_groups:
                vg_names.append(kb.vertex_group)

        return vg_names

    @classmethod
    def poll(cls, context):
        if not cls.get_affected_vertex_group_names(context.object):
            cls.poll_message_set(
                "No shape keys of this pose shape key use vertex masks. There is nothing to clamp."
            )
            return False
        return True

    def normalize_vgroups(self, obj, vgroups):
        """Normalize a set of vertex groups in isolation"""
        """ Used for creating mask vertex groups for splitting shape keys """
        for vert in obj.data.vertices:
            # Find sum of weights in specified vgroups
            # set weight to original/sum
            sum_weights = 0
            for vgroup in vgroups:
                try:
                    sum_weights += vgroup.weight(vert.index)
                except:
                    pass
            for vgroup in vgroups:
                if sum_weights > 1.0:
                    try:
                        vgroup.add([vert.index], vgroup.weight(vert.index) / sum_weights, 'REPLACE')
                    except:
                        pass

    def execute(self, context):
        obj = context.object
        vg_names = self.get_affected_vertex_group_names(obj)
        self.normalize_vgroups(obj, [obj.vertex_groups[vg_name] for vg_name in vg_names])
        return {'FINISHED'}


class OBJECT_OT_pose_key_place_objects_in_grid(Operator):
    """Place the storage objects in a grid above this object"""

    bl_idname = "object.posekey_object_grid"
    bl_label = "Place ALL Storage Objects in a Grid"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @staticmethod
    def get_storage_objects(context) -> list[Object]:
        obj = context.object
        pose_keys = obj.data.pose_keys
        return [pk.storage_object for pk in pose_keys if pk.storage_object]

    @classmethod
    def poll(cls, context):
        """Only available if there are any storage objects in any of the pose keys."""
        if not cls.get_storage_objects(context):
            cls.poll_message_set(
                "This pose key has no storage objects, so there is nothing to sort into a grid."
            )
            return False
        return True

    @staticmethod
    def place_objects_in_grid(context, objs: list[Object]):
        if not objs:
            return
        x = max([obj.dimensions.x for obj in objs])
        y = max([obj.dimensions.y for obj in objs])
        z = max([obj.dimensions.z for obj in objs])
        scalar = 1.2
        dimensions = Vector((x * scalar, y * scalar, z * scalar))

        grid_rows = round(sqrt(len(objs)))
        for i, obj in enumerate(objs):
            col_i = (i % grid_rows) - int(grid_rows / 2)
            row_i = int(i / grid_rows) + scalar
            offset = Vector((col_i * dimensions.x, 0, row_i * dimensions.z))
            obj.location = context.object.location + offset

    def execute(self, context):
        storage_objects = self.get_storage_objects(context)
        self.place_objects_in_grid(context, storage_objects)

        return {'FINISHED'}


class OBJECT_OT_pose_key_jump_to_storage(Operator):
    """Place the storage object next to this object and select it"""

    bl_idname = "object.posekey_jump_to_storage"
    bl_label = "Jump To Storage Object"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @staticmethod
    def get_storage_object(context):
        obj = context.object
        pose_key = get_active_pose_key(obj)
        return pose_key.storage_object

    @classmethod
    def poll(cls, context):
        """Only available if there is a storage object in the pose key."""
        if not cls.get_storage_object(context):
            cls.poll_message_set("This pose key doesn't have a storage object to jump to.")
            return False
        return True

    def execute(self, context):
        storage_object = self.get_storage_object(context)

        storage_object.location = context.object.location
        storage_object.location.x -= context.object.dimensions.x * 1.1

        if storage_object.name not in context.view_layer.objects:
            self.report({'ERROR'}, "Storage object must be in view layer.")
            return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        storage_object.select_set(True)
        storage_object.hide_set(False)
        context.view_layer.objects.active = storage_object

        # Put the other storage objects in a grid
        prefs = get_addon_prefs(context)
        if prefs.grid_objects_on_jump:
            storage_objects = OBJECT_OT_pose_key_place_objects_in_grid.get_storage_objects(context)
            storage_objects.remove(storage_object)
            OBJECT_OT_pose_key_place_objects_in_grid.place_objects_in_grid(context, storage_objects)

        return {'FINISHED'}


class OBJECT_OT_pose_key_copy_data(Operator):
    """Copy Pose Key data from active object to selected ones"""

    bl_idname = "object.posekey_copy_data"
    bl_label = "Copy Pose Key Data"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Only available if there is a selected mesh and the active mesh has pose key data."""
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if len(selected_meshes) < 2:
            cls.poll_message_set("No other meshes are selected to copy pose key data to.")
            return False
        if context.object.type != 'MESH' or not context.object.data.pose_keys:
            cls.poll_message_set("No active mesh object with pose keys to copy.")
            return False
        return True

    def execute(self, context):
        source_ob = context.object
        targets = [
            obj for obj in context.selected_objects if obj.type == 'MESH' and obj != source_ob
        ]

        for target_ob in targets:
            target_ob.data.pose_keys.clear()

            for src_pk in source_ob.data.pose_keys:
                new_pk = target_ob.data.pose_keys.add()
                new_pk.name = src_pk.name
                new_pk.action = src_pk.action
                new_pk.frame = src_pk.frame
                new_pk.storage_object = src_pk.storage_object
                for src_sk_slot in src_pk.target_shapes:
                    new_sk_slot = new_pk.target_shapes.add()
                    new_sk_slot.name = src_sk_slot.name
                    new_sk_slot.mirror_x = src_sk_slot.mirror_x

        return {'FINISHED'}


class OBJECT_OT_pose_key_shape_add(UILIST_OT_Entry_Add, Operator):
    """Add Target Shape Key"""

    bl_idname = "object.posekey_shape_add"
    bl_label = "Add Target Shape Key"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    list_context_path: StringProperty()
    active_idx_context_path: StringProperty()

    def update_sk_name(self, context):
        def set_vg(vg_name):
            obj = context.object
            vg = obj.vertex_groups.get(vg_name)
            if vg:
                self.vg_name = vg.name
                return vg

        vg = set_vg(self.sk_name)
        if not vg and self.sk_name.endswith(".L"):
            vg = set_vg("Side.L")
        if not vg and self.sk_name.endswith(".R"):
            vg = set_vg("Side.R")

    sk_name: StringProperty(
        name="Name",
        description="Name to set for the new shape key",
        default="Key",
        update=update_sk_name,
    )
    def update_create_sk(self, context):
        obj = context.object
        if not self.create_sk and not obj.data.shape_keys:
            # If there are no shape keys, force enable creation of new shape key.
            self.create_sk = True
            return
        pose_key = get_active_pose_key(obj)
        if self.create_sk:
            self.sk_name = pose_key.name
        elif self.sk_name not in context.object.data.shape_keys.key_blocks:
            self.sk_name = ""

    create_sk: BoolProperty(
        name="Create New Shape Key",
        description="Create a new blank Shape Key to push this pose into, instead of using an existing one",
        default=True,
        update=update_create_sk
    )
    vg_name: StringProperty(
        name="Vertex Group",
        description="Vertex Group to assign as the masking group of this shape key",
        default="",
    )

    def update_create_vg(self, context):
        if self.create_vg:
            self.vg_name = self.sk_name
        elif self.vg_name not in context.object.vertex_groups:
            self.vg_name = ""

    create_vg: BoolProperty(
        name="Create New Vertex Group",
        description="Create a new blank Vertex Group as a mask for this shape key, as opposed to using an existing vertex group for masking",
        default=False,
        update=update_create_vg,
    )

    create_slot: BoolProperty(
        name="Create New Slot",
        description="Internal. Whether to assign the chosen (or created) shape key to the current slot, or to create a new one",
        default=True,
    )

    def invoke(self, context, event):
        obj = context.object
        if obj.data.shape_keys:
            self.sk_name = f"Key {len(obj.data.shape_keys.key_blocks)}"
        else:
            self.sk_name = "Key"
            self.create_sk = True

        pose_key = get_active_pose_key(obj)
        if pose_key.name:
            self.sk_name = pose_key.name
        if not self.create_slot and pose_key.active_target:
            self.sk_name = pose_key.active_target.name

        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        layout = self.layout.column()
        layout.use_property_split = True

        obj = context.object

        row = layout.row(align=True)
        if self.create_sk:
            row.prop(self, 'sk_name', icon='SHAPEKEY_DATA')
        else:
            row.prop_search(
                self, 'sk_name', obj.data.shape_keys, 'key_blocks', icon='SHAPEKEY_DATA'
            )

        if obj.data.shape_keys:
            # We don't want to draw this option if there are no shape keys. (Since it would have to be True.)
            row.prop(self, 'create_sk', text="", icon='ADD')

        if (self.create_sk and self.sk_name) or obj.data.shape_keys.key_blocks.get(self.sk_name):
            row = layout.row(align=True)
            if self.create_vg:
                if obj.vertex_groups.get(self.vg_name):
                    row.alert = True
                    layout.label(
                        text="Cannot create that vertex group because it already exists!", icon='ERROR'
                    )
                row.prop(self, 'vg_name', icon='GROUP_VERTEX')
            else:
                row.prop_search(self, 'vg_name', obj, "vertex_groups")

            row.prop(self, 'create_vg', text="", icon='ADD')

    def execute(self, context):
        if self.sk_name.strip() == "":
            self.report({'ERROR'}, "Must provide shape key name.")
            return {'CANCELLED'}
        obj = context.object

        if self.create_vg and obj.vertex_groups.get(self.vg_name):
            self.report({'ERROR'}, f"Vertex group '{self.vg_name}' already exists!")
            return {'CANCELLED'}

        # Ensure Basis shape key
        if not obj.data.shape_keys:
            basis = obj.shape_key_add()
            basis.name = "Basis"
            obj.data.update()

        if self.create_sk:
            # Add new shape key.
            key_block = obj.shape_key_add()
            key_block.name = self.sk_name
            key_block.value = 1
        else:
            key_block = obj.data.shape_keys.key_blocks.get(self.sk_name)

        if key_block:
            if self.create_vg:
                obj.vertex_groups.new(name=self.vg_name)

            if self.vg_name:
                key_block.vertex_group = self.vg_name

            pose_key = get_active_pose_key(obj)

        if self.create_slot:
            super().execute(context)

        if key_block:
            target_slot = pose_key.active_target
            target_slot.name = key_block.name
            self.report({'INFO'}, f"Added shape key {key_block.name}.")
        else:
            self.report({'ERROR'}, "Failed to add shape key.")

        return {'FINISHED'}


class OBJECT_OT_pose_key_shape_remove(UILIST_OT_Entry_Remove, OperatorWithWarning, Operator):
    """Remove Target Shape Key. Hold Shift to only remove the slot and keep the actual shape key"""

    bl_idname = "object.posekey_shape_remove"
    bl_label = "Remove Target Shape Key"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    list_context_path: StringProperty()
    active_idx_context_path: StringProperty()

    delete_sk: BoolProperty(
        name="Delete Shape Key",
        description="Delete the underlying Shape Key",
        default=True,
    )

    def get_key_block(self, context):
        obj = context.object
        pose_key = get_active_pose_key(obj)
        target_slot = pose_key.active_target
        return target_slot.key_block

    def invoke(self, context, event):
        if self.get_key_block(context):
            # If this actually targets a shape key, prompt for removal.
            self.delete_sk = not event.shift
            if self.delete_sk:
                return super().invoke(context, event)
        return self.execute(context)

    def get_warning_text(self, context):
        return "Delete this Shape Key?"

    @staticmethod
    def delete_shapekey_with_drivers(obj, key_block):
        shape_key = key_block.id_data
        if shape_key.animation_data:
            for fcurve in shape_key.animation_data.drivers:
                if fcurve.data_path.startswith(f'key_blocks["{key_block.name}"]'):
                    shape_key.animation_data.drivers.remove(fcurve)
        obj.shape_key_remove(key_block)

    def execute(self, context):
        obj = context.object

        key_block = self.get_key_block(context)
        if key_block and self.delete_sk:
            self.delete_shapekey_with_drivers(obj, key_block)

        super().execute(context)

        self.report({'INFO'}, f"Removed shape key slot.")
        return {'FINISHED'}


class OBJECT_OT_pose_key_magic_driver(Operator):
    """Automatically drive this shape key based on current pose"""

    bl_idname = "object.posekey_magic_driver"
    bl_label = "Auto-initialize Driver"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    key_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return poll_correct_pose_key_pose(cls, context)

    @staticmethod
    def get_posed_channels(context, side=None) -> OrderedDict[str, tuple[str, float]]:
        obj = context.object
        arm_ob = get_deforming_armature(obj)

        channels = OrderedDict()

        EPSILON = 0.0001

        for pb in arm_ob.pose.bones:
            is_left = side_is_left(pb.name)
            if is_left != None and ((is_left and side!='LEFT') or (is_left==False and side=='LEFT')):
                continue
            bone_channels = OrderedDict({'loc' : [], 'rot': [], 'scale': []})

            for axis in "xyz":
                value = getattr(pb.location, axis)
                if abs(value) > EPSILON:
                    bone_channels['loc'].append((axis.upper(), value))
                    channels[pb.name] = bone_channels

                if len(pb.rotation_mode) == 3:
                    # Euler rotation: Check each axis.
                    value = getattr(pb.rotation_euler, axis)
                    if abs(value) > EPSILON:
                        bone_channels['rot'].append((axis.upper(), value))
                        channels[pb.name] = bone_channels
                else:
                    if pb.rotation_mode == 'QUATERNION':
                        euler_rot = pb.rotation_quaternion.to_euler()
                    elif pb.rotation_mode == 'AXIS_ANGLE':
                        quat = Quaternion(Vector(pb.rotation_axis_angle).yzw, pb.rotation_axis_angle[0])
                        euler_rot = quat.to_euler()

                    value = getattr(euler_rot, axis)
                    if abs(value) > EPSILON:
                        bone_channels['rot'].append((axis.upper(), value))
                        channels[pb.name] = bone_channels

                value = getattr(pb.scale, axis)
                if abs(value-1) > EPSILON:
                    bone_channels['scale'].append((axis.upper(), value))
                    channels[pb.name] = bone_channels

        return channels

    @staticmethod
    def sanitize_variable_name(name):
        # Replace all non-word characters with underscores
        sanitized = re.sub(r'\W', '_', name)
        # Prepend underscore if the first character is a digit
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized

    def invoke(self, context, event):
        is_left = side_is_left(self.key_name)
        if is_left == None:
            side = None
        elif is_left == False:
            side = 'RIGHT'
        else:
            side = 'LEFT'
        self.posed_channels = self.get_posed_channels(context, side=side)
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Driver will be created based on these transforms:")

        obj = context.object
        arm_ob = get_deforming_armature(obj)

        col = layout.column(align=True)
        for bone_name, transforms in self.posed_channels.items():
            pb = arm_ob.pose.bones.get(bone_name)
            bone_box = col.box()
            bone_box.prop(pb, 'name', icon='BONE_DATA', text="", emboss=False)
            for transform, trans_inf in transforms.items():
                axes = [f"{inf[0]} ({val:.2f})" for inf, val in trans_inf]
                if not axes:
                    continue

                if transform == 'rot':
                    icon = 'CON_ROTLIKE'
                elif transform == 'scale':
                    icon = 'CON_SIZELIKE'
                else:
                    icon = 'CON_LOCLIKE'
                bone_box.row().label(text=", ".join(axes), icon=icon)

    def execute(self, context):
        obj = context.object
        arm_ob = get_deforming_armature(obj)
        key_block = obj.data.shape_keys.key_blocks.get(self.key_name)

        key_block.driver_remove('value')
        fc = key_block.driver_add('value')
        drv = fc.driver

        expressions = []

        for bone_name, transforms in self.posed_channels.items():
            for transform, trans_inf in transforms.items():
                for axis, value in trans_inf:
                    transf_type = transform.upper()+"_"+axis
                    var = drv.variables.new()
                    var.name = self.sanitize_variable_name(bone_name) + "_" + transf_type.lower()
                    var.type = 'TRANSFORMS'
                    var.targets[0].id = arm_ob
                    var.targets[0].bone_target = bone_name
                    var.targets[0].transform_type = transf_type
                    var.targets[0].rotation_mode = 'SWING_TWIST_Y'
                    var.targets[0].transform_space = 'LOCAL_SPACE'
                    if transf_type.startswith("SCALE"):
                        expressions.append(f"((1-{var.name})/{value:.4f})")
                    else:
                        expressions.append(f"({var.name}/{value:.4f})")

        drv.expression = " * ".join(expressions)

        self.report({'INFO'}, "Created automatic driver.")
        return {'FINISHED'}


def get_deforming_armature(mesh_ob: Object) -> Object | None:
    for mod in mesh_ob.modifiers:
        if mod.type == 'ARMATURE':
            return mod.object


def reset_rig(rig, *, reset_transforms=True, reset_props=True, pbones=[]):
    if not pbones:
        pbones = rig.pose.bones
    for pb in pbones:
        if reset_transforms:
            pb.location = (0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.scale = (1, 1, 1)

        if not reset_props or len(pb.keys()) == 0:
            continue

        rna_properties = [prop.identifier for prop in pb.bl_rna.properties if prop.is_runtime]

        # Reset custom property values to their default value
        for key in pb.keys():
            if key.startswith("$"):
                continue
            if key in rna_properties:
                continue  # Addon defined property.

            property_settings = None
            try:
                property_settings = pb.id_properties_ui(key)
                if not property_settings:
                    continue
                property_settings = property_settings.as_dict()
                if not 'default' in property_settings:
                    continue
            except TypeError:
                # Some properties don't support UI data, and so don't have a default value. (like addon PropertyGroups)
                pass

            if not property_settings:
                continue

            if type(pb[key]) not in (float, int, bool):
                continue
            pb[key] = property_settings['default']


def set_pose_of_active_pose_key(context):
    rigged_ob = context.object
    pose_key = rigged_ob.data.pose_keys[rigged_ob.data.active_pose_key_index]

    arm_ob = get_deforming_armature(rigged_ob)
    reset_rig(arm_ob)
    if pose_key.action:
        # Set Action and Frame to get the right pose
        arm_ob.animation_data.action = pose_key.action
        context.scene.frame_current = pose_key.frame


def poll_correct_pose_key_pose(operator, context, demand_pose=True):
    """To make these operators foolproof, there are a lot of checks to make sure
    that the user gets to see the effect of the operator. The "Set Pose" operator
    can be used first to set the correct state and pass all the checks here.
    """

    obj = context.object

    if not obj:
        operator.poll_message_set("There must be an active mesh object.")
        return False

    pose_key = get_active_pose_key(obj)
    if not pose_key:
        operator.poll_message_set("A Pose Shape Key must be selected.")
        return False
    if not pose_key.name:
        operator.poll_message_set("The Pose Shape Key must be named.")

    arm_ob = get_deforming_armature(obj)

    if not arm_ob:
        operator.poll_message_set("This mesh object is not deformed by any Armature modifier.")
        return False

    if not pose_key.action:
        operator.poll_message_set("An Action must be associated with the Pose Shape Key.")
        return False

    if demand_pose:
        # Action must exist and match.
        if not (
            arm_ob.animation_data
            and arm_ob.animation_data.action
            and arm_ob.animation_data.action == pose_key.action
        ):
            operator.poll_message_set(
                "The armature must have the Pose Shape Key's action assigned. Use the Set Pose button."
            )
            return False

        if pose_key.frame != context.scene.frame_current:
            operator.poll_message_set(
                "The Pose Shape Key's frame must be the same as the current scene frame. Use the Set Pose button."
            )
            return False

    return True


def get_active_pose_key(obj):
    if obj.type != 'MESH':
        return
    if len(obj.data.pose_keys) == 0:
        return

    return obj.data.pose_keys[obj.data.active_pose_key_index]


registry = [
    OBJECT_OT_pose_key_auto_init,
    OBJECT_OT_pose_key_add,
    OBJECT_OT_pose_key_save,
    OBJECT_OT_pose_key_set_pose,
    OBJECT_OT_pose_key_push,
    OBJECT_OT_pose_key_push_all,
    OBJECT_OT_pose_key_clamp_influence,
    OBJECT_OT_pose_key_place_objects_in_grid,
    OBJECT_OT_pose_key_jump_to_storage,
    OBJECT_OT_pose_key_copy_data,
    OBJECT_OT_pose_key_shape_add,
    OBJECT_OT_pose_key_shape_remove,
    OBJECT_OT_pose_key_magic_driver,
]
