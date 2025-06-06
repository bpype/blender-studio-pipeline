# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# <pep8-80 compliant>
import os
import sys
from pathlib import Path
from typing import List, Dict, Union, Any, Optional

import bpy
import bl_app_override

from bl_app_override.helpers import AppOverrideState
from bpy.app.handlers import persistent


def draw_left_override(self, context: bpy.types.Context):
    layout: bpy.types.UILayout = self.layout
    bpy.types.TOPBAR_MT_editor_menus.draw_collapsible(context, layout)


class AppStateStore(AppOverrideState):
    # Just provides data & callbacks for AppOverrideState
    __slots__ = ()

    @staticmethod
    def class_ignore():
        classes = []

        # I found I actually only need to override a couple of headers
        # and then the media-viewer already looks like it needs to look.
        # I had troubles using this:

        # cls = bl_app_override.class_filter(
        #         bpy.types.Header,
        #         blacklist={"TOPBAR_HT_upper_bar", "..."}
        #     ),

        # As this made it impossible to append a new draw handler after that
        # to the headers....

        # Mr. Hackerman.
        # Overrides draw function of header to just return None
        # That way we clear all these header globally and can replace
        # them with our custom draw function
        bpy.types.STATUSBAR_HT_header.draw = lambda self, context: None
        bpy.types.IMAGE_HT_header.draw = lambda self, context: None
        bpy.types.SEQUENCER_HT_header.draw = lambda self, context: None
        bpy.types.TEXT_HT_header.draw = lambda self, context: None

        # TOPBAR_HT_upper_bar.draw calls draw_left and draw_right
        # we will override those individually. We don't need draw_right anymore.
        # But for draw_left we only want it to draw TOPBAR_MT_editor_menus.draw, which is
        # why we override it with draw_left_override.
        bpy.types.TOPBAR_HT_upper_bar.draw_left = draw_left_override
        bpy.types.TOPBAR_HT_upper_bar.draw_right = lambda self, context: None
        bpy.types.TOPBAR_MT_editor_menus.draw = lambda self, context: None
        return classes

    # ----------------
    # UI Filter/Ignore

    @staticmethod
    def ui_ignore_classes():
        # What does this do?
        return ()

    @staticmethod
    def ui_ignore_operator(op_id):
        return True

    @staticmethod
    def ui_ignore_property(ty, prop):
        return True

    @staticmethod
    def ui_ignore_menu(menu_id):
        return True

    @staticmethod
    def ui_ignore_label(text):
        return True

    # -------
    # Add-ons

    @staticmethod
    def addon_paths():
        return (os.path.normpath(os.path.join(os.path.dirname(__file__), "addons")),)

    @staticmethod
    def addons():
        return ("media_viewer",)


@persistent
def handler_load_recent_directory(_):
    bpy.ops.media_viewer.load_recent_directory()


@persistent
def handler_set_template_defaults(_):
    bpy.ops.media_viewer.set_template_defaults()


init_filepaths: List[Path] = []


@persistent  # Is needed.
def init_with_mediapaths(_):
    global init_filepaths
    print("Initializing media-viewer with filepaths:")
    print("\n".join([f.as_posix() for f in init_filepaths]))
    # Assemble Path data structure that works for operator.
    files_dict = [{"name": f.as_posix()} for f in init_filepaths]
    bpy.ops.media_viewer.init_with_media_paths(files=files_dict, active_file_idx=0)


app_state = AppStateStore()
active_load_post_handlers = []


def register():
    global init_filepaths

    print("Template Register", __file__)
    app_state.setup()

    # Handler.
    bpy.app.handlers.load_post.append(handler_load_recent_directory)
    bpy.app.handlers.load_post.append(handler_set_template_defaults)
    active_load_post_handlers[:] = (
        handler_load_recent_directory,
        handler_set_template_defaults,
    )

    # Check if blender-media-viewer was started from commandline with filepaths
    # after '--'.
    # In this case that means user wants to open media with blender-media-viewer.
    # To achieve this we collect all valid existent filepaths after -- and
    # update the global init_filepaths list. We then register the init_with_mediapaths
    # load post handler that reads that variable.

    # Check cli input.
    argv = sys.argv
    if "--" not in argv:
        return
    else:
        # Collect all arguments after -- which should represent
        # individual filepaths.
        ddash_idx = argv.index("--")
        filepaths: List[Path] = []
        for idx in range(ddash_idx + 1, len(argv)):
            p = Path(argv[idx])
            # Only use if filepath that exists.
            if p.exists() and p.is_file():
                filepaths.append(p)

        if filepaths:
            init_filepaths.extend(filepaths)
            bpy.app.handlers.load_post.append(init_with_mediapaths)
            active_load_post_handlers.append(init_with_mediapaths)


def unregister():
    print("Template Unregister", __file__)
    app_state.teardown()

    # Handler.
    for handler in reversed(active_load_post_handlers):
        bpy.app.handlers.load_post.remove(handler)
