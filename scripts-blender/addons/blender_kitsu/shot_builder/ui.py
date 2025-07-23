# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from typing import Any


def topbar_file_new_draw_handler(self: Any, context: bpy.types.Context) -> None:
    layout = self.layout
    layout.operator("kitsu.build_new_shot", text="Shot File")
    layout.operator("kitsu.build_new_asset", text="Asset File")
    layout.operator("kitsu.create_edit_file", text="Edit File")
    layout.separator()
