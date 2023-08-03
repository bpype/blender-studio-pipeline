import bpy, os, importlib

from . import operators, ui, props, prefs

bl_info = {
    'name': "GeoNode Shape Keys",
    'author': "Demeter Dzadik",
    "version": (0, 0, 3),
    'blender': (3, 5, 0),
    'description': "Shape keys in the modifier stack",
    'location': "Properties->Mesh->Shape Keys->GeoNode ShapeKeys, only on overridden meshes",
    'category': 'Animation',
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
