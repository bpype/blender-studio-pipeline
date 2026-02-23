# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bmesh
import bpy
import mathutils
import numpy as np


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
        point = mathutils.geometry.closest_point_on_tri(p, *[tri[i].vert.co for i in range(3)])
        tris.append(tri)
        points.append(point)
        dist.append((point - p).length)
    min_idx = np.argmin(np.array(dist))
    point = points[min_idx]
    tri = tris[min_idx]
    return (tri, point)


def closest_edge_on_face_to_line(face, p1, p2, skip_edges=None):
    """Returns edge of a face which is closest to line."""
    for edge in face.edges:
        if skip_edges:
            if edge in skip_edges:
                continue
        res = mathutils.geometry.intersect_line_line(p1, p2, *[edge.verts[i].co for i in range(2)])
        if not res:
            continue
        (p_traversal, p_edge) = res
        frac_1 = (edge.verts[1].co - edge.verts[0].co).dot(p_edge - edge.verts[0].co) / (
            edge.verts[1].co - edge.verts[0].co
        ).length ** 2.0
        frac_2 = (p2 - p1).dot(p_traversal - p1) / (p2 - p1).length ** 2.0
        if (frac_1 >= 0 and frac_1 <= 1) and (frac_2 >= 0 and frac_2 <= 1):
            return edge
    return None


def edge_data_split(edge, data_layer, data_suffix: str):
    for vert in edge.verts:
        vals = []
        for loop in vert.link_loops:
            loops_edge_vert = set([loop for f in edge.link_faces for loop in f.loops])
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


def interpolate_data_from_face(bm_source, tris_dict, face, p, data_layer_source, data_suffix=''):
    """Returns interpolated value of a data layer within a face closest to a point."""

    (tri, point) = closest_tri_on_face(tris_dict, face, p)
    if not tri:
        return None
    weights = mathutils.interpolate.poly_3d_calc([tri[i].vert.co for i in range(3)], point)

    if not data_suffix:
        cols_weighted = [weights[i] * np.array(data_layer_source[tri[i].index]) for i in range(3)]
        col = sum(np.array(cols_weighted))
    else:
        cols_weighted = [weights[i] * np.array(getattr(data_layer_source[tri[i].index], data_suffix)) for i in range(3)]
        col = sum(np.array(cols_weighted))
    return col


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

        face_source = closest_face_to_point(bm_source, face_target_center, bvh_tree)

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
                while face_source_int is not face_source_closest:
                    traversed_faces.add(face_source_int)
                    edge = closest_edge_on_face_to_line(
                        face_source_int,
                        face_target_center,
                        p,
                        skip_edges=traversed_edges,
                    )
                    if edge == None:
                        break
                    if len(edge.link_faces) != 2:
                        break
                    traversed_edges.add(edge)

                    split = edge_data_split(edge, data_layer_source, data_suffix)
                    if split:
                        break

                    # set new source face to other face belonging to edge
                    face_source_int = (
                        edge.link_faces[1] if edge.link_faces[1] is not face_source_int else edge.link_faces[0]
                    )

                    # avoid looping behaviour
                    if face_source_int in traversed_faces:
                        face_source_int = face_source
                        break

            # interpolate data from selected face
            col = interpolate_data_from_face(bm_source, tris_dict, face_source_int, p, data_layer_source, data_suffix)
            if col is None:
                continue
            if not data_suffix:
                data_layer_target.data[corner_target.index] = col
            else:
                setattr(data_layer_target[corner_target.index], data_suffix, list(col))
    return


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


def is_curve_identical(curve_a: bpy.types.Curve, curve_b: bpy.types.Curve) -> bool:
    if len(curve_a.splines) != len(curve_b.splines):
        return False
    for spline1, spline2 in zip(curve_a.splines, curve_b.splines):
        if len(spline1.points) != len(spline2.points):
            return False
    return True


def is_obdata_identical(a: bpy.types.Object or bpy.types.Mesh, b: bpy.types.Object or bpy.types.Mesh) -> bool:
    """Checks if two objects have matching topology (efficiency over exactness)"""
    if type(a) == bpy.types.Object:
        a = a.data
    if type(b) == bpy.types.Object:
        b = b.data

    if type(a) != type(b):
        return False

    if type(a) == bpy.types.Mesh:
        return is_mesh_identical(a, b)
    elif type(a) == bpy.types.Curve:
        return is_curve_identical(a, b)
    else:
        # TODO: Support geometry types other than mesh or curve.
        return
