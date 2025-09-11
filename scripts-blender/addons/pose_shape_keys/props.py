# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, random
from bpy.types import PropertyGroup, Object, Action, ActionSlot, ShapeKey
from bpy.props import PointerProperty, IntProperty, CollectionProperty, StringProperty, BoolProperty
from .ops import get_active_pose_key

class PoseShapeKeyTarget(PropertyGroup):
    def update_name(self, context):
        if self.block_name_update:
            return
        obj = context.object
        if not obj.data.shape_keys:
            return
        sk = obj.data.shape_keys.key_blocks.get(self.shape_key_name)
        if sk:
            sk.name = self.name
        self.shape_key_name = self.name

    def update_shape_key_name(self, context):
        self.block_name_update = True
        self.name = self.shape_key_name
        self.block_name_update = False

    name: StringProperty(
        name="Shape Key Target",
        description="Name of this shape key target. Should stay in sync with the displayed name and the shape key name, unless the shape key is renamed outside of our UI",
        update=update_name,
    )
    mirror_x: BoolProperty(
        name="Mirror X",
        description="Mirror the shape key on the X axis when applying the stored shape to this shape key",
        default=False,
    )

    block_name_update: BoolProperty(
        description="Flag to help keep shape key names in sync", default=False
    )
    shape_key_name: StringProperty(
        name="Shape Key",
        description="Name of the shape key to push data to",
        update=update_shape_key_name,
    )

    @property
    def has_error(self):
        return self.key_block == None

    @property
    def key_block(self) -> list[ShapeKey]:
        mesh = self.id_data
        if not mesh.shape_keys:
            return
        return mesh.shape_keys.key_blocks.get(self.name)


class PoseShapeKey(PropertyGroup):
    target_shapes: CollectionProperty(type=PoseShapeKeyTarget)

    def update_active_sk_index(self, context):
        obj = context.object
        if not obj.data.shape_keys:
            return
        active_target = self.active_target
        if active_target:
            sk_name = self.active_target.shape_key_name
            key_block_idx = obj.data.shape_keys.key_blocks.find(sk_name)
            obj.active_shape_key_index = key_block_idx
        else:
            obj.active_shape_key_index = -1
            return

        # If in weight paint mode and there is a mask vertex group,
        # also set that vertex group as active.
        if context.mode == 'PAINT_WEIGHT':
            key_block = obj.data.shape_keys.key_blocks[key_block_idx]
            vg_idx = obj.vertex_groups.find(key_block.vertex_group)
            if vg_idx > -1:
                obj.vertex_groups.active_index = vg_idx

    active_target_shape_index: IntProperty(update=update_active_sk_index)

    @property
    def active_target(self):
        if len(self.target_shapes) == 0:
            return
        return self.target_shapes[self.active_target_shape_index]

    @property
    def has_error(self):
        return self.name.strip() == "" or any([target.has_error for target in self.target_shapes])

    def update_name(self, context):
        if self.name.strip() == "":
            self.name = "Pose Key"

    name: StringProperty(name="Name", update=update_name)

    def auto_slot(self, context):
        if self.action and len(self.action.slots)==1:
            self.action_slot = self.action.slots[0]

    action: PointerProperty(
        name="Action",
        type=Action,
        description="Action that contains the frame that should be used when applying the stored shape as a shape key",
        update=auto_slot,
    )

    def slot_name_from_handle(self, curr_value, _is_set) -> str:
        try:
            curr_value = int(curr_value)
        except:
            return ""
        action_slot = next((s for s in self.action.slots if s.handle==curr_value), None)
        if not action_slot:
            return ""
        return action_slot.name_display

    def slot_name_to_handle(self, new_value, curr_value, _is_set)  -> str:
        action_slot = next((s for s in self.action.slots if s.name_display==new_value and s.identifier.startswith("OB")), None)
        if not action_slot:
            return ""
        return str(action_slot.handle)

    action_slot_ui: StringProperty(
        name="Acion Slot",
        description="Slot of the Action to use for the Action Constraints",
        get_transform=slot_name_from_handle,
        set_transform=slot_name_to_handle,
    )

    @property
    def unique_id(self) -> int:
        if not self.action and 'unique_id' not in self:
            return 0
        if 'unique_id' in self and self['unique_id'] != 0:
            return self.get('unique_id')
        else:
            self['unique_id'] = random.randint(0, 100_000_000)
        return self['unique_id']

    @property
    def action_slot(self) -> ActionSlot | None:
        return self.action.slots.get("OB"+self.action_slot_ui)

    @action_slot.setter
    def action_slot(self, slot):
        if slot:
            self.action_slot_ui = slot.name_display

    frame: IntProperty(
        name="Frame",
        description="Frame that should be used within the selected action when applying the stored shape as a shape key",
        default=0,
    )
    storage_object: PointerProperty(
        type=Object,
        name="Storage Object",
        description="Specify an object that stores the vertex position data",
    )


registry = [
    PoseShapeKeyTarget,
    PoseShapeKey,
]


def update_posekey_index(self, context):
    # Want to piggyback on update_active_sk_index() to also update the active
    # shape key index when switching pose keys.
    mesh = context.object.data
    if mesh.pose_keys:
        pk = get_active_pose_key(context.object)
        if pk:
            # We just want to fire the update func.
            pk.active_target_shape_index = pk.active_target_shape_index
        else:
            # If nothing is active in the UI, avoid any shape key being active, 
            # so it doesn't get unintentionally modified.
            context.object.data.active_shape_key_index = -1

def register():
    bpy.types.Mesh.pose_keys = CollectionProperty(type=PoseShapeKey)
    bpy.types.Mesh.active_pose_key_index = IntProperty(update=update_posekey_index)


def unregister():
    del bpy.types.Mesh.pose_keys
    del bpy.types.Mesh.active_pose_key_index
