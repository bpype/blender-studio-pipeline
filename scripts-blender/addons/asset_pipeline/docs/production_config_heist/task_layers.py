from typing import Any, Dict, List, Set, Union, Optional, Tuple
from bpy.types import PropertyGroup, Object, Mesh, Curve, Context, Attribute, FCurve, Collection

import bpy
import mathutils
import bmesh
import numpy as np
from asset_pipeline.api import (
    AssetTransferMapping,
    TaskLayer,
    BuildContext,
)


class TransferSettings(PropertyGroup):
    pass
    # imp_mat: bpy.props.BoolProperty(name="Materials", default=True)  # type: ignore
    # imp_uv: bpy.props.BoolProperty(name="UVs", default=True)  # type: ignore
    # imp_vcol: bpy.props.BoolProperty(name="Vertex Colors", default=True)  # type: ignore
    # transfer_type: bpy.props.EnumProperty(  # type: ignore
    #    name="Transfer Type",
    #    items=[("VERTEX_ORDER", "Vertex Order", ""), ("PROXIMITY", "Proximity", "")],
    # )


class TaskLayerMixin:
    """Functionality that should be shared among all TaskLayers.
    Code that ends up here should probably be migrated to the 
    TaskLayer class in the AssetPipeline add-on itself.
    """

    @classmethod
    def handle_new_object(cls, obj: Object, transfer_mapping: AssetTransferMapping):
        prefix_modifiers(obj, cls.mod_prefix)

        # Sync modifier settings.
        for i, mod in enumerate(obj.modifiers):
            if mod.name.split('-')[0] not in [cls.mod_prefix, 'APL']:
                continue
            for prop in [p.identifier for p in mod.bl_rna.properties if not p.is_readonly]:
                value = getattr(mod, prop)
                if type(value) == Object and value in transfer_mapping.object_map:
                    # If a modifier is referencing a .TASK object,
                    # remap that reference to a .TARGET object.
                    # (Eg. modeling Mirror modifier with a mirror object)
                    value = transfer_mapping.object_map[value]
                setattr(mod, prop, value)

    @classmethod
    def handle_new_objects(cls, transfer_mapping: AssetTransferMapping):
        for obj in transfer_mapping.no_match_source_objs:
            cls.handle_new_object(obj, transfer_mapping)

    @classmethod
    def get_collections(
            cls, 
            transfer_mapping: AssetTransferMapping
            ) -> Tuple[Collection, List[Object], Collection]:
        # TODO: I think this is already done by the add-on? Maybe it's just a matter of passing it on?

        # identify hair collections in source and target
        colls_source = []
        for coll in transfer_mapping.collection_map.keys():
            task_suffix_separator = "."
            if cls.task_suffix in coll.name:
                colls_source += [coll]
        objs_source = {
            ob for coll in colls_source for ob in list(coll.all_objects)}

        colls_target = []
        for coll in transfer_mapping.collection_map.keys():
            if coll.name.split(cls.task_suffix[:1])[-2] == cls.task_suffix[1:]:
                colls_target += [transfer_mapping.collection_map[coll]]

        return colls_source, objs_source, colls_target


class RiggingTaskLayer(TaskLayer, TaskLayerMixin):
    name = "Rigging"
    task_suffix = ".rig"
    order = 0

    @classmethod
    def transfer_data(
        cls,
        context: Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: PropertyGroup,
    ) -> None:
        print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

        # add prefixes to existing modifiers
        for obj_source, obj_target in transfer_mapping.object_map.items():
            prefix_modifiers(obj_target, 'RIG')


