# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import bpy

from . import (
    easy_constraints,
    bone_selection_sets,
    prefs,
    operators,
)

bl_info = {
    'name': "Animation Cupboard",
    'author': "Demeter Dzadik",
    "version": (0, 0, 6),
    'blender': (3, 2, 0),
    'description': "Small random tools for Blender Studio animators",
    'location': "Various",
    'category': 'Animation',
    # 'doc_url' : "https://gitlab.com/blender/CloudRig/",
}

modules = (
    easy_constraints,
    bone_selection_sets,
    prefs,
    operators,
)


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
