# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import bpy

from ..context import core as context_core
from .. import cache, prefs, ui, bkglobals
from ..context.ops import (
    KITSU_OT_con_detect_context,
)


class KITSU_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_category = "Kitsu"
    bl_label = "Context"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        project_active = cache.project_active_get()
        return bool(not project_active)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        project_active = cache.project_active_get()
        episode_active = cache.episode_active_get()

        # Catch errors
        if self.poll_error(context):
            box = ui.draw_error_box(layout)
            if not project_active:
                ui.draw_error_active_project_unset(box)

        # Production
        layout.row().label(text=f"Production: {project_active.name}")
        layout.row(align=True)

        row = layout.row(align=True)
        row.label(text="Browser", icon="FILEBROWSER")

        # Detect Context
        row.operator(
            KITSU_OT_con_detect_context.bl_idname,
            icon="FILE_REFRESH",
            text="",
            emboss=False,
        )

        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )
        col = flow.column()
        # Entity context
        col.prop(context.scene.kitsu, "category")

        if not prefs.session_auth(context) or not project_active:
            row.enabled = False

        # Episode selector
        if project_active.production_type == bkglobals.KITSU_TV_PROJECT:
            context_core.draw_episode_selector(context, col)

        # Sequence selector (if context is Sequence)
        if context_core.is_sequence_context():
            context_core.draw_sequence_selector(context, col)

        # Shot selector
        if context_core.is_shot_context():
            context_core.draw_sequence_selector(context, col)
            context_core.draw_shot_selector(context, col)

        # AssetType selector (if context is Asset)
        if context_core.is_asset_context():
            context_core.draw_asset_type_selector(context, col)
            context_core.draw_asset_selector(context, col)

        # Task Type selector
        context_core.draw_task_type_selector(context, col)


class KITSU_PT_comp_context(KITSU_PT_vi3d_context):
    bl_space_type = "NODE_EDITOR"


class KITSU_PT_editorial_context(KITSU_PT_vi3d_context):
    bl_space_type = "SEQUENCE_EDITOR"


# ---------REGISTER ----------.

# Classes that inherit from another need to be registered first for some reason.
classes = [KITSU_PT_comp_context, KITSU_PT_editorial_context, KITSU_PT_vi3d_context]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