class ModelingTaskLayer(TaskLayer, TaskLayerMixin):
    """Only affects objects of the target inside collections ending with '.geometry'.
        New objects can be created anywhere.
        New modifiers are automatically prefixed with 'GEO-'.
        Any modifier that is given the prefix 'APL-' will be automatically applied after push.
        The order of the modifier stack is generally owned by the rigging task layer.
        Newly created modifiers in the modeling task layer are an exception.
    """
    name = "Modeling"
    task_suffix = ".geometry"
    order = 1
    mod_prefix = 'GEO'

    @classmethod
    def transfer_data(
        cls,
        context: Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        _transfer_settings: PropertyGroup,

    ) -> None:
        print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

        # Identify geometry collections in source and target.
        _geo_colls_src, geo_objs_src, _geo_colls_tgt = cls.get_collections(transfer_mapping)

        cls.handle_new_objects(transfer_mapping)

        # Transfer data between object geometries.
        for obj_source, obj_target in transfer_mapping.object_map.items():
            if obj_source not in geo_objs_src:
                continue

            cls.transfer_transforms_and_parenting(obj_source, obj_target)
            cls.transfer_instancing(obj_source, obj_target, transfer_mapping)

            if obj_source.type != obj_target.type:
                print(warning_text(
                    f"Mismatching object type. Skipping {obj_target.name}."))
                continue

            topo_match = is_obdata_identical(obj_source, obj_target)
            if topo_match is None:
                continue

            if topo_match:
                if obj_target.type == 'MESH':
                    cls.transfer_modeling_mesh_data_by_topo(context, obj_source, obj_target)
                elif obj_target.type == 'CURVE':  # TODO: proper geometry transfer for curves
                    obj_target.data = obj_source.data
                else:
                    pass

                cls.transfer_geometry_shape_keys(obj_source, obj_target)

            # If topology does not match replace geometry (throw warning)
            # TODO: handle data transfer onto mesh for simple cases (trivial 
            # topological changes: e.g. added separate mesh island, added span)
            else:
                cls.transfer_modeling_mesh_data_by_proximity(context, obj_source, obj_target)

            prefix_modifiers(obj_source, cls.mod_prefix)
            sync_modifiers(transfer_mapping, obj_source,
                           obj_target, [cls.mod_prefix, 'APL'])
            rebind_modifiers(obj_target)

        # Restore multi-users.
        if not (build_context.is_push or type(cls) in build_context.asset_context.task_layer_assembly.get_used_task_layers()):
            meshes_dict = dict()
            for ob in transfer_mapping.object_map.keys():
                if not ob.data:
                    continue
                if ob.type not in ['MESH', 'CURVE']:
                    continue
                if ob.data not in meshes_dict.keys():
                    meshes_dict[ob.data] = [ob]
                else:
                    meshes_dict[ob.data] += [ob]
            for mesh, objects in meshes_dict.items():
                main_mesh = transfer_mapping.object_map[objects[0]].data
                for ob in objects:
                    transfer_mapping.object_map[ob].data = main_mesh


    @staticmethod
    def transfer_modeling_mesh_data_by_topo(context: Context, obj_source: Object, obj_target: Object):
        if len(obj_target.data.vertices) == 0:
            print(warning_text(
                f"Mesh object '{obj_target.name}' has empty object data"))
            return

        # Transfer Vertex Bevel Weights.
        # for vert_from, vert_to in zip(obj_source.data.vertices, obj_target.data.vertices):
        #     vert_to.bevel_weight = vert_from.bevel_weight

        # Transfer Vertex Crease.
        if len(obj_source.data.vertex_creases) > 0:
            if len(obj_target.data.vertex_creases) == 0:
                # Ensure the target vertex crease data layer exists.
                # Sadly this can only be done with bmesh, which needs mode switching.
                context.view_layer.objects.active = obj_target
                target_bm = bmesh.new()
                target_bm.from_mesh(obj_target.data)
                target_bm.verts.layers.crease.verify()
                target_bm.to_mesh(obj_target.data)

            for i in range(len(obj_source.data.vertices)):
                obj_target.data.vertex_creases[0].data[i].value = obj_source.data.vertex_creases[0].data[i].value

        # Transfer Edge Bevel & Crease.
        # for edge_from, edge_to in zip(obj_source.data.edges, obj_target.data.edges):
        #     edge_to.bevel_weight = edge_from.bevel_weight
        #     edge_to.crease = edge_from.crease

        # Transfer vertex position while keeping Shape Keys intact.
        offset = [obj_source.data.vertices[i].co -
                    obj_target.data.vertices[i].co for i in range(len(obj_source.data.vertices))]

        offset_sum = 0
        for x in offset:
            offset_sum += x.length
        offset_avg = offset_sum/len(offset)
        if offset_avg > 0.1:
            print(warning_text(
                f"Average Vertex offset is {offset_avg} for {obj_target.name}"))

        for i, vec in enumerate(offset):
            obj_target.data.vertices[i].co += vec

        # Update Shape Keys.
        if obj_target.data.shape_keys:
            for key in obj_target.data.shape_keys.key_blocks:
                for i, point in enumerate([dat.co for dat in key.data]):
                    key.data[i].co = point + offset[i]


    @staticmethod
    def transfer_modeling_mesh_data_by_proximity(context: Context, obj_source: Object, obj_target: Object):
        """Replace the object data and transfer all rigging data by proximity."""

        if obj_target.type != 'MESH':
            obj_target.data = obj_source.data
            return

        # Generate new transfer source object from mesh data.
        obj_target_original = bpy.data.objects.new(
            f"{obj_target.name}.original", obj_target.data)

        sk_original = None
        if obj_target.data.shape_keys:
            sk_original = obj_target.data.shape_keys.copy()

        context.scene.collection.objects.link(obj_target_original)

        print(warning_text(
            f"Topology Mismatch! Replacing object data and transferring with potential data loss on '{obj_target.name}'"))
        obj_target.data = obj_source.data

        # transfer weights
        bpy.ops.object.data_transfer(
            {
                "object": obj_target_original,
                "active_object": obj_target_original,
                "selected_editable_objects": [obj_target],
            },
            data_type="VGROUP_WEIGHTS",
            use_create=True,
            vert_mapping='POLYINTERP_NEAREST',
            layers_select_src="ALL",
            layers_select_dst="NAME",
            mix_mode="REPLACE",
        )

        # Transfer Shape Keys.
        # TODO: Allow proximity transfer for geometry shapekeys.
        transfer_shapekeys_proximity(obj_target_original, obj_target)

        # Transfer drivers.
        copy_drivers(sk_original, obj_target.data.shape_keys)

        del sk_original
        bpy.data.objects.remove(obj_target_original)


    @staticmethod
    def transfer_transforms_and_parenting(obj_source: Object, obj_target: Object):
        # Transfer object transformation: Constraints (TODO?), parenting, transforms.
        con_vis = []
        for con in obj_target.constraints:
            con_vis += [con.enabled]
            con.enabled = False
        for con in obj_source.constraints:
            con.enabled = False

        copy_parenting(obj_target, obj_source)
        copy_transforms(obj_source, obj_target)

        for con, vis in zip(obj_target.constraints, con_vis):
            con.enabled = vis

    @staticmethod
    def transfer_instancing(obj_source: Object, obj_target: Object, transfer_mapping: AssetTransferMapping):
        obj_target.instance_type = obj_source.instance_type
        if obj_target.instance_type == 'COLLECTION':
            instance_coll = transfer_mapping.collection_map.get(
                obj_source.instance_collection)
            if not instance_coll:
                instance_coll = obj_source.instance_collection
            obj_target.instance_collection = instance_coll


    @staticmethod
    def transfer_geometry_shape_keys(obj_source: Object, obj_target: Object):
        if obj_target.data.shape_keys:
            for sk_target in obj_target.data.shape_keys.key_blocks:
                if not sk_target.name.split('-')[0] == 'GEO':
                    continue
                obj_target.shape_key_remove(sk_target)
        if obj_source.data.shape_keys:
            for sk_source in obj_source.data.shape_keys.key_blocks:
                if not sk_source.name.split('-')[0] == 'GEO':
                    continue
                if obj_target.data.shape_keys:
                    sk_target = obj_target.data.shape_keys.key_blocks.get(
                        sk_source.name)
                else:
                    obj_target.shape_key_add(name='Basis')
                    sk_target = None
                if not sk_target:
                    sk_target = obj_target.shape_key_add()
                    sk_target.name = sk_source.name

                sk_target.vertex_group = sk_source.vertex_group
                sk_target.value = sk_source.value
                sk_target.relative_key = obj_target.data.shape_keys.key_blocks[
                    sk_source.relative_key.name]

                for i in range(len(sk_source.data)):
                    sk_target.data[i].co = sk_source.data[i].co


