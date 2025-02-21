# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2021, Blender Foundation - Paul Golter
# (c) 2022, Blender Foundation - Demeter Dzadik

import importlib
import bpy

from . import (
    props,
    repository,
    operators,
    threaded,
    ui,
    prefs,
    svn_info,
)

bl_info = {
    "name": "Blender SVN",
    "author": "Demeter Dzadik, Paul Golter",
    "description": "An SVN (Subversion) interface built directly into Blender",
    "blender": (3, 1, 0),
    "version": (1, 0, 3),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts-blender/addons/blender_svn",
    "category": "Generic",
}


modules = [
    props,
    operators,
    repository,
    threaded,
    ui,
    prefs,
    svn_info,
]


def register_unregister_modules(modules, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = bpy.utils.register_class if register else bpy.utils.unregister_class

    for m in modules:
        if register:
            importlib.reload(m)
        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    un = 'un' if not register else ''
                    print(f"Warning: Failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()


def register():
    register_unregister_modules(modules, True)


def unregister():
    register_unregister_modules(modules, False)
