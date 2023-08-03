import importlib
import bpy

from .operators import (
    select_similar_curves,
    lock_curves,
    bake_anim_across_armatures,
    relink_overridden_asset,
    id_management_pie,
)
from . import (
    easy_constraints,
    warn_about_broken_libraries,
    bone_selection_sets,
    prefs,
)

bl_info = {
    'name': "Animation Cupboard",
    'author': "Demeter Dzadik",
    "version": (0, 0, 4),
    'blender': (3, 2, 0),
    'description': "Tools to improve animation workflows",
    'location': "Various",
    'category': 'Animation',
    # 'doc_url' : "https://gitlab.com/blender/CloudRig/",
}

modules = (
    select_similar_curves,
    lock_curves,
    bake_anim_across_armatures,
    easy_constraints,
    warn_about_broken_libraries,
    bone_selection_sets,
    relink_overridden_asset,
    id_management_pie,
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
                    print(
                        f"Warning: Failed to {un}register class: {c.__name__}"
                    )
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