class GroomingTaskLayer(TaskLayer, TaskLayerMixin):
    name = "Grooming"
    task_suffix = ".hair"
    order = 2
    mod_prefix = 'GRM'

    @classmethod
    def handle_new_object(cls, obj: Object, transfer_mapping: AssetTransferMapping):
        if obj.type == 'CURVES':
            surface_object = obj.data.surface
            if surface_object in transfer_mapping.object_map:
                obj.data.surface = transfer_mapping.object_map[surface_object]
        super().handle_new_object(obj, transfer_mapping)

    @classmethod
    def transfer_data(
        cls,
        context: Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: PropertyGroup,
    ) -> None:

        print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

        hair_colls_src, hair_objs_source, _hair_colls_tgt = cls.get_collections(transfer_mapping)

        if not hair_colls_src:
            print(info_text(
                f'No Grooming Task layer collection has been found. Use the suffix {cls.task_suffix} to add one for customized transfer.'))

        cls.handle_new_objects(transfer_mapping)

        # Update hair objects.
        for obj_source, obj_target in transfer_mapping.object_map.items():

            if not obj_source in hair_objs_source:
                continue

            obj_target.matrix_world = obj_source.matrix_world

            if obj_source.type == obj_target.type:
                obj_target.data = obj_source.data
            if obj_target.type == 'CURVES':
                surface_object = obj_source.data.surface
                if surface_object in transfer_mapping.object_map:
                    obj_target.data.surface = transfer_mapping.object_map[surface_object]

            # Sync objects with old particle system.
            if not "PARTICLE_SYSTEM" in [mod.type for mod in obj_source.modifiers]:
                continue
            l = []
            for mod in obj_source.modifiers:
                if not mod.type == "PARTICLE_SYSTEM":
                    l += [mod.show_viewport]
                    mod.show_viewport = False

            bpy.ops.particle.copy_particle_systems(
                {"object": obj_source,
                    "selected_editable_objects": [obj_target]}
            )

            c = 0
            for mod in obj_source.modifiers:
                if mod.type == "PARTICLE_SYSTEM":
                    continue
                mod.show_viewport = l[c]
                c += 1

            prefix_modifiers(obj_source, cls.mod_prefix)
            sync_modifiers(transfer_mapping, obj_source,
                           obj_target, [cls.mod_prefix, 'APL'])
            rebind_modifiers(obj_target)


