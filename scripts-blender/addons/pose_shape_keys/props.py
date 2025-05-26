# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import PropertyGroup, Object, Action, ShapeKey
from bpy.props import PointerProperty, IntProperty, CollectionProperty, StringProperty, BoolProperty


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
        try:
            sk_name = self.target_shapes[self.active_target_shape_index].shape_key_name
        except IndexError:
            obj.active_shape_key_index = len(obj.data.shape_keys.key_blocks) - 1
            return
        key_block_idx = obj.data.shape_keys.key_blocks.find(sk_name)
        if key_block_idx > -1:
            obj.active_shape_key_index = key_block_idx

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
        return self.target_shapes[self.active_target_shape_index]

    @property
    def has_error(self):
        return self.name.strip() == "" or any([target.has_error for target in self.target_shapes])

    def update_name(self, context):
        if self.name.strip() == "":
            self.name = "Pose Key"

    name: StringProperty(name="Name", update=update_name)

    action: PointerProperty(
        name="Action",
        type=Action,
        description="Action that contains the frame that should be used when applying the stored shape as a shape key",
    )
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
        pk = mesh.pose_keys[mesh.active_pose_key_index]
        # We just want to fire the update func.
        pk.active_target_shape_index = pk.active_target_shape_index


def register():
    bpy.types.Mesh.pose_keys = CollectionProperty(type=PoseShapeKey)
    bpy.types.Mesh.active_pose_key_index = IntProperty(update=update_posekey_index)


def unregister():
    del bpy.types.Mesh.pose_keys
    del bpy.types.Mesh.active_pose_key_index
