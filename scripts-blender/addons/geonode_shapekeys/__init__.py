# SPDX-License-Identifier: GPL-2.0-or-later

import bpy, importlib

from . import operators, ui, props, prefs

bl_info = {
    'name': "GeoNode Shape Keys",
    'author': "Demeter Dzadik",
    "version": (1, 0, 0),
    'blender': (3, 5, 0),
    'description': "Sculpt on linked meshes",
    'location': "Properties->Mesh->Shape Keys->GeoNode ShapeKeys, only on overridden meshes",
    'category': 'Animation',
    'doc_url': "https://studio.blender.org/pipeline/addons/geonode_shapekeys",
    'tracker_url': "https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts-blender/addons/geonode_shapekeys",
    'support': 'COMMUNITY',
}

modules = (
    operators,
    props,
    ui,
    prefs,
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