class ShadingTaskLayer(TaskLayer, TaskLayerMixin):
    name = "Shading"
    task_suffix = ".shading"
    order = 3
    mod_prefix = 'SH'

    @classmethod
    def transfer_data(
        cls,
        context: Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: PropertyGroup,
    ) -> None:
        print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

        cls.handle_new_objects(transfer_mapping)

        for obj_source, obj_target in transfer_mapping.object_map.items():
            if not obj_target.type in ["MESH", "CURVE", "CURVES"]:
                continue

            if obj_target.name.startswith("WGT-"):
                for ms in obj_target.material_slots:
                    ms.material = None
                    # Material slots can only be removed through PyAPI without 
                    # bpy.ops if the material is linked to the object data.
                    ms.link = 'DATA'
                while obj_target.data.materials:
                    obj_target.data.materials.pop()
                continue

            # Transfer material slot assignments.
            # Delete extra material slots of target object.
            while len(obj_target.data.materials) > len(obj_source.data.materials):
                obj_target.data.materials.pop()

            # Transfer material slots.
            for idx in range(len(obj_source.material_slots)):
                if idx >= len(obj_target.material_slots):
                    # Crazily, material slots can only be added through PyAPI without bpy.ops by appending a material to the object data.
                    obj_target.data.materials.append(
                        obj_source.material_slots[idx].material)
                    obj_target.material_slots[idx].material = None
                obj_target.material_slots[idx].link = obj_source.material_slots[idx].link
                obj_target.material_slots[idx].material = obj_source.material_slots[idx].material

            # Transfer active material slot index.
            obj_target.active_material_index = obj_source.active_material_index

            prefix_modifiers(obj_source, cls.mod_prefix)
            sync_modifiers(transfer_mapping, obj_source,
                           obj_target, [cls.mod_prefix, 'APL'])

            if obj_source.type != obj_target.type:
                print(warning_text(
                    f"Mismatching object type. Skipping {obj_target.name}."))
                continue

            # Transfer material slot assignments for curve.
            if obj_target.type == "CURVE":
                if len(obj_target.data.splines) == 0:
                    print(warning_text(
                        f"Curve object '{obj_target.name}' has empty object data"))
                    continue
                for spl_to, spl_from in zip(obj_target.data.splines, obj_source.data.splines):
                    spl_to.material_index = spl_from.material_index

            # Rest of the loop applies only to meshes.
            if obj_target.type != "MESH":
                continue

            obj_target.data.use_auto_smooth = obj_source.data.use_auto_smooth

            if len(obj_target.data.vertices) == 0:
                print(warning_text(
                    f"Mesh object '{obj_target.name}' has empty object data"))
                continue

            topo_match = is_obdata_identical(obj_source, obj_target)
            if not topo_match:  # TODO: Support trivial topology changes in more solid way than proximity transfer
                print(warning_text(
                    f"Mismatch in topology, falling back to proximity transfer. (Object '{obj_target.name}')"))

            # Generate new transfer source object from mesh data.
            obj_source_original = bpy.data.objects.new(
                f"{obj_source.name}.original", obj_source.data)
            context.scene.collection.objects.link(obj_source_original)

            cls.remove_shading_data_from_mesh(obj_target)

            if topo_match:
                cls.transfer_shading_mesh_data_by_topo(obj_source, obj_target)
            else:
                print(warning_text(
                    f"Mismatch in topology, transferring mesh data by proximity: '{obj_target.name}'"))
                cls.transfer_shading_mesh_data_by_proximity(
                    context, obj_source, obj_source_original, obj_target)

            # Make sure correct UV layer is set to active.
            # This is currently broken due to a Blender bug:
            # https://projects.blender.org/blender/blender/issues/104789
            # for uv_l in obj_source.data.uv_layers:
            #     if uv_l.active_render:
            #         obj_target.data.uv_layers[uv_l.name].active_render = True
            #         break

            transfer_all_attributes(
                obj_source, obj_source_original, obj_target, topo_match)

            # Cleanup.
            bpy.data.objects.remove(obj_source_original)

    @staticmethod
    def remove_shading_data_from_mesh(obj_target: Object):
        # Remove UV Layers
        for i in range(len(obj_target.data.uv_layers)):
            try:
                obj_target.data.uv_layers.remove(obj_target.data.uv_layers[0])
            except RuntimeError:
                # This is a Blender bug!! uv_layers.remove() will ALWAYS raise an error, as of 15/Feb/2023.
                # Reported here: https://projects.blender.org/blender/blender/issues/104789
                pass

        # Remove vertex colors
        while len(obj_target.data.vertex_colors) > 0:
            rem = obj_target.data.vertex_colors[0]
            obj_target.data.vertex_colors.remove(rem)


    @staticmethod
    def transfer_shading_mesh_data_by_proximity(
        context: Context,
        obj_source: Object,
        obj_source_original: Object,
        obj_target: Object
    ):
        # Transfer Face Data: Material Index, Smooth
        for pol_target in obj_target.data.polygons:
            (_hit, _loc, _norm, face_index) = obj_source_original.closest_point_on_mesh(
                pol_target.center)
            pol_source = obj_source_original.data.polygons[face_index]
            pol_target.material_index = pol_source.material_index
            pol_target.use_smooth = pol_source.use_smooth

        # Transfer Edge Seams
        bpy.ops.object.data_transfer(
            {
                "object": obj_source_original,
                "active_object": obj_source_original,
                "selected_editable_objects": [obj_target],
            },
            data_type="SEAM",
            edge_mapping="NEAREST",
            mix_mode="REPLACE",
        )

        # Transfer UV layers
        for uv_from in obj_source.data.uv_layers:
            uv_to = obj_target.data.uv_layers.new(name=uv_from.name, do_init=False)
            transfer_corner_data(obj_source, obj_target,
                                uv_from.data, uv_to.data, data_suffix='uv')

        # Transfer Vertex Colors
        for vcol_from in obj_source.data.vertex_colors:
            vcol_to = obj_target.data.vertex_colors.new(
                name=vcol_from.name, do_init=False)
            transfer_corner_data(obj_source, obj_target,
                                vcol_from.data, vcol_to.data, data_suffix='color')


    @staticmethod
    def transfer_shading_mesh_data_by_topo(obj_source: Object, obj_target: Object):
        # Transfer face data
        for pol_to, pol_from in zip(obj_target.data.polygons, obj_source.data.polygons):
            pol_to.material_index = pol_from.material_index
            pol_to.use_smooth = pol_from.use_smooth

        # Transfer Edge Data
        for edge_from, edge_to in zip(obj_source.data.edges, obj_target.data.edges):
            edge_to.use_seam = edge_from.use_seam

        # Transfer UV layers
        for uv_from in obj_source.data.uv_layers:
            uv_to = obj_target.data.uv_layers.new(name=uv_from.name, do_init=False)
            for loop in obj_target.data.loops:
                uv_to.data[loop.index].uv = uv_from.data[loop.index].uv

        # Transfer Vertex Colors
        for vcol_from in obj_source.data.vertex_colors:
            vcol_to = obj_target.data.vertex_colors.new(
                name=vcol_from.name, do_init=False)
            for loop in obj_target.data.loops:
                vcol_to.data[loop.index].color = vcol_from.data[loop.index].color


