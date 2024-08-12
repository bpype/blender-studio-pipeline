# SPDX-License-Identifier: GPL-2.0-or-later

from collections import defaultdict
import bpy
import sys
import itertools

from bpy.props import IntProperty, CollectionProperty, StringProperty, BoolProperty
from bpy.types import PropertyGroup, Panel, UIList, Operator, Mesh, VertexGroup, MeshVertex, Object
from bpy.utils import flip_name

from .utils import get_deforming_vgroups, poll_deformed_mesh_with_vgroups

"""
This module implements the Sidebar -> EasyWeight -> Weight Islands panel, which provides
a workflow for hunting down and cleaning up rogue weights efficiently.
"""


class VertIndex(PropertyGroup):
    index: IntProperty()


class WeightIsland(PropertyGroup):
    vert_indicies: CollectionProperty(type=VertIndex)


class IslandGroup(PropertyGroup):
    name: StringProperty(
        name="Name", description="Name of the vertex group this set of islands is associated with"
    )
    islands: CollectionProperty(type=WeightIsland)
    num_expected_islands: IntProperty(
        name="Expected Islands",
        default=1,
        min=1,
        description="Number of weight islands that have been marked as the expected amount by the user. If the real amount differs from this value, a warning appears",
    )
    index: IntProperty()


def update_vgroup_islands(
    mesh, vgroup, vert_index_map, island_groups, island_group=None
) -> IslandGroup:
    islands = get_islands_of_vgroup(mesh, vgroup, vert_index_map)

    if not island_group:
        island_group = island_groups.add()
        island_group.index = len(island_groups) - 1
        island_group.name = vgroup.name
    else:
        island_group.islands.clear()
    for island in islands:
        island_storage = island_group.islands.add()
        for vert_idx in island:
            vert_idx_storage = island_storage.vert_indicies.add()
            vert_idx_storage.index = vert_idx

    return island_group


def build_vert_connection_map_new(mesh) -> dict:
    """Build a dictionary of vertex indicies pointing to a list of other vertex indicies
    that the vertex is connected to by an edge.
    """

    vert_dict = defaultdict(list)

    for edge in mesh.edges:
        vert_dict[edge.vertices[0]] += [edge.vertices[1]]
        vert_dict[edge.vertices[1]] += [edge.vertices[0]]

    return vert_dict


def find_weight_island_vertices(
    mesh: Mesh, vert_idx: int, group_index: int, vert_idx_map: dict, island=[]
) -> list[int]:
    """Recursively find all vertices that are connected to a vertex by edges,
    and are also in the same vertex group.

    Recursion depth may exceed system default on high poly meshes.
    """

    island.append(vert_idx)
    # For each edge connected to the vert.
    for connected_vert_idx in vert_idx_map[vert_idx]:
        if connected_vert_idx in island:
            # Avoid infinite recursion!
            continue
        # For each group this other vertex belongs to.
        for group_data in mesh.vertices[connected_vert_idx].groups:
            if group_data.group == group_index and group_data.weight:
                # If this vert is in the group, continue recursion.
                find_weight_island_vertices(
                    mesh, connected_vert_idx, group_index, vert_idx_map, island
                )
    return island


def find_any_vertex_in_group(mesh: Mesh, vgroup: VertexGroup, excluded_indicies=[]) -> MeshVertex:
    """Return the index of the first vertex we find which is part of the
    vertex group and optinally, has a specified selection state."""

    # TODO: This is probably our performance bottleneck atm.
    # We should build an acceleration structure for this similar to build_vert_connection_map_new,
    # to map each vertex group to all of the verts within it, so we only need to iterate
    # like this once.

    for vert in mesh.vertices:
        if vert.index in excluded_indicies:
            continue
        for group in vert.groups:
            if vgroup.index == group.group:
                return vert
    return None


