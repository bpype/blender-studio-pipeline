# Blender Log addon for Blender
# Copyright (C) 2024 Demeter Dzadik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Blender Log",
    "author": "Demeter Dzadik",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D View -> Sidebar -> (You can choose which panel)",
    "description": "A dedicated place for other add-ons to report, organize, and fix issues",
    "category": "System",
    "doc_url": "",
    "tracker_url": "",
}

import importlib
import bpy

from . import prefs, props, operators, ui, app_handlers, id_types

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