# Mesh Data Comparison.

def is_mesh_identical(mesh_a, mesh_b) -> bool:
    if len(mesh_a.vertices) != len(mesh_b.vertices):
        return False
    if len(mesh_a.edges) != len(mesh_b.edges):
        return False
    if len(mesh_a.polygons) != len(mesh_b.polygons):
        return False
    for e1, e2 in zip(mesh_a.edges, mesh_b.edges):
        for v1, v2 in zip(e1.vertices, e2.vertices):
            if v1 != v2:
                return False

    return True


def is_curve_identical(curve_a: Curve, curve_b: Curve) -> bool:
    if len(curve_a.splines) != len(curve_b.splines):
        return False
    for spline1, spline2 in zip(curve_a.splines, curve_b.splines):
        if len(spline1.points) != len(spline2.points):
            return False
    return True


def is_obdata_identical(
    a: Object or Mesh,
    b: Object or Mesh
) -> bool:
    """Checks if two objects have matching topology (efficiency over exactness)"""
    if type(a) == Object:
        a = a.data
    if type(b) == Object:
        b = b.data

    if type(a) != type(b):
        return False

    if type(a) == Mesh:
        return is_mesh_identical(a, b)
    elif type(a) == Curve:
        return is_curve_identical(a, b)
    else:
        # TODO: Support geometry types other than mesh or curve.
        return


# Generic Attribute Transfer.

def transfer_all_attributes(
    obj_source: Object,
    obj_source_original: Object,
    obj_target: Object,
    topo_match: bool
):
    # Transfer Generic Attributes
    # TODO: Split up ownership of generic attributes for all task layers
    if not obj_source.type == 'MESH':
        # TODO: support other geometry types
        return
    
    def get_non_internal_attributes(obj: Object):
        """Return an iterable of removable/transferrable attributes."""
        for attr in obj.data.attributes:
            if attr.name.startswith('.') or attr.name == 'position':
                continue
            yield attr

    for attr in reversed(list(get_non_internal_attributes(obj_target))):
        attr_name = attr.name
        try:
            obj_target.data.attributes.remove(attr)
        except RuntimeError:
            # Some built-in attributes like "position" cannot be removed...
            print("Attribute cannot be removed: ", attr_name)
            continue

    for attr in get_non_internal_attributes(obj_source):
        transfer_single_attribute(
            obj_source_original, obj_target, attr, topo_match=topo_match)


def transfer_single_attribute(
    obj_source: Object,
    obj_target: Object,
    src_attr: Attribute,
    topo_match: bool
):
    src_dat = obj_source.data
    tgt_dat = obj_target.data
    if type(src_dat) is not type(tgt_dat) or not (src_dat or tgt_dat):
        return False
    if type(tgt_dat) is not Mesh:  # TODO: support more types
        return False

    # If target attribute already exists, remove it.
    tgt_attr = tgt_dat.attributes.get(src_attr.name)
    if tgt_attr is not None:
        try:
            tgt_dat.attributes.remove(tgt_attr)
        except RuntimeError:
            # Built-ins like "position" cannot be removed, and should be skipped.
            return

    # Create target attribute.
    tgt_attr = tgt_dat.attributes.new(
        src_attr.name, src_attr.data_type, src_attr.domain)

    data_sfx = {'INT8': 'value',
                'INT': 'value',
                'FLOAT': 'value',
                'FLOAT2': 'vector',
                'BOOLEAN': 'value',
                'STRING': 'value',
                'BYTE_COLOR': 'color',
                'FLOAT_COLOR': 'color',
                'FLOAT_VECTOR': 'vector'}

    data_sfx = data_sfx[src_attr.data_type]

    if topo_match:
        # TODO: optimize using foreach_get/set rather than loop
        for i in range(len(src_attr.data)):
            setattr(tgt_attr.data[i], data_sfx,
                    getattr(src_attr.data[i], data_sfx))
        return

    # proximity fallback
    if src_attr.data_type == 'STRING':
        # TODO: add NEAREST transfer fallback for attributes without interpolation
        print(error_text(
            f'Proximity based transfer for generic attributes of type STRING not supported yet. Skipping attribute {src_attr.name} on {obj_target}.'))
        return

    domain = src_attr.domain
    if domain == 'POINT':  # TODO: deduplicate interpolated point domain proximity transfer
        bm_source = bmesh.new()
        bm_source.from_mesh(obj_source.data)
        bm_source.faces.ensure_lookup_table()

        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

        tris_dict = tris_per_face(bm_source)

        for i, vert in enumerate(obj_target.data.vertices):
            p = vert.co
            face = closest_face_to_point(bm_source, p, bvh_tree)

            (tri, point) = closest_tri_on_face(tris_dict, face, p)
            if not tri:
                continue
            weights = mathutils.interpolate.poly_3d_calc(
                [tri[i].vert.co for i in range(3)], point)

            if data_sfx in ['color']:
                vals_weighted = [
                    weights[i]*(np.array(getattr(src_attr.data[tri[i].vert.index], data_sfx))) for i in range(3)]
            else:
                vals_weighted = [
                    weights[i]*(getattr(src_attr.data[tri[i].vert.index], data_sfx)) for i in range(3)]
            setattr(tgt_attr.data[i], data_sfx, sum(np.array(vals_weighted)))
        return
    elif domain == 'EDGE':
        # TODO support proximity fallback for generic edge attributes
        print(error_text(
            f'Proximity based transfer of generic edge attributes not supported yet. Skipping attribute {src_attr.name} on {obj_target}.'))
        return
    elif domain == 'FACE':
        bm_source = bmesh.new()
        bm_source.from_mesh(obj_source.data)
        bm_source.faces.ensure_lookup_table()

        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)
        for i, face in enumerate(obj_target.data.polygons):
            p_target = face.center
            closest_face = closest_face_to_point(bm_source, p_target, bvh_tree)
            setattr(tgt_attr.data[i], data_sfx, getattr(
                src_attr.data[closest_face.index], data_sfx))
        return
    elif domain == 'CORNER':
        transfer_corner_data(obj_source, obj_target,
                             src_attr.data, tgt_attr.data, data_suffix=data_sfx)
        return


