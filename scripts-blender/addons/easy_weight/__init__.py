# SPDX-License-Identifier: GPL-2.0-or-later

from . import (
    force_apply_mirror,
    toggle_weight_paint,
    vertex_group_operators,
    weight_cleaner,
    weight_pie,
    vertex_group_menu,
    rogue_weights,
    prefs,
)
import bpy
import importlib

bl_info = {
    "name": "Easy Weight",
    "author": "Demeter Dzadik",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D View -> Sidebar -> Easy Weight",
    "description": "Operators to make weight painting easier.",
    "category": "Rigging",
    "doc_url": "https://studio.blender.org/pipeline/addons/easy_weight",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-pipeline",
}


modules = [
    force_apply_mirror,
    toggle_weight_paint,
    vertex_group_operators,
    weight_cleaner,
    weight_pie,
    vertex_group_menu,
    rogue_weights,
    prefs,
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
