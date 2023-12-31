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


from .utils import hotkeys
from . import (
    rogue_weights,
    vertex_group_menu,
    vertex_group_operators,
    weight_paint_context_menu,
    toggle_weight_paint,
    force_apply_mirror,
    smart_weight_transfer,
    prefs,
)
import bpy
import importlib

bl_info = {
    "name": "Easy Weights",
    "author": "Demeter Dzadik",
    "version": (0, 1, 3),
    "blender": (2, 90, 0),
    "location": "Weight Paint > Weights > Easy Weights",
    "description": "Operators to make weight painting easier.",
    "category": "Rigging",
    "doc_url": "https://studio.blender.org/pipeline/addons/easy_weights",
    "tracker_url": "https://projects.blender.org/studio/blender-studio-pipeline",
}


modules = [
    smart_weight_transfer,
    force_apply_mirror,
    toggle_weight_paint,
    weight_paint_context_menu,
    vertex_group_operators,
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

    prefs_class = bpy.types.AddonPreferences.bl_rna_get_subclass_py(
        'EASYWEIGHT_addon_preferences'
    )
    prefs_class.hotkeys.append(
        hotkeys.addon_hotkey_register(
            op_idname='object.custom_weight_paint_context_menu',
            keymap_name='Weight Paint',
            key_id='W',
            add_on_conflict=False,
            warn_on_conflict=True,
            error_on_conflict=False,
        )
    )


def unregister():
    prefs_class = bpy.types.AddonPreferences.bl_rna_get_subclass_py(
        'EASYWEIGHT_addon_preferences'
    )
    for py_kmi in prefs_class.hotkeys:
        py_kmi.unregister()

    register_unregister_modules(modules, False)