# Text Utilities.

def info_text(text: str) -> str:
    return f"\t\033[1mInfo\033[0m\t: "+text


def warning_text(text: str) -> str:
    return f"\t\033[1m\033[93mWarning\033[0m\t: "+text


def error_text(text: str) -> str:
    return f"\t\033[1m\033[91mError\033[0m\t: "+text


# Modifier Utilities.

def prefix_modifiers(obj: Object, prefix: str, delimiter='-') -> None:
    prefixes = ['RIG', 'GEO', 'APL', 'GRM', 'SH']
    if prefix not in prefixes:
        print(warning_text(
            f"Prefix '{prefix}' is unknown. Prefixing modifiers might fail."))
    for mod in obj.modifiers:
        if not mod.name.split(delimiter)[0] in prefixes:
            mod.name = f'{prefix}{delimiter}{mod.name}'


def rebind_modifiers(object: Object):
    """Un-bind and re-bind modifiers that require bind data."""
    # TODO: This should only be necessary if either this object or the modifier's
    # target object has changed in vertex count.
    return
    for mod in object.modifiers:
        if "NOREBIND" in mod.name or not mod.show_viewport:
            continue
        if mod.type == 'SURFACE_DEFORM':
            if not mod.is_bound:
                continue
            for i in range(2):
                bpy.ops.object.surfacedeform_bind(
                    {"object": object, "active_object": object}, modifier=mod.name)
        elif mod.type == 'MESH_DEFORM':
            if not mod.is_bound:
                continue
            for i in range(2):
                bpy.ops.object.meshdeform_bind(
                    {"object": object, "active_object": object}, modifier=mod.name)
        elif mod.type == 'CORRECTIVE_SMOOTH':
            if not mod.is_bind:
                continue
            for i in range(2):
                bpy.ops.object.correctivesmooth_bind(
                    {"object": object, "active_object": object}, modifier=mod.name)


def sync_modifiers(
    transfer_mapping: AssetTransferMapping,
    obj_source: Object,
    obj_target: Object,
    transfer_prefixes: list[str],
    delimiter: str = '-'
):
    """Sync modifier stack. Those without prefix on the source are added and prefixed, 
    those with matching/other prefix are synced/ignored based on their prefix."""

    # Remove old and sync existing modifiers.
    for mod in obj_target.modifiers:
        if mod.name.split('-')[0] not in transfer_prefixes:
            continue
        if mod.name not in [m.name for m in obj_source.modifiers]:
            print(info_text(f"Removing modifier {mod.name}"))
            obj_target.modifiers.remove(mod)

    # Transfer new modifiers.
    for i, mod in enumerate(obj_source.modifiers):
        if mod.name.split(delimiter)[0] not in transfer_prefixes:
            continue
        if mod.name in [m.name for m in obj_target.modifiers]:
            continue
        mod_new = obj_target.modifiers.new(mod.name, mod.type)
        
        # Sort new modifier at correct index (default to beginning of the stack).
        idx = 0
        if i > 0:
            name_prev = obj_source.modifiers[i-1].name
            for target_mod_i, target_mod in enumerate(obj_target.modifiers):
                if target_mod.name == name_prev:
                    idx = target_mod_i+1
        with bpy.context.temp_override(object=obj_target):
            bpy.ops.object.modifier_move_to_index(modifier=mod_new.name, index=idx)

    # Sync modifier settings.
    for i, mod_source in enumerate(obj_source.modifiers):
        mod_target = obj_target.modifiers.get(mod_source.name)
        if not mod_target:
            continue
        if mod_source.name.split(delimiter)[0] not in transfer_prefixes:
            continue
        for prop in [p.identifier for p in mod_source.bl_rna.properties if not p.is_readonly]:
            value = getattr(mod_source, prop)
            if type(value) == Object and value in transfer_mapping.object_map:
                # If a modifier is referencing a .TASK object,
                # remap that reference to a .TARGET object.
                # (Eg. modeling Mirror modifier with a mirror object)
                value = transfer_mapping.object_map[value]
            setattr(mod_target, prop, value)

        # For geometry nodes modifiers: transfer inputs (TODO: fix pointers)
        if not mod_target.type == 'NODES':
            continue
        for k in list(mod_source.keys()):
            value = mod_source[k]
            if type(value) == bpy.types.Object and value in transfer_mapping.object_map:
                value = transfer_mapping.object_map[value]
                mod_target[k] = value
            else:
                mod_target[k] = value


# Object Properties Utilities.

