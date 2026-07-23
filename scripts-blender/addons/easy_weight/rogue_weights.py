# SPDX-FileCopyrightText: 2024-2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections import defaultdict

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import (
    Context,
    Event,
    Mesh,
    Object,
    Operator,
    OperatorProperties,
    Panel,
    PropertyGroup,
    UILayout,
    UIList,
    VertexGroup,
)
from bpy.utils import flip_name

from .utils import get_deforming_vgroups, poll_deformed_mesh_with_vgroups

"""
This module implements the Sidebar -> EasyWeight -> Weight Islands panel, which provides
a workflow for hunting down and cleaning up rogue weights efficiently.
"""


class EASYWEIGHT_PT_WeightIslands(Panel):
    """Panel with utilities for detecting rogue weights."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "EasyWeight"
    bl_label = "Weight Islands"

    @classmethod
    def poll(cls, context: Context):
        return (
            context.active_object
            and context.active_object.type == "MESH"
            and context.mode == "PAINT_WEIGHT"
        )

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row(align=True)
        text = "Calculate Weight Islands"
        if context.active_object.island_groups:
            text = "Re-Calculate Weight Islands"
        row.operator(EASYWEIGHT_OT_calculate_weight_islands.bl_idname, text=text)
        row.operator(EASYWEIGHT_OT_remove_island_data.bl_idname, text="", icon="X")

        obj = context.active_object
        island_groups = obj.island_groups
        if len(island_groups) == 0:
            return

        EASYWEIGHT_UL_weight_island_groups.draw_header(layout)

        row = layout.row()
        row.template_list(
            "EASYWEIGHT_UL_weight_island_groups",
            "",
            obj,
            "island_groups",
            obj,
            "active_islands_index",
        )


class EASYWEIGHT_UL_weight_island_groups(UIList):
    @staticmethod
    def draw_header(layout: UILayout):
        row = layout.row()
        split1 = row.split(factor=0.6)
        row1 = split1.row()
        row1.label(text="Vertex Group")
        row1.alignment = "RIGHT"
        row1.label(text="|")
        row2 = split1.row()
        row2.label(text="Islands")

    def filter_items(self, _context: Context, data: Object, propname: str):
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

        for idx, island_group in enumerate(island_groups):
            if len(island_group.islands) <= 1:
                # Filter island groups with only 1 or 0 islands in them
                flt_flags[idx] = 0
            elif len(island_group.islands) == island_group.num_expected_islands:
                # Filter island groups with the expected number of islands in them
                flt_flags[idx] = 0

        if self.use_filter_invert:
            for idx, flag in enumerate(flt_flags):
                flt_flags[idx] = 0 if flag else self.bitflag_filter_item

        return flt_flags, flt_neworder

    def draw_filter(self, _context: Context, layout: UILayout):
        # Nothing much to say here, it's usual UI code...
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, "filter_name", text="")
        row.prop(
            self, "use_filter_invert", toggle=True, text="", icon="ARROW_LEFTRIGHT"
        )

        row = main_row.row(align=True)
        row.use_property_split = True
        row.use_property_decorate = False
        row.prop(self, "use_filter_sort_alpha", toggle=True, text="")
        row.prop(self, "use_filter_sort_reverse", toggle=True, text="", icon="SORT_ASC")

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: Object,
        item: IslandGroup,
        icon: str,
        _active_data: Object,
        _active_propname: str,
    ):
        island_group = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            icon = "ERROR"
            num_islands = len(island_group.islands)
            if num_islands == island_group.num_expected_islands:
                icon = "CHECKMARK"
            row = layout.row()
            split = row.split(factor=0.6)
            row1 = split.row()
            row1.label(text=island_group.name)
            row1.alignment = "RIGHT"
            row1.label(text="|")
            row2 = split.row(align=True)
            row2.label(text=str(num_islands), icon=icon)
            row2.operator(
                EASYWEIGHT_OT_focus_smallest_island.bl_idname, text="", icon="VIEWZOOM"
            ).vgroup = island_group.name
            if num_islands != island_group.num_expected_islands:
                row2.operator(
                    EASYWEIGHT_OT_mark_island_as_okay.bl_idname,
                    text="",
                    icon="CHECKMARK",
                ).vgroup = island_group.name
            else:
                row2.label(text="", icon='BLANK1')
        elif self.layout_type in {"GRID"}:
            pass


class EASYWEIGHT_OT_calculate_weight_islands(Operator):
    "Calculate weight islands for each deforming vertex group and list groups with an unexpected island count below."\
    "\nShift: Confirmed counts persist across recalculation"

    bl_idname = "object.calculate_weight_islands"
    bl_label = "Calculate Weight Islands"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    preserve_counts: BoolProperty(default=False)

    @staticmethod
    def store_all_weight_islands(
        context: Context,
        obj: Object,
        vert_index_map: dict,
        vgroup_membership_map: dict[int, set[int]],
        preserve_counts=False,
    ):
        """Store the weight island information of every deforming vertex group."""
        wm = context.window_manager

        island_groups = obj.island_groups
        prev_expected_islands = dict()
        if preserve_counts:
            prev_expected_islands = {
                island_group.name: island_group.num_expected_islands
                for island_group in island_groups
            }
        island_groups.clear()
        obj.active_islands_index = 0
        vgroups = get_deforming_vgroups(obj)
        wm.progress_begin(0, len(vgroups))
        for i, vgroup in enumerate(vgroups):
            if "skip_groups" in obj and vgroup.name in obj["skip_groups"]:
                continue

            island_group, _ = update_vgroup_islands(
                vgroup, vert_index_map, vgroup_membership_map, island_groups
            )
            if preserve_counts:
                island_group.num_expected_islands = prev_expected_islands.get(vgroup.name, 1)
            wm.progress_update(i)
        wm.progress_end()

    @classmethod
    def poll(cls, context: Context):
        return poll_deformed_mesh_with_vgroups(cls, context)

    def invoke(self, context: Context, event: Event):
        if event.shift:
            self.preserve_counts = True
        return self.execute(context)

    def execute(self, context: Context):
        obj = context.active_object
        mesh = obj.data
        vert_index_map = build_vert_connection_map(mesh)
        vgroup_membership_map = build_vgroup_membership_map(mesh)
        self.store_all_weight_islands(
            context, obj, vert_index_map, vgroup_membership_map, self.preserve_counts
        )
        return {"FINISHED"}


def ops_check_group(operator: OperatorProperties, obj: Object, vg_name: str) -> set[str] | None:
    if vg_name not in obj.island_groups:
        operator.report(
            {"ERROR"},
            f"Vertex Group Island {vg_name} not found in object {obj.name}.",
        )
        return {"CANCELLED"}
    if vg_name not in obj.vertex_groups:
        operator.report(
            {"ERROR"},
            f"Vertex Group {vg_name} not found in object {obj.name}. Removed entry.",
        )
        if vg_name in obj.island_groups:
            obj.island_groups.remove(obj.island_groups.find(vg_name))
        return {"CANCELLED"}


class EASYWEIGHT_OT_mark_island_as_okay(Operator):
    """Mark this number of vertex islands to be the intended amount. Vertex group will be hidden from the list until this number changes"""

    bl_idname = "object.set_expected_island_count"
    bl_label = "Set Intended Island Count"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    vgroup: StringProperty(
        name="Vertex Group",
        default="",
        description="Name of the vertex group whose intended island count will be set",
    )

    def execute(self, context: Context):
        obj = context.active_object
        mesh = obj.data

        ret = ops_check_group(self, obj, self.vgroup)
        if ret:
            return ret

        # Update existing island data first
        island_group = obj.island_groups[self.vgroup]
        vgroup = obj.vertex_groups[self.vgroup]
        vert_index_map = build_vert_connection_map(mesh)
        vgroup_membership_map = build_vgroup_membership_map(mesh)
        org_num_islands = len(island_group.islands)
        island_group, _ = update_vgroup_islands(
            vgroup, vert_index_map, vgroup_membership_map, obj.island_groups, island_group
        )
        new_num_islands = len(island_group.islands)
        if new_num_islands != org_num_islands:
            if new_num_islands == 1:
                self.report(
                    {"INFO"},
                    "Vertex group is now a single island, changing expected island count no longer necessary.",
                )
            else:
                self.report(
                    {"INFO"},
                    f"Vertex group island count changed from {org_num_islands} to {new_num_islands}. Click again to mark this as the expected number.",
                )
                return {'CANCELLED'}

        island_group.num_expected_islands = new_num_islands
        ensure_active_islands_is_visible(obj)
        return {"FINISHED"}


class EASYWEIGHT_OT_focus_smallest_island(Operator):
    """Enter Weight Paint mode and focus on the smallest island"""

    bl_idname = "object.focus_smallest_weight_island"
    bl_label = "Focus Smallest Island"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

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

    def execute(self, context: Context):
        obj = context.active_object
        mesh = obj.data
        org_mode = obj.mode

        ret = ops_check_group(self, obj, self.vgroup)
        if ret:
            return ret

        # Also update the opposite side vertex group.
        vgroup_names = [self.vgroup]
        flipped = flip_name(self.vgroup)
        if flipped != self.vgroup:
            vgroup_names.append(flipped)

        vert_index_map = build_vert_connection_map(mesh)
        vgroup_membership_map = build_vgroup_membership_map(mesh)
        self_islands: list[list[int]] = []
        for vg_name in vgroup_names:
            if vg_name not in obj.island_groups:
                continue
            # Update existing island data first.
            island_group = obj.island_groups[vg_name]
            vgroup = obj.vertex_groups[vg_name]
            org_num_islands = len(island_group.islands)
            island_group, islands = update_vgroup_islands(
                vgroup, vert_index_map, vgroup_membership_map, obj.island_groups, island_group
            )
            new_num_islands = len(island_group.islands)
            if vg_name == self.vgroup:
                self_islands = islands
                if new_num_islands < 2 and org_num_islands > 1:
                    self.report(
                        {"INFO"},
                        f"Vertex group {vg_name} no longer has multiple islands, hidden from list.",
                    )
                    ensure_active_islands_is_visible(obj)
                    return {"FINISHED"}

        island_groups = obj.island_groups
        island_group = island_groups[self.vgroup]
        obj.active_islands_index = island_group.index

        smallest_island = min(self_islands, key=len)
        select_vertices(mesh, smallest_island)

        if self.focus_view:
            # We have to focus the verts in edit mode, because
            # in WP mode it would focus the selected bones instead.
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.view3d.view_selected()

        if self.enter_wp and context.mode != 'PAINT_WEIGHT':
            bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
        elif obj.mode != org_mode:
            bpy.ops.object.mode_set(mode=org_mode)

        # Select the bone
        if context.mode == "PAINT_WEIGHT":
            rig = context.pose_object
            if rig:
                for pb in rig.pose.bones:
                    if bpy.app.version < (5, 0, 0):
                        pb.bone.select = False
                    else:
                        pb.select = False
                if self.vgroup in rig.pose.bones:
                    if bpy.app.version < (5, 0, 0):
                        rig.pose.bones[self.vgroup].bone.select = True
                    else:
                        rig.pose.bones[self.vgroup].select = True

        self.report({"INFO"}, "Focused on the smallest island of weights.")
        return {"FINISHED"}


class EASYWEIGHT_OT_remove_island_data(Operator):
    """Remove weight island data"""

    bl_idname = "object.remove_island_data"
    bl_label = "Remove Island Data"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @classmethod
    def poll(cls, context: Context):
        if not context.active_object:
            cls.poll_message_set("No active object.")
            return False
        if bpy.app.version < (5, 0, 0):
            if "island_groups" not in context.active_object:
                cls.poll_message_set("No island data to remove.")
                return False
        elif not context.active_object.is_property_set("island_groups"):
            cls.poll_message_set("No island data to remove.")
            return False

        return True

    def execute(self, context: Context):
        if bpy.app.version < (5, 0, 0):
            del context.active_object["island_groups"]
            del context.active_object["active_islands_index"]
        else:
            context.active_object.property_unset("island_groups")
            context.active_object.property_unset("active_islands_index")
        return {"FINISHED"}


class WeightIsland(PropertyGroup):
    num_verts: IntProperty()


class IslandGroup(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name of the vertex group this set of islands is associated with",
    )
    islands: CollectionProperty(type=WeightIsland)
    num_expected_islands: IntProperty(
        name="Expected Islands",
        default=1,
        min=1,
        description="Number of weight islands that have been marked as the expected amount by the user. If the real amount differs from this value, a warning appears",
    )

    @property
    def index(self) -> int:
        obj = self.id_data
        return obj.island_groups.find(self.name)


def update_vgroup_islands(
    vgroup: VertexGroup,
    vert_index_map: dict,
    vgroup_membership_map: dict[int, set[int]],
    island_groups: list[IslandGroup],
    island_group: IslandGroup | None = None,
) -> tuple[IslandGroup, list[list[int]]]:
    """Recompute the weight islands of a vertex group, storing only their
    sizes in RNA. The full vertex index lists are returned instead of stored,
    since they're only needed transiently by callers (e.g. to select them)."""
    islands = get_islands_of_vgroup(vgroup, vert_index_map, vgroup_membership_map)

    if not island_group:
        island_group = island_groups.add()
        island_group.name = vgroup.name
    else:
        island_group.islands.clear()
    for island in islands:
        island_storage = island_group.islands.add()
        island_storage.num_verts = len(island)

    if len(islands) <= 1:
        # A group with 0 or 1 islands is never rogue, regardless of what was
        # previously marked as the expected count.
        island_group.num_expected_islands = 1

    return island_group, islands


