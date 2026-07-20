# SPDX-FileCopyrightText: 2024-2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bmesh
import bpy
from bpy.props import BoolProperty
from bpy.types import ID, AnimData, Context, FCurve, Object, Operator, ShapeKey
from bpy.utils import flip_name
from mathutils.kdtree import KDTree


class EASYWEIGHT_OT_force_apply_mirror(Operator):
    """Force apply mirror modifier by duplicating the object, flipping it on the X axis, merging into the original, and welding it at the middle"""

    bl_idname = "object.force_apply_mirror_modifier"
    bl_label = "Force Apply Mirror Modifier"
    bl_options = {"REGISTER", "UNDO"}

    weighted_normals: BoolProperty(name="Weighted Normals", default=True)
    split_shape_keys: BoolProperty(
        name="Split Shape Keys",
        default=True,
        description="If shape keys end in either .L or .R, duplicate them, flip their mask vertex group name, and their driver",
    )

    @classmethod
    def poll(cls, context: Context):
        obj = context.active_object
        if not (obj and obj.type == "MESH" and obj.data and obj.data.shape_keys):
            cls.poll_message_set("There must be an active mesh object with shape keys.")
            return False
        for mod in obj.modifiers:
            if mod.type == "MIRROR":
                if mod.use_axis[:] != (True, False, False):
                    cls.poll_message_set("Only X axis mirror modifier is supported.")
                    return False
                return True
        cls.poll_message_set("This mesh has no Mirror modifier.")
        return False

    def execute(self, context: Context):
        obj = context.active_object

        mirror = next((mod for mod in obj.modifiers if mod.type == "MIRROR"), None)
        if not mirror:
            return {"CANCELLED"}
        if mirror.use_axis[:] != (True, False, False):
            self.report({"ERROR"}, "Only X axis mirroring is supported for now.")
            return {"CANCELLED"}

        merge_center = mirror.use_mirror_merge
        clip_threshold = mirror.merge_threshold

        obj.modifiers.remove(mirror)

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj

        org_scale = obj.scale[:]
        obj.scale = (1, 1, 1)

        bpy.ops.object.duplicate()
        flipped_obj = context.active_object
        flipped_obj.scale = (-1, 1, 1)

        _flip_names(flipped_obj.vertex_groups)

        if self.split_shape_keys and flipped_obj.data.shape_keys:
            _flip_names(flipped_obj.data.shape_keys.key_blocks)
            flip_shape_key_drivers(flipped_obj)
            copy_shape_key_drivers(
                flipped_obj.data.shape_keys,
                obj.data.shape_keys,
            )

        flipped_obj.select_set(True)
        obj.select_set(True)
        # We want to be sure the original is the active so the object name doesn't get a .001
        context.view_layer.objects.active = obj
        bpy.ops.object.join()

        combined_object = context.active_object
        combined_object.select_set(False)
        bpy.ops.object.delete(use_global=False)

        bpy.ops.object.mode_set(mode="EDIT")

        if merge_center:
            bm = bmesh.from_edit_mesh(combined_object.data)
            for vert in bm.verts:
                vert.select = abs(vert.co.x) < clip_threshold
            bm.select_flush_mode()
            _average_seam_weights(bm, clip_threshold)
            bmesh.update_edit_mesh(combined_object.data)

            bpy.ops.mesh.remove_doubles(threshold=clip_threshold)

        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.object.mode_set(mode="OBJECT")
        if self.weighted_normals and "calculate_weighted_normals" in dir(
            bpy.ops.object
        ):
            bpy.ops.object.calculate_weighted_normals()

        refresh_drivers(combined_object)

        combined_object.scale = org_scale

        self.report({"INFO"}, "Applied X-Mirror modifier with shape keys.")
        return {"FINISHED"}


def _average_seam_weights(bm: bmesh.types.BMesh, threshold: float) -> None:
    """Average vertex group weights across vertices that will be merged by remove_doubles,
    so the surviving vertex always ends up with the averaged weights of the merge cluster."""
    seam_verts = [v for v in bm.verts if v.select]
    if len(seam_verts) < 2:
        return

    kd = KDTree(len(seam_verts))
    for i, v in enumerate(seam_verts):
        kd.insert(v.co, i)
    kd.balance()

    deform = bm.verts.layers.deform.verify()

    # BFS to find connected components within the merge threshold.
    component = [-1] * len(seam_verts)
    comp_id = 0
    for i in range(len(seam_verts)):
        if component[i] != -1:
            continue
        queue = [i]
        component[i] = comp_id
        while queue:
            curr = queue.pop()
            for _, j, _ in kd.find_range(seam_verts[curr].co, threshold):
                if component[j] == -1:
                    component[j] = comp_id
                    queue.append(j)
        comp_id += 1

    clusters: dict[int, list[int]] = {}
    for i, c in enumerate(component):
        clusters.setdefault(c, []).append(i)

    for indices in clusters.values():
        if len(indices) < 2:
            continue
        all_keys: set[int] = set()
        for idx in indices:
            all_keys.update(seam_verts[idx][deform].keys())
        for key in all_keys:
            avg = sum(seam_verts[idx][deform].get(key, 0.0) for idx in indices) / len(
                indices
            )
            for idx in indices:
                seam_verts[idx][deform][key] = avg