def copy_parenting(source_ob: Object, target_ob: Object) -> None:
    """Copy parenting data from source to target object."""
    target_ob.parent = source_ob.parent
    target_ob.parent_type = source_ob.parent_type
    target_ob.parent_bone = source_ob.parent_bone
    target_ob.matrix_parent_inverse = source_ob.matrix_parent_inverse.copy()


def copy_transforms(source_ob: Object, target_ob: Object):
    """Copy transforms properties from source to target object."""
    target_ob.rotation_mode = source_ob.rotation_mode
    target_ob.rotation_euler = source_ob.rotation_euler.copy()
    target_ob.rotation_quaternion = source_ob.rotation_quaternion.copy()
    target_ob.location = source_ob.location.copy()
    target_ob.scale = source_ob.scale.copy()


def copy_attributes(a: Any, b: Any) -> None:
    keys = dir(a)
    for key in keys:
        if (
            not key.startswith("_")
            and not key.startswith("error_")
            and key not in ['group', 'is_valid', 'rna_type', 'bl_rna']
        ):
            try:
                setattr(b, key, getattr(a, key))
            except AttributeError:
                pass


def copy_driver(
    source_fcurve: FCurve,
    target_obj: Object,
    data_path: Optional[str] = None,
    index: Optional[int] = None,
) -> FCurve:
    if not data_path:
        data_path = source_fcurve.data_path

    new_fc = None
    try:
        if index:
            new_fc = target_obj.driver_add(data_path, index)
        else:
            new_fc = target_obj.driver_add(data_path)
    except:
        print(warning_text(
            f"Couldn't copy driver {source_fcurve.data_path} to {target_obj.name}"))
        return

    copy_attributes(source_fcurve, new_fc)
    copy_attributes(source_fcurve.driver, new_fc.driver)

    # Remove default curve modifiers and driver variables.
    for m in new_fc.modifiers:
        new_fc.modifiers.remove(m)
    for v in new_fc.driver.variables:
        new_fc.driver.variables.remove(v)

    # Copy curve modifiers.
    for m1 in source_fcurve.modifiers:
        m2 = new_fc.modifiers.new(type=m1.type)
        copy_attributes(m1, m2)

    # Copy driver variables.
    for v1 in source_fcurve.driver.variables:
        v2 = new_fc.driver.variables.new()
        copy_attributes(v1, v2)
        for i in range(len(v1.targets)):
            copy_attributes(v1.targets[i], v2.targets[i])

    return new_fc


def copy_drivers(source_ob: Object, target_ob: Object) -> None:
    """Copy all drivers from one object to another."""
    if not hasattr(source_ob, "animation_data") or not source_ob.animation_data:
        return

    for fc in source_ob.animation_data.drivers:
        copy_driver(fc, target_ob)


def copy_rigging_object_data(
    source_ob: Object, target_ob: Object
) -> None:
    """Copy all object data that could be relevant to rigging."""
    # TODO: Object constraints, if needed.
    copy_drivers(source_ob, target_ob)
    copy_parenting(source_ob, target_ob)
    # HACK: For some reason Armature constraints on grooming objects lose their target when updating? Very strange...
    for con in target_ob.constraints:
        if con.type == "ARMATURE":
            for tgt in con.targets:
                if tgt.target == None:
                    tgt.target = target_ob.parent


### Mesh interpolation utilities.

def edge_data_split(edge, data_layer, data_suffix: str):
    for vert in edge.verts:
        vals = []
        for loop in vert.link_loops:
            loops_edge_vert = set(
                [loop for f in edge.link_faces for loop in f.loops])
            if loop not in loops_edge_vert:
                continue
            dat = data_layer[loop.index]
            element = list(getattr(dat, data_suffix))
            if not vals:
                vals.append(element)
            elif not vals[0] == element:
                vals.append(element)
        if len(vals) > 1:
            return True
    return False


def closest_edge_on_face_to_line(face, p1, p2, skip_edges=None):
    """Returns edge of a face which is closest to line."""
    for edge in face.edges:
        if skip_edges:
            if edge in skip_edges:
                continue
        res = mathutils.geometry.intersect_line_line(
            p1, p2, *[edge.verts[i].co for i in range(2)])
        if not res:
            continue
        (p_traversal, p_edge) = res
        frac_1 = (edge.verts[1].co-edge.verts[0].co).dot(p_edge -
                                                         edge.verts[0].co)/(edge.verts[1].co-edge.verts[0].co).length**2.
        frac_2 = (p2-p1).dot(p_traversal-p1)/(p2-p1).length**2.
        if (frac_1 >= 0 and frac_1 <= 1) and (frac_2 >= 0 and frac_2 <= 1):
            return edge
    return None


def interpolate_data_from_face(bm_source, tris_dict, face, p, data_layer_source, data_suffix=''):
    """Returns interpolated value of a data layer within a face closest to a point."""

    (tri, point) = closest_tri_on_face(tris_dict, face, p)
    if not tri:
        return None
    weights = mathutils.interpolate.poly_3d_calc(
        [tri[i].vert.co for i in range(3)], point)

    if not data_suffix:
        cols_weighted = [
            weights[i]*np.array(data_layer_source[tri[i].index]) for i in range(3)]
        col = sum(np.array(cols_weighted))
    else:
        cols_weighted = [
            weights[i]*np.array(getattr(data_layer_source[tri[i].index], data_suffix)) for i in range(3)]
        col = sum(np.array(cols_weighted))
    return col


def closest_face_to_point(bm_source, p_target, bvh_tree=None):
    if not bvh_tree:
        bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)
    (loc, norm, index, distance) = bvh_tree.find_nearest(p_target)
    return bm_source.faces[index]