def get_islands_of_vgroup(mesh: Mesh, vgroup: VertexGroup, vert_index_map: dict) -> list[list[int]]:
    """Return a list of lists of vertex indicies: Weight islands within this vertex group."""
    islands = []
    while True:
        verts_already_part_of_an_island = set(itertools.chain.from_iterable(islands))
        any_vert_in_group = find_any_vertex_in_group(
            mesh, vgroup, excluded_indicies=verts_already_part_of_an_island
        )
        if not any_vert_in_group:
            break
        # NOTE: We could avoid recursion here by doing the expansion in a `while True` block,
        # and break if the current list of verts is the same as at the end of the last loop.
        # But I'm fine with just changing the recursion limit.
        sys.setrecursionlimit(len(mesh.vertices))
        island = find_weight_island_vertices(
            mesh, any_vert_in_group.index, vgroup.index, vert_index_map, island=[]
        )
        sys.setrecursionlimit(990)
        islands.append(island)
    return islands


def select_vertices(mesh: Mesh, vert_indicies: list[int]):
    assert (
        bpy.context.mode != 'EDIT_MESH'
    ), "Object must not be in edit mode, otherwise vertex selection doesn't work!"

    for i, vert in enumerate(mesh.vertices):
        vert.select = i in vert_indicies
        vert.hide = False


def ensure_active_islands_is_visible(obj):
    """Make sure the active entry is visible, keep incrementing index until that is the case."""
    new_active_index = obj.active_islands_index + 1
    looped = False
    while True:
        if new_active_index >= len(obj.island_groups):
            new_active_index = 0
            if looped:
                break
            looped = True
        island_group = obj.island_groups[new_active_index]
        if (
            len(island_group.islands) < 2
            or len(island_group.islands) == island_group.num_expected_islands
        ):
            new_active_index += 1
            continue
        break
    obj.active_islands_index = new_active_index


class EASYWEIGHT_OT_mark_island_as_okay(Operator):
    """Mark this number of vertex islands to be the intended amount. Vertex group will be hidden from the list until this number changes"""

    bl_idname = "object.set_expected_island_count"
    bl_label = "Set Intended Island Count"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    vgroup: StringProperty(
        name="Vertex Group",
        default="",
        description="Name of the vertex group whose intended island count will be set",
    )

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        org_mode = obj.mode

        assert (
            self.vgroup in obj.island_groups
        ), f"Island Group {self.vgroup} not found in object {obj.name}, aborting."

        # Update existing island data first
        island_group = obj.island_groups[self.vgroup]
        vgroup = obj.vertex_groups[self.vgroup]
        bpy.ops.object.mode_set(mode='EDIT')
        vert_index_map = build_vert_connection_map_new(mesh)
        bpy.ops.object.mode_set(mode=org_mode)
        org_num_islands = len(island_group.islands)
        island_group = update_vgroup_islands(
            mesh, vgroup, vert_index_map, obj.island_groups, island_group
        )
        new_num_islands = len(island_group.islands)
        if new_num_islands != org_num_islands:
            if new_num_islands == 1:
                self.report(
                    {'INFO'},
                    f"Vertex group is now a single island, changing expected island count no longer necessary.",
                )
                return {'FINISHED'}
            self.report(
                {'INFO'},
                f"Vertex group island count changed from {org_num_islands} to {new_num_islands}. Click again to mark this as the expected number.",
            )
            return {'FINISHED'}

        island_group.num_expected_islands = new_num_islands
        ensure_active_islands_is_visible(obj)
        return {'FINISHED'}


