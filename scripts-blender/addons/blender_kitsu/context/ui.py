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
from .. import cache, prefs, ui
from ..context.ops import (
    KITSU_OT_con_sequences_load,
    KITSU_OT_con_shots_load,
    KITSU_OT_con_asset_types_load,
    KITSU_OT_con_assets_load,
    KITSU_OT_con_task_types_load,
    KITSU_OT_con_detect_context,
    KITSU_OT_con_episodes_load,
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
        if context_core.is_edit_file():
            return False
        return prefs.session_auth(context)

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        project_active = cache.project_active_get()
        return bool(not project_active)

    def draw_episode_selector(self, layout, project_active, episode_active):
        row = layout.row(align=True)

        if not project_active:
            row.enabled = False

        label_text = "Select Episode" if not episode_active else episode_active.name

        if project_active.nb_episodes > 0:
            row.operator(
                KITSU_OT_con_episodes_load.bl_idname,
                text=label_text,
                icon="DOWNARROW_HLT",
            )

    def draw_sequence_selector(self, layout, project_active, episode_active):
        row = layout.row(align=True)

        if not project_active:
            row.enabled = False

        elif project_active.nb_episodes > 0 and not episode_active:
            row.enabled = False

        sequence = cache.sequence_active_get()
        label_text = "Select Sequence" if not sequence else sequence.name

        row.operator(
            KITSU_OT_con_sequences_load.bl_idname,
            text=label_text,
            icon="DOWNARROW_HLT",
        )

    def draw_asset_type_selector(self, layout, project_active):
        row = layout.row(align=True)

        if not project_active:
            row.enabled = False

        asset_type = cache.asset_type_active_get()
        label_text = "Select Asset Type" if not asset_type else asset_type.name

        row.operator(
            KITSU_OT_con_asset_types_load.bl_idname,
            text=label_text,
            icon="DOWNARROW_HLT",
        )

    def draw_shot_selector(self, layout, project_active):
        row = layout.row(align=True)

        if not project_active:
            row.enabled = False

        shot = cache.shot_active_get()
        label_text = "Select Shot" if not shot else shot.name

        row.operator(
            KITSU_OT_con_shots_load.bl_idname,
            text=label_text,
            icon="DOWNARROW_HLT",
        )

    def draw_asset_selector(self, layout, project_active):
        row = layout.row(align=True)

        if not project_active:
            row.enabled = False

        asset = cache.asset_active_get()
        label_text = "Select Asset" if not asset else asset.name

        row.operator(
            KITSU_OT_con_assets_load.bl_idname,
            text=label_text,
            icon="DOWNARROW_HLT",
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
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

        # Entity context
        row = layout.row(align=True)
        row.prop(context.scene.kitsu, "category", expand=True)

        if not prefs.session_auth(context) or not project_active:
            row.enabled = False

        # Sequence (if context is Shot or Sequence)
        if context_core.is_sequence_context():
            if project_active.nb_episodes > 0:
                self.draw_episode_selector(layout, project_active, episode_active)
            self.draw_sequence_selector(layout, project_active, episode_active)

        # Shot
        if context_core.is_shot_context():
            if project_active.nb_episodes > 0:
                self.draw_episode_selector(layout, project_active, episode_active)
            self.draw_sequence_selector(layout, project_active, episode_active)
            self.draw_shot_selector(layout, project_active)

        # AssetType (if context is Asset)
        if context_core.is_asset_context():
            self.draw_asset_type_selector(layout, project_active)
            self.draw_asset_selector(layout, project_active)

        # Task Type.
        t_text = "Select Task Type"
        task_type_active = cache.task_type_active_get()
        if task_type_active:
            t_text = task_type_active.name
        row = layout.row(align=True)
        row.operator(KITSU_OT_con_task_types_load.bl_idname, text=t_text, icon="DOWNARROW_HLT")


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
