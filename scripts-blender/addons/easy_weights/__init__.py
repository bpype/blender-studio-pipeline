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
from . import rogue_weights
from . import vertex_group_menu
from . import vertex_group_operators
from . import weight_paint_context_menu
from . import toggle_weight_paint
from . import force_apply_mirror
from . import smart_weight_transfer
import bpy
import importlib

bl_info = {
    "name": "Easy Weight",
    "author": "Demeter Dzadik",
    "version": (0, 1, 2),
    "blender": (2, 90, 0),
    "location": "Weight Paint > Weights > Easy Weight",
    "description": "Operators to make weight painting easier.",
    "category": "Rigging",
    "doc_url": "https://gitlab.com/blender/easy_weight/-/blob/master/README.md",
    "tracker_url": "https://gitlab.com/blender/easy_weight/-/issues/new",
}


# Each module is expected to have a register() and unregister() function.
modules = [
    smart_weight_transfer,
    force_apply_mirror,
    toggle_weight_paint,
    weight_paint_context_menu,
    vertex_group_operators,
    vertex_group_menu,
    rogue_weights,
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

    hotkeys.addon_hotkey_register(
        op_idname='paint.weight_paint',
        keymap_name='Weight Paint',
        key_id='LEFTMOUSE',
        op_kwargs={'mode': 'NORMAL'},
    )
    hotkeys.addon_hotkey_register(
        op_idname='paint.weight_paint',
        keymap_name='Weight Paint',
        key_id='LEFTMOUSE',
        ctrl=True,
        op_kwargs={'mode': 'INVERT'},
    )
    hotkeys.addon_hotkey_register(
        op_idname='paint.weight_paint',
        keymap_name='Weight Paint',
        key_id='LEFTMOUSE',
        shift=True,
        op_kwargs={'mode': 'SMOOTH'},
    )

    hotkeys.addon_hotkey_register(
        op_idname='object.custom_weight_paint_context_menu',
        keymap_name='Weight Paint',
        key_id='W',
    )


def unregister():
    register_unregister_modules(modules, False)
