# SPDX-License-Identifier: GPL-3.0-or-later

from . import (
    force_apply_mirror,
    mode_switch_hook,
    operators,
    weight_cleaner,
    weight_pie,
    vertex_group_menu,
    rogue_weights,
    prefs_to_disk,
    prefs,
    utils,
)
import bpy
import importlib

bl_info = {
    "name": "Easy Weight",
    "author": "Demeter Dzadik",
    "version": (1, 0, 5),
    "blender": (4, 2, 0),
    "location": "3D View -> Sidebar -> Easy Weight",
    "description": "Operators to make weight painting easier.",
    "category": "Rigging",
    "doc_url": "https://studio.blender.org/pipeline/addons/easy_weight",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-tools",
}


modules = [
    force_apply_mirror,
    mode_switch_hook,
    operators,
    weight_cleaner,
    weight_pie,
    vertex_group_menu,
    rogue_weights,
    prefs_to_disk,
    prefs,
    utils,
]


def register_unregister_modules(modules, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = bpy.utils.register_class if register else bpy.utils.unregister_class

    for mod in modules:
        if register:
            importlib.reload(mod)
        if hasattr(mod, 'registry'):
            for class_to_register in mod.registry:
                try:
                    register_func(class_to_register)
                except Exception as e:
                    un = 'un' if not register else ''
                    print(f"Warning: Failed to {un}register class: {class_to_register.__name__}")
                    print(e)

        if hasattr(mod, 'modules'):
            register_unregister_modules(mod.modules, register)

        if register and hasattr(mod, 'register'):
            mod.register()
        elif hasattr(mod, 'unregister'):
            mod.unregister()


def register():
    register_unregister_modules(modules, True)


def unregister():
    register_unregister_modules(modules, False)