def build_vert_connection_map(mesh: Mesh) -> dict:
    """Build a dictionary of vertex indicies pointing to a list of other vertex indicies
    that the vertex is connected to by an edge.
    """

    vert_dict = defaultdict(list)

    for edge in mesh.edges:
        vert_dict[edge.vertices[0]] += [edge.vertices[1]]
        vert_dict[edge.vertices[1]] += [edge.vertices[0]]

    return vert_dict


def build_vgroup_membership_map(mesh: Mesh) -> dict[int, set[int]]:
    """Build a dictionary mapping each vertex group index to the set of vertex
    indicies that are members of that group with a non-zero weight, so that
    group membership can be looked up in O(1) instead of scanning all of the
    mesh's vertices for every group/island.
    """

    vgroup_verts: dict[int, set[int]] = defaultdict(set)
    for vert in mesh.vertices:
        for group in vert.groups:
            if group.weight:
                vgroup_verts[group.group].add(vert.index)

    return vgroup_verts


def find_weight_island_vertices(
    start_vert_idx: int, member_verts: set[int], vert_idx_map: dict
) -> list[int]:
    """Iteratively find all vertices connected to start_vert_idx by edges that are also members of the same vertex group."""
    island = []
    visited = {start_vert_idx}
    queue = [start_vert_idx]
    while queue:
        vert_idx = queue.pop()
        island.append(vert_idx)
        for connected_vert_idx in vert_idx_map[vert_idx]:
            if connected_vert_idx in visited or connected_vert_idx not in member_verts:
                continue
            visited.add(connected_vert_idx)
            queue.append(connected_vert_idx)
    return island


