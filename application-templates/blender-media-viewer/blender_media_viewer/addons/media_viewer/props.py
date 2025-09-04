# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from typing import Tuple, Any, List, Union, Dict, Optional

import bpy

from media_viewer.log import LoggerFactory
from media_viewer import vars, opsdata, ops

logger = LoggerFactory.getLogger(name=__name__)

def update_interpret_image_strips(self, context):

    opsdata.del_all_images()
    ops.force_update_media = True

class MV_property_group(bpy.types.PropertyGroup):
    """
    Property group that will be registered on scene.
    """
    interpret_strips: bpy.props.BoolProperty(
        name = "Interpret Image Sequences",
        default = False,
        update = update_interpret_image_strips,
    )
    review_output_dir: bpy.props.StringProperty(
        name="Review Outpout",
        subtype="DIR_PATH",
        default=vars.REVIEW_OUTPUT_DIR.as_posix(),
    )
    sequence_file_type: bpy.props.EnumProperty(
        name="File Format",
        items=[
            ("MOVIE", "MOVIE", "Creates mp4 file"),
            ("IMAGE", "IMAGE", "Creates image sequence in subfolder"),
        ],
        default="MOVIE",
        description="Controls if sequence output should be a .mp4 or a jpg sequence",
    )
    draw_header_toggle = bpy.props.BoolProperty(
        name="Draw Header Toggle",
        description="Controls if custom openGL header toggle should be drawn",
        default=True,
    )


# ----------------REGISTER--------------.

classes = [
    MV_property_group,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Window Manager Properties.
    bpy.types.WindowManager.media_viewer = bpy.props.PointerProperty(
        name="Media Viewer",
        type=MV_property_group,
        description="Metadata that is required for the blender-media-viewer",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