def tris_per_face(bm_source):
    tris_source = bm_source.calc_loop_triangles()
    tris_dict = dict()
    for face in bm_source.faces:
        tris_face = []
        for i in range(len(tris_source))[::-1]:
            if tris_source[i][0] in face.loops:
                tris_face.append(tris_source.pop(i))
        tris_dict[face] = tris_face
    return tris_dict


def closest_tri_on_face(tris_dict, face, p):
    points = []
    dist = []
    tris = []
    for tri in tris_dict[face]:
        point = mathutils.geometry.closest_point_on_tri(
            p, *[tri[i].vert.co for i in range(3)])
        tris.append(tri)
        points.append(point)
        dist.append((point-p).length)
    min_idx = np.argmin(np.array(dist))
    point = points[min_idx]
    tri = tris[min_idx]
    return (tri, point)


def transfer_corner_data(obj_source, obj_target, data_layer_source, data_layer_target, data_suffix=''):
    """
    Transfers interpolated face corner data from data layer of a source object to data layer of a
    target object, while approximately preserving data seams (e.g. necessary for UV Maps).
    The transfer is face interpolated per target corner within the source face that is closest
    to the target corner point and does not have any data seams on the way back to the
    source face that is closest to the target face's center.
    """

    bm_source = bmesh.new()
    bm_source.from_mesh(obj_source.data)
    bm_source.faces.ensure_lookup_table()
    bm_target = bmesh.new()
    bm_target.from_mesh(obj_target.data)
    bm_target.faces.ensure_lookup_table()

    bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

    tris_dict = tris_per_face(bm_source)

    for face_target in bm_target.faces:
        face_target_center = face_target.calc_center_median()

        face_source = closest_face_to_point(
            bm_source, face_target_center, bvh_tree)

        for corner_target in face_target.loops:
            # find nearest face on target compared to face that loop belongs to
            p = corner_target.vert.co

            face_source_closest = closest_face_to_point(bm_source, p, bvh_tree)
            enclosed = face_source_closest is face_source
            face_source_int = face_source
            if not enclosed:
                # traverse faces between point and face center
                traversed_faces = set()
                traversed_edges = set()
                while (face_source_int is not face_source_closest):
                    traversed_faces.add(face_source_int)
                    edge = closest_edge_on_face_to_line(
                        face_source_int, face_target_center, p, skip_edges=traversed_edges)
                    if edge == None:
                        break
                    if len(edge.link_faces) != 2:
                        break
                    traversed_edges.add(edge)

                    split = edge_data_split(
                        edge, data_layer_source, data_suffix)
                    if split:
                        break

                    # set new source face to other face belonging to edge
                    face_source_int = edge.link_faces[1] if edge.link_faces[
                        1] is not face_source_int else edge.link_faces[0]

                    # avoid looping behaviour
                    if face_source_int in traversed_faces:
                        face_source_int = face_source
                        break

            # interpolate data from selected face
            col = interpolate_data_from_face(
                bm_source, tris_dict, face_source_int, p, data_layer_source, data_suffix)
            if col is None:
                continue
            if not data_suffix:
                data_layer_target.data[corner_target.index] = col
            else:
                setattr(
                    data_layer_target[corner_target.index], data_suffix, list(col))
    return


def transfer_shapekeys_proximity(obj_source, obj_target, skip_prefix=None) -> None:
    """Transfers shapekeys from one object to another based on the mesh proximity 
    with face interpolation."""
    # copy shapekey layout
    if not obj_source.data.shape_keys:
        return
    for sk_source in obj_source.data.shape_keys.key_blocks:
        if obj_target.data.shape_keys:
            if skip_prefix:
                if sk_source.name.split('-')[0] == skip_prefix:
                    continue
            sk_target = obj_target.data.shape_keys.key_blocks.get(
                sk_source.name)
            if sk_target:
                continue
        sk_target = obj_target.shape_key_add()
        sk_target.name = sk_source.name
    for sk_target in obj_target.data.shape_keys.key_blocks:
        if skip_prefix:
            if sk_target.name.split('-')[0] == skip_prefix:
                continue
        sk_source = obj_source.data.shape_keys.key_blocks[sk_target.name]
        sk_target.vertex_group = sk_source.vertex_group
        sk_target.relative_key = obj_target.data.shape_keys.key_blocks[
            sk_source.relative_key.name]

    bm_source = bmesh.new()
    bm_source.from_mesh(obj_source.data)
    bm_source.faces.ensure_lookup_table()

    bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

    tris_dict = tris_per_face(bm_source)

    for i, vert in enumerate(obj_target.data.vertices):
        p = vert.co
        face = closest_face_to_point(bm_source, p, bvh_tree)

        (tri, point) = closest_tri_on_face(tris_dict, face, p)
        if not tri:
            continue
        weights = mathutils.interpolate.poly_3d_calc(
            [tri[i].vert.co for i in range(3)], point)

        for sk_target in obj_target.data.shape_keys.key_blocks:
            if skip_prefix:
                if sk_target.name.split('-')[0] == skip_prefix:
                    continue
            sk_source = obj_source.data.shape_keys.key_blocks.get(
                sk_target.name)

            vals_weighted = [weights[i]*(sk_source.data[tri[i].vert.index].co -
                                         obj_source.data.vertices[tri[i].vert.index].co) for i in range(3)]
            val = mathutils.Vector(sum(np.array(vals_weighted)))
            sk_target.data[i].co = vert.co+val
