# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Lattice Magic",
    "author": "Demeter Dzadik",
    "version": (0, 1, 3),
    "blender": (2, 90, 0),
    "location": "View3D > Sidebar > Lattice Magic",
    "description": "Various Lattice-based tools to smear or adjust geometry.",
    "category": "Rigging",
    "doc_url": "https://gitlab.com/blender/lattice_magic/-/wikis/home",
    "tracker_url": "https://gitlab.com/blender/lattice_magic/-/issues/new",
}

import importlib
import bpy

from . import (
    camera_lattice,
    tweak_lattice,
    operators,
    utils,
    prefs,
)

modules = [camera_lattice, tweak_lattice, operators, utils, prefs]


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
