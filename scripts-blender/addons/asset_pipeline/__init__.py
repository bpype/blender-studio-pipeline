# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from bpy.utils import register_class, unregister_class
from types import ModuleType

from . import (
    ui,
    ops,
    opscore,
    props,
    prefs,
    merge,
    asset_catalog,
    config,
    hooks,
    images,
    logging,
    utils,
)

modules = [
    ui,
    ops,
    opscore,
    props,
    prefs,
    merge,
    asset_catalog,
    config,
    hooks,
    images,
    logging,
    utils,
]

# ----------------REGISTER--------------.


def recurive_register(modules: list[ModuleType], register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = register_class if register else unregister_class

    for m in modules:
        un = "un"
        if register:
            importlib.reload(m)
            un = ""

        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    print(f"{__package__}: Failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, 'modules'):
            recurive_register(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()


def register():
    """Very first entry point called by Blender when enabling the add-on."""
    recurive_register(modules, True)


def unregister():
    """Called by Blender when disabling the add-on."""

    # We want to save add-on prefs to file so they don't get lost when the add-on is disabled.
    # This should be done before unregistering anything, otherwise things can fail.
    # prefs.update_prefs_on_file()

    recurive_register(modules, False)