def get_islands_of_vgroup(
    vgroup: VertexGroup, vert_index_map: dict, vgroup_membership_map: dict[int, set[int]]
) -> list[list[int]]:
    """Return a list of lists of vertex indicies: Weight islands within this vertex group."""
    member_verts = vgroup_membership_map.get(vgroup.index, set())
    visited: set[int] = set()
    islands = []
    for start_vert_idx in member_verts:
        if start_vert_idx in visited:
            continue
        island = find_weight_island_vertices(start_vert_idx, member_verts, vert_index_map)
        visited.update(island)
        islands.append(island)
    return islands


def select_vertices(mesh: Mesh, vert_indicies: list[int]):
    assert bpy.context.mode != "EDIT_MESH", (
        "Object must not be in edit mode, otherwise vertex selection doesn't work!"
    )

    mesh.use_paint_mask_vertex = True

    vert_indicies_set = set(vert_indicies)
    for i, vert in enumerate(mesh.vertices):
        vert.hide = False
        vert.select = i in vert_indicies_set

def ensure_active_islands_is_visible(obj: Object):
    """Make sure the active entry is visible, keep incrementing index until that is the case."""
    if len(obj.island_groups) == 0:
        return
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


registry = [
    WeightIsland,
    IslandGroup,
    EASYWEIGHT_OT_calculate_weight_islands,
    EASYWEIGHT_OT_remove_island_data,
    EASYWEIGHT_OT_focus_smallest_island,
    EASYWEIGHT_OT_mark_island_as_okay,
    EASYWEIGHT_PT_WeightIslands,
    EASYWEIGHT_UL_weight_island_groups,
]


def update_active_islands_index(obj: Object, _context: Context):
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
