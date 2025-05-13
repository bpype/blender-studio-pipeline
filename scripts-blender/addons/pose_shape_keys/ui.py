# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel, UIList, Menu
from bl_ui.properties_data_mesh import DATA_PT_shape_keys
from bpy.props import EnumProperty

from .ui_list import draw_ui_list
from .ops import get_deforming_armature, poll_correct_pose_key_pose
from .prefs import get_addon_prefs


class MESH_PT_pose_keys(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Pose Shape Keys"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def draw(self, context):
        obj = context.object
        mesh = obj.data
        layout = self.layout.column()

        layout.row().prop(mesh, 'shape_key_ui_type', expand=True)

        if mesh.shape_key_ui_type == 'DEFAULT':
            return DATA_PT_shape_keys.draw(self, context)

        arm_ob = get_deforming_armature(obj)
        if not arm_ob:
            layout.alert = True
            layout.label(text="Object must be deformed by an Armature to use Pose Keys.")
            return

        if mesh.shape_keys and not mesh.shape_keys.use_relative:
            layout.alert = True
            layout.label("Relative Shape Keys must be enabled!")
            return

        list_row = layout.row()

        groups_col = list_row.column()
        draw_ui_list(
            groups_col,
            context,
            class_name='POSEKEYS_UL_pose_keys',
            list_context_path='object.data.pose_keys',
            active_idx_context_path='object.data.active_pose_key_index',
            menu_class_name='MESH_MT_pose_key_utils',
            add_op_name='object.posekey_add',
        )

        layout.use_property_split = True
        layout.use_property_decorate = False

        if len(mesh.pose_keys) == 0:
            return

        idx = context.object.data.active_pose_key_index
        active_posekey = context.object.data.pose_keys[idx]

        action_split = layout.row().split(factor=0.4, align=True)
        action_split.alignment = 'RIGHT'
        action_split.label(text="Action")
        row = action_split.row(align=True)
        icon = 'FORWARD'
        if active_posekey.action:
            icon = 'FILE_REFRESH'
        row.operator('object.posekey_auto_init', text="", icon=icon)
        row.prop(active_posekey, 'action', text="")
        layout.prop(active_posekey, 'frame')

        layout.separator()

        layout.operator('object.posekey_set_pose', text="Set Pose", icon="ARMATURE_DATA")

        layout.separator()

        row = layout.row(align=True)
        text = "Save Posed Mesh"
        if active_posekey.storage_object:
            text = "Overwrite Posed Mesh"
        row.operator('object.posekey_save', text=text, icon="FILE_TICK")
        row.prop(active_posekey, 'storage_object', text="")
        row.operator('object.posekey_jump_to_storage', text="", icon='RESTRICT_SELECT_OFF')


class POSEKEYS_UL_pose_keys(UIList):
    def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
        pose_key = item

        if self.layout_type != 'DEFAULT':
            # Other layout types not supported by this UIList.
            return

        split = layout.row().split(factor=0.7, align=True)

        icon = 'SURFACE_NCIRCLE' if pose_key.storage_object else 'CURVE_NCIRCLE'
        name_row = split.row()
        if not pose_key.name:
            name_row.alert = True
            split = name_row.split()
            name_row = split.row()
            split.label(text="Unnamed!", icon='ERROR')
        name_row.prop(pose_key, 'name', text="", emboss=False, icon=icon)


class MESH_MT_pose_key_utils(Menu):
    bl_label = "Pose Key Utilities"

    def draw(self, context):
        layout = self.layout
        layout.operator('object.posekey_object_grid', icon='LIGHTPROBE_VOLUME')
        layout.operator('object.posekey_push_all', icon='WORLD')
        layout.operator('object.posekey_clamp_influence', icon='NORMALIZE_FCURVES')
        layout.operator('object.posekey_copy_data', icon='PASTEDOWN')


class MESH_PT_shape_key_subpanel(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Shape Key Slots"
    bl_parent_id = "MESH_PT_pose_keys"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not (obj and obj.data and obj.data.shape_key_ui_type=='POSE_KEYS'):
            return False
        try:
            return poll_correct_pose_key_pose(cls, context, demand_pose=False)
        except AttributeError:
            # Happens any time that function tries to set a poll message,
            # since panels don't have poll messages, lol.
            return False

    def draw(self, context):
        obj = context.object
        mesh = obj.data
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        idx = context.object.data.active_pose_key_index
        active_posekey = context.object.data.pose_keys[idx]

        layout.operator('object.posekey_push', text="Overwrite Shape Keys", icon="IMPORT")

        draw_ui_list(
            layout,
            context,
            class_name='POSEKEYS_UL_target_shape_keys',
            list_context_path=f'object.data.pose_keys[{idx}].target_shapes',
            active_idx_context_path=f'object.data.pose_keys[{idx}].active_target_shape_index',
            add_op_name='object.posekey_shape_add',
            remove_op_name='object.posekey_shape_remove',
        )

        if len(active_posekey.target_shapes) == 0:
            return

        active_target = active_posekey.active_target
        row = layout.row()
        if not mesh.shape_keys:
            return
        row.prop_search(active_target, 'shape_key_name', mesh.shape_keys, 'key_blocks')
        if not active_target.key_block:
            add_shape_op = row.operator('object.posekey_shape_add', icon='ADD', text="")
            add_shape_op.create_slot=False
        sk = active_target.key_block
        if not sk:
            return
        addon_prefs = get_addon_prefs(context)
        icon = 'HIDE_OFF' if addon_prefs.show_shape_key_info else 'HIDE_ON'
        row.prop(addon_prefs, 'show_shape_key_info', text="", icon=icon)
        if addon_prefs.show_shape_key_info:
            layout.prop(active_target, 'mirror_x')
            split = layout.split(factor=0.1)
            split.row()
            col = split.column()
            col.row().prop(sk, 'value')
            row = col.row(align=True)
            row.prop(sk, 'slider_min', text="Range")
            row.prop(sk, 'slider_max', text="")
            col.prop_search(sk, "vertex_group", obj, "vertex_groups", text="Vertex Mask")
            col.row().prop(sk, 'relative_key')


class POSEKEYS_UL_target_shape_keys(UIList):
    def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
        obj = context.object
        pose_key_target = item
        key_block = pose_key_target.key_block

        if self.layout_type != 'DEFAULT':
            # Other layout types not supported by this UIList.
            return

        split = layout.row().split(factor=0.7, align=True)

        name_row = split.row()
        name_row.prop(pose_key_target, 'name', text="", emboss=False, icon='SHAPEKEY_DATA')

        value_row = split.row(align=True)
        value_row.emboss = 'NONE_OR_STATUS'
        if not key_block:
            return
        if (
            key_block.mute
            or (obj.mode == 'EDIT' and not (obj.use_shape_key_edit_mode and obj.type == 'MESH'))
            or (obj.show_only_shape_key and key_block != obj.active_shape_key)
        ):
            name_row.active = value_row.active = False

        value_row.operator('object.posekey_magic_driver', text="", icon='DECORATE_DRIVER').key_name = key_block.name
        value_row.prop(key_block, "value", text="")

        mute_row = split.row()
        mute_row.alignment = 'RIGHT'
        mute_row.prop(key_block, 'mute', emboss=False, text="")


@classmethod
def shape_key_panel_new_poll(cls, context):
    engine = context.engine
    obj = context.object
    return obj and obj.type in {'LATTICE', 'CURVE', 'SURFACE'} and (engine in cls.COMPAT_ENGINES)


registry = [
    POSEKEYS_UL_pose_keys,
    POSEKEYS_UL_target_shape_keys,
    MESH_PT_pose_keys,
    MESH_PT_shape_key_subpanel,
    MESH_MT_pose_key_utils,
]


def register():
    bpy.types.Mesh.shape_key_ui_type = EnumProperty(
        name="Shape Key List Type",
        items=[
            ('DEFAULT', 'Shape Keys', "Show a flat list of shape keys"),
            (
                'POSE_KEYS',
                'Pose Shape Keys',
                "Organize shape keys into a higher-level concept called Pose Keys. These can store vertex positions and push one shape to multiple shape keys at once, relative to existing deformation",
            ),
        ],
    )

    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'bl_parent_id') and panel.bl_parent_id == 'DATA_PT_shape_keys':
            panel.bl_parent_id = 'MESH_PT_pose_keys'
            try:
                bpy.utils.unregister_class(panel)
                bpy.utils.register_class(panel)
            except RuntimeError:
                # Class was already unregistered, leave it unregistered.
                pass

    DATA_PT_shape_keys.replacement = 'MESH_PT_pose_keys'  # This is used by GeoNodeShapeKeys add-on to register to the correct parent panel. Could be used by any other add-on I guess.
    DATA_PT_shape_keys.old_poll = DATA_PT_shape_keys.poll
    DATA_PT_shape_keys.poll = shape_key_panel_new_poll


def unregister():
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'bl_parent_id') and panel.bl_parent_id == 'MESH_PT_pose_keys':
            panel.bl_parent_id = 'DATA_PT_shape_keys'
            try:
                bpy.utils.unregister_class(panel)
                bpy.utils.register_class(panel)
            except RuntimeError:
                # Class was already unregistered, leave it unregistered.
                pass

    del bpy.types.Mesh.shape_key_ui_type
    DATA_PT_shape_keys.poll = DATA_PT_shape_keys.old_poll
    DATA_PT_shape_keys.replacement = None