class EASYWEIGHT_OT_focus_smallest_island(Operator):
    """Enter Weight Paint mode and focus on the smallest island"""

    bl_idname = "object.focus_smallest_weight_island"
    bl_label = "Focus Smallest Island"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    enter_wp: BoolProperty(
        name="Enter Weight Paint",
        default=True,
        description="Enter Weight Paint Mode using the Toggle Weight Paint operator",
    )
    vgroup: StringProperty(
        name="Vertex Group",
        default="",
        description="Name of the vertex group whose smallest island should be focused",
    )
    focus_view: BoolProperty(
        name="Focus View",
        default=True,
        description="Whether to focus the 3D Viewport on the selected vertices",
    )

    def execute(self, context):
        rig = context.pose_object
        obj = context.active_object
        mesh = obj.data
        org_mode = obj.mode

        assert (
            self.vgroup in obj.vertex_groups
        ), f"Vertex Group {self.vgroup} not found in object {obj.name}, aborting."

        # Also update the opposite side vertex group.
        vgroup_names = [self.vgroup]
        flipped = flip_name(self.vgroup)
        if flipped != self.vgroup:
            vgroup_names.append(flipped)

        vert_index_map = build_vert_connection_map_new(mesh)
        bpy.ops.object.mode_set(mode=org_mode)
        hid_islands = False
        for vg_name in vgroup_names:
            if vg_name in obj.island_groups:
                # Update existing island data first.
                island_group = obj.island_groups[vg_name]
                vgroup = obj.vertex_groups[vg_name]
                org_num_islands = len(island_group.islands)
                island_group = update_vgroup_islands(
                    mesh, vgroup, vert_index_map, obj.island_groups, island_group
                )
                new_num_islands = len(island_group.islands)
                if new_num_islands < 2 and org_num_islands > 1:
                    hid_islands = True
                    self.report(
                        {'INFO'},
                        f"Vertex group {vg_name} no longer has multiple islands, hidden from list.",
                    )
        if hid_islands:
            ensure_active_islands_is_visible(obj)
            return {'FINISHED'}
            # self.report({'INFO'}, f"Vertex group island count changed from {org_num_islands} to {new_num_islands}. Click again to focus smallest island.")
            # return {'FINISHED'}

        island_groups = obj.island_groups
        island_group = island_groups[self.vgroup]
        vgroup = obj.vertex_groups[self.vgroup]
        obj.active_islands_index = island_group.index

        smallest_island = min(island_group.islands, key=lambda island: len(island.vert_indicies))
        select_vertices(mesh, [vi.index for vi in smallest_island.vert_indicies])

        # NOTE: Unfortunately these mode switches introduce some lag.
        # Especially because the weight paint switch triggers mode_switch_hook,
        # which causes more mode switches to put the Armature into pose mode.

        if self.focus_view:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.view3d.view_selected()

        if self.enter_wp:
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        else:
            bpy.ops.object.mode_set(mode=org_mode)

        # Select the bone
        if context.mode == 'PAINT_WEIGHT':
            rig = context.pose_object
            if rig:
                for pb in rig.pose.bones:
                    pb.bone.select = False
                if self.vgroup in rig.pose.bones:
                    rig.pose.bones[self.vgroup].bone.select = True

        mesh.use_paint_mask_vertex = True

        self.report({'INFO'}, "Focused on the smallest island of weights.")
        return {'FINISHED'}


