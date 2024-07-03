bl_info = {
    "name": "Pose Shape Keys",
    "author": "Demeter Dzadik",
    "version": (1, 0, 0),
    "blender": (3, 1, 0),
    "location": "Properties -> Mesh Data -> Shape Keys -> Pose Keys",
    "description": "Create shape keys that blend deformed meshes into a desired shape",
    "category": "Rigging",
    "doc_url": "https://studio.blender.org/pipeline/addons/pose_shape_keys",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts-blender/addons/pose_shape_keys",
}

import importlib
import bpy

from . import (
    props, 
    ui,
    ops,
    ui_list,
    symmetrize_shape_key,
    prefs,
)

# Each module can have register() and unregister() functions and a list of classes to register called "registry".
modules = [props, prefs, ui, ops, ui_list, symmetrize_shape_key]


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
    register_unregister_modules(modules, register=True)


def unregister():
    register_unregister_modules(modules, register=False)
