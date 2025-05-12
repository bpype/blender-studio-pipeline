# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

from .util import get_addon_prefs
from bpy.props import StringProperty, PointerProperty, BoolProperty
from bpy.types import PropertyGroup
import bpy
from typing import Optional, Dict, Any, List, Tuple, Set
from . import wheels
# This will load the dateutil and BAT wheel files.
wheels.preload_dependencies()


class SVN_scene_properties(PropertyGroup):
    """Subversion properties to match this scene to a repo in the UserPrefs"""
    svn_url: StringProperty(
        name="Remote URL",
        default="",
        description="URL of the remote SVN repository of the current file, if any. Used to match to the SVN data stored in the user preferences",
    )
    svn_directory: StringProperty(
        name="Root Directory",
        default="",
        subtype="DIR_PATH",
        description="Absolute directory path of the SVN repository's root in the file system",
    )

    file_is_outdated: BoolProperty(
        name="File Is Outdated",
        description="Set to True when downloading a newer version of this file without reloading it, so that the warning in the UI can persist. This won't work in some cases involving multiple running Blender instances",
        default=False
    )

    def get_repo(self, context) -> Optional['SVN_repository']:
        """Return the active repository."""
        prefs = get_addon_prefs(context)
        return prefs.active_repo


registry = [
    SVN_scene_properties,
]


def register() -> None:
    # Scene Properties.
    bpy.types.Scene.svn = PointerProperty(type=SVN_scene_properties)


def unregister() -> None:
    del bpy.types.Scene.svn