class EASYWEIGHT_OT_calculate_weight_islands(Operator):
    """Calculate and store number of weight islands for each deforming vertex group. Groups with more than one island will be displayed below"""

    bl_idname = "object.calculate_weight_islands"
    bl_label = "Calculate Weight Islands"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @staticmethod
    def store_all_weight_islands(context, obj: Object, vert_index_map: dict):
        """Store the weight island information of every deforming vertex group."""
        wm = context.window_manager

        mesh = obj.data
        island_groups = obj.island_groups
        island_groups.clear()
        obj.active_islands_index = 0
        vgroups = get_deforming_vgroups(obj)
        wm.progress_begin(0, len(vgroups))
        for i, vgroup in enumerate(vgroups):
            if 'skip_groups' in obj and vgroup.name in obj['skip_groups']:
                continue
            obj.vertex_groups.active_index = vgroup.index

            update_vgroup_islands(mesh, vgroup, vert_index_map, island_groups)
            wm.progress_update(i)
        wm.progress_end()

    @classmethod
    def poll(cls, context):
        return poll_deformed_mesh_with_vgroups(cls, context)

    def execute(self, context):
        obj = context.active_object
        org_mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')

        vert_index_map = build_vert_connection_map_new(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        self.store_all_weight_islands(context, obj, vert_index_map)

        bpy.ops.object.mode_set(mode=org_mode)

        return {'FINISHED'}


class EASYWEIGHT_OT_remove_island_data(Operator):
    """Remove weight island data"""

    bl_idname = "object.remove_island_data"
    bl_label = "Remove Island Data"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            cls.poll_message_set("No active object.")
            return False
        if 'island_groups' not in context.active_object:
            cls.poll_message_set("No island data to remove.")
            return False
        return True

    def execute(self, context):
        del context.active_object['island_groups']
        return {'FINISHED'}


class EASYWEIGHT_UL_weight_island_groups(UIList):
    @staticmethod
    def draw_header(layout):
        row = layout.row()
        split1 = row.split(factor=0.6)
        row1 = split1.row()
        row1.label(text="Vertex Group")
        row1.alignment = 'RIGHT'
        row1.label(text="|")
        row2 = split1.row()
        row2.label(text="Islands")

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []
        island_groups = getattr(data, propname)

        helper_funcs = bpy.types.UI_UL_list

        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(
                self.filter_name,
                self.bitflag_filter_item,
                island_groups,
                "name",
                reverse=self.use_filter_sort_reverse,
            )

        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(island_groups)

        if self.use_filter_invert:
            for idx, flag in enumerate(flt_flags):
                flt_flags[idx] = 0 if flag else self.bitflag_filter_item

        for idx, island_group in enumerate(island_groups):
            if len(island_group.islands) < 1:
                # Filter island groups with only 1 or 0 islands in them
                flt_flags[idx] = 0
            elif len(island_group.islands) == island_group.num_expected_islands:
                # Filter island groups with the expected number of islands in them
                flt_flags[idx] = 0

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'filter_name', text="")
        row.prop(self, 'use_filter_invert', toggle=True, text="", icon='ARROW_LEFTRIGHT')

        row = main_row.row(align=True)
        row.use_property_split = True
        row.use_property_decorate = False
        row.prop(self, 'use_filter_sort_alpha', toggle=True, text="")
        row.prop(self, 'use_filter_sort_reverse', toggle=True, text="", icon='SORT_ASC')

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        island_group = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            icon = 'ERROR'
            num_islands = len(island_group.islands)
            if num_islands == island_group.num_expected_islands:
                icon = 'CHECKMARK'
            row = layout.row()
            split = row.split(factor=0.6)
            row1 = split.row()
            row1.label(text=island_group.name)
            row1.alignment = 'RIGHT'
            row1.label(text="|")
            row2 = split.row(align=True)
            row2.label(text=str(num_islands), icon=icon)
            row2.operator(
                EASYWEIGHT_OT_focus_smallest_island.bl_idname, text="", icon='VIEWZOOM'
            ).vgroup = island_group.name
            row2.operator(
                EASYWEIGHT_OT_mark_island_as_okay.bl_idname, text="", icon='CHECKMARK'
            ).vgroup = island_group.name
        elif self.layout_type in {'GRID'}:
            pass


class EASYWEIGHT_PT_WeightIslands(Panel):
    """Panel with utilities for detecting rogue weights."""

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EasyWeight'
    bl_label = "Weight Islands"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator(EASYWEIGHT_OT_calculate_weight_islands.bl_idname)
        row.operator(EASYWEIGHT_OT_remove_island_data.bl_idname, text="", icon='X')

        obj = context.active_object
        island_groups = obj.island_groups
        if len(island_groups) == 0:
            return

        EASYWEIGHT_UL_weight_island_groups.draw_header(layout)

        row = layout.row()
        row.template_list(
            'EASYWEIGHT_UL_weight_island_groups',
            '',
            obj,
            'island_groups',
            obj,
            'active_islands_index',
        )


registry = [
    VertIndex,
    WeightIsland,
    IslandGroup,
    EASYWEIGHT_OT_calculate_weight_islands,
    EASYWEIGHT_OT_remove_island_data,
    EASYWEIGHT_OT_focus_smallest_island,
    EASYWEIGHT_OT_mark_island_as_okay,
    EASYWEIGHT_PT_WeightIslands,
    EASYWEIGHT_UL_weight_island_groups,
]


def update_active_islands_index(obj, context):
    if len(obj.island_groups) == 0:
        return
    obj.vertex_groups.active_index = obj.vertex_groups.find(
        obj.island_groups[obj.active_islands_index].name
    )


def register():
    Object.island_groups = CollectionProperty(type=IslandGroup)
    Object.active_islands_index = IntProperty(update=update_active_islands_index)


def unregister():
    del Object.island_groups
    del Object.active_islands_index
