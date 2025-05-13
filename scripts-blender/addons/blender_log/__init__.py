# SPDX-FileCopyrightText: 2024 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Blender Log",
    "author": "Demeter Dzadik",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D View -> Sidebar -> (You can choose which panel)",
    "description": "A dedicated place for other add-ons to report, organize, and fix issues",
    "category": "System",
    "doc_url": "",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts-blender/addons/blender_log",
}

import importlib
import bpy

from . import prefs, props, operators, ui, app_handlers, id_types, hotkeys

# Each module can have register() and unregister() functions and a list of classes to register called "registry".
modules = [prefs, props, operators, ui, app_handlers]


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
                un = 'un' if not register else ''
                try:
                    register_func(c)
                except Exception as e:
                    print(f"Warning: Failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()


def register():
    register_unregister_modules(modules, register=True)


def unregister():
    register_unregister_modules(modules, register=False)
