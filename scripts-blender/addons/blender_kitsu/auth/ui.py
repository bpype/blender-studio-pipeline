#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .. import prefs
from ..auth.ops import KITSU_OT_session_end, KITSU_OT_session_start


class KITSU_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_category = "Kitsu"
    bl_label = "Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        session = prefs.session_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not session.is_auth():
            row.label(text=f"Email: {addon_prefs.email}")
            row = layout.row(align=True)
            row.label(text=f"Host:  {addon_prefs.host}")
            row = layout.row(align=True)
            row.operator(KITSU_OT_session_start.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {session.email}")
            row = layout.row(align=True)
            row.operator(
                KITSU_OT_session_end.bl_idname, text="Logout", icon="PANEL_CLOSE"
            )


class KITSU_PT_sqe_auth(KITSU_PT_vi3d_auth):
    bl_space_type = "SEQUENCE_EDITOR"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(not prefs.session_auth(context))


class KITSU_PT_comp_auth(KITSU_PT_vi3d_auth):
    bl_space_type = "NODE_EDITOR"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(not prefs.session_auth(context))


# ---------REGISTER ----------
# classes that inherit from another need to be registered first for some reason
classes = [KITSU_PT_comp_auth, KITSU_PT_sqe_auth, KITSU_PT_vi3d_auth]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