def _flip_names(things_with_names: list):
    """Swap mirrored name pairs in a vertex group or shape key collection."""
    done = set()
    for item in things_with_names:
        if item in done:
            continue
        old_name = item.name
        flipped = flip_name(old_name)
        if old_name == flipped:
            continue
        opposite = things_with_names.get(flipped)
        if opposite:
            item.name = "temp"
            opposite.name = old_name
            done.add(opposite)
        item.name = flipped
        done.add(item)


def copy_shape_key_drivers(src_shape_keys: ShapeKey, dst_shape_keys: ShapeKey):
    anim_data = src_shape_keys.animation_data
    if not (anim_data and anim_data.drivers):
        return
    for old_fcurve in anim_data.drivers:
        for key_block in src_shape_keys.key_blocks:
            if key_block.name in old_fcurve.data_path:
                copy_driver(old_fcurve, dst_shape_keys, old_fcurve.data_path)


def copy_driver(
    from_fcurve: FCurve, target: ID, data_path: str = None, index: int = None
) -> FCurve:
    """Copy an existing FCurve containing a driver to a new ID, by creating a copy
    of the existing driver on the target ID.

    Args:
        from_fcurve: FCurve containing a driver
        target: ID that can have AnimationData
        data_path: Data Path of new driver. Defaults to copying the passed fcurve
        index: array index of the property to drive. Defaults to copying the passed fcurve

    Returns:
        FCurve: Fcurve with new driver on target ID
    """

    # Ensure anim data.
    if not target.animation_data:
        target.animation_data_create()

    # Remove old driver if it exists.
    tgt_drivers = target.animation_data.drivers
    if not data_path:
        data_path = from_fcurve.data_path
    if index not in {-1, None}:
        old_fcurve = tgt_drivers.find(data_path, index=index)
    else:
        old_fcurve = tgt_drivers.find(data_path)

    if old_fcurve:
        tgt_drivers.remove(old_fcurve)

    new_fcurve = tgt_drivers.from_existing(src_driver=from_fcurve)
    new_fcurve.data_path = data_path
    if index not in {None, -1}:
        new_fcurve.array_index = index

    return new_fcurve


def flip_shape_key_drivers(obj: Object):
    def _flip_var_sign(expression: str, var_name: str) -> str:
        if f"-{var_name}" in expression:
            return expression.replace(f"-{var_name}", f"+{var_name}")
        if f"+ {var_name}" in expression:
            return expression.replace(f"+ {var_name}", f"- {var_name}")
        return expression.replace(var_name, f"-{var_name}")

    shape_keys: ShapeKey = obj.data.shape_keys
    if not shape_keys:
        return
    anim_data: AnimData = shape_keys.animation_data
    if not anim_data:
        return

    flipped_sks = set()
    for key_block in shape_keys.key_blocks:
        # The name prefix before the first underscore indicates which transform axes to flip.
        flip_flags = key_block.name.split("_")[0]
        has_axis_prefix = flip_flags in {"XYZ", "XZ", "XY", "YZ", "Z"}
        x_flag = has_axis_prefix and "X" in flip_flags
        y_flag = has_axis_prefix and "Y" in flip_flags
        z_flag = has_axis_prefix and "Z" in flip_flags
        any_flag = any((x_flag, y_flag, z_flag))

        driver_fcurves: list[FCurve] = anim_data.drivers

        for fcurve in driver_fcurves:
            if key_block.name not in fcurve.data_path:
                continue
            if key_block.name not in flipped_sks:
                key_block.vertex_group = flip_name(key_block.vertex_group)
                flipped_sks.add(key_block.name)
            driver = fcurve.driver
            for var in driver.variables:
                for tar in var.targets:
                    if tar.bone_target:
                        tar.bone_target = flip_name(tar.bone_target)

                target_0 = var.targets[0]
                should_flip = target_0.bone_target and (
                    "SCALE" not in target_0.transform_type
                    and (
                        (target_0.transform_type.endswith("_X") and x_flag)
                        or (target_0.transform_type.endswith("_Y") and y_flag)
                        or (target_0.transform_type.endswith("_Z") and z_flag)
                    )
                    or (
                        not any_flag
                        and target_0.transform_type in ("ROT_Z", "ROT_Y", "LOC_X")
                    )
                )
                if should_flip:
                    driver.expression = _flip_var_sign(driver.expression, var.name)


def refresh_drivers(id: ID):
    """Cause all drivers belonging to the object to be re-evaluated, clearing any errors."""

    if hasattr(id, "data") and id.data:
        refresh_drivers(id.data)
        if hasattr(id.data, "shape_keys") and id.data.shape_keys:
            refresh_drivers(id.data.shape_keys)

    # Refresh object's own drivers if any
    anim_data = getattr(id, "animation_data", None)

    if anim_data:
        for fcu in anim_data.drivers:
            # Make a fake change to the driver
            fcu.driver.type = fcu.driver.type


def draw_force_apply_mirror(self, _context: Context):
    self.layout.separator()
    self.layout.operator(EASYWEIGHT_OT_force_apply_mirror.bl_idname, icon="MOD_MIRROR")


registry = [EASYWEIGHT_OT_force_apply_mirror]


def register():
    bpy.types.MESH_MT_shape_key_context_menu.append(draw_force_apply_mirror)


def unregister():
    bpy.types.MESH_MT_shape_key_context_menu.remove(draw_force_apply_mirror)
