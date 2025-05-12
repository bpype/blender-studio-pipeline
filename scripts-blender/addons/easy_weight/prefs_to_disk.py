# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path

import bpy

from . import __package__ as base_package

def get_addon_prefs(context=None):
    if not context:
        context = bpy.context

    addons = context.preferences.addons
    if base_package.startswith('bl_ext'):
        # 4.2 and later
        name = base_package
    else:
        # Pre-4.2
        name = base_package.split(".")[0]

    if name in addons:
        prefs = addons[name].preferences
        if prefs == None:
            pass
            # print("This happens when packaging the extension, due to the registration delay.")
        return addons[name].preferences


def update_prefs_on_file(self=None, context=None) -> tuple[str, dict]:
    prefs = get_addon_prefs(context)
    if not type(prefs).loading:
        prefs.save_prefs_to_file()


class PrefsFileSaveLoadMixin:
    """Mix-in class that can be used by any add-on to store their preferences in a file,
    so that they don't get lost when the add-on is disabled.
    To use it, copy this class and the two functions above it, and do this in your code:

    ```
    import bpy, json
    from pathlib import Path

    class MyAddonPrefs(PrefsFileSaveLoadMixin, bpy.types.AddonPreferences):
        some_prop: bpy.props.IntProperty(update=update_prefs_on_file)

    def register():
        bpy.utils.register_class(MyAddonPrefs)
        MyAddonPrefs.register_autoload_from_file()
    ```
    """

    loading = False

    @staticmethod
    def register_autoload_from_file(delay=0.5):
        def timer_func(_scene=None):
            prefs = get_addon_prefs()
            if not prefs:
                return 1
            prefs.load_prefs_from_file()
        bpy.app.timers.register(timer_func, first_interval=delay)

    def prefs_to_dict_recursive(self, propgroup: 'IDPropertyGroup') -> dict:
        """Recursively convert AddonPreferences to a dictionary.
        Note that AddonPreferences don't support PointerProperties,
        so this function doesn't either."""
        from rna_prop_ui import IDPropertyGroup

        ret = {}

        if hasattr(propgroup, 'bl_rna'):
            rna_class = propgroup.bl_rna
        else:
            property_group_class_name = type(propgroup).__name__
            rna_class = bpy.types.PropertyGroup.bl_rna_get_subclass_py(
                property_group_class_name
            )

        for key, value in propgroup.items():
            if type(value) == list:
                ret[key] = [self.prefs_to_dict_recursive(elem) for elem in value]
            elif type(value) == IDPropertyGroup:
                ret[key] = self.prefs_to_dict_recursive(value)
            else:
                if (
                    rna_class
                    and key in rna_class.properties
                    and hasattr(rna_class.properties[key], 'enum_items')
                ):
                    # Save enum values as string, not int.
                    ret[key] = rna_class.properties[key].enum_items[value].identifier
                else:
                    ret[key] = value
        return ret

    def apply_prefs_from_dict_recursive(self, propgroup, data):
        for key, value in data.items():
            if not hasattr(propgroup, key):
                # Property got removed or renamed in the implementation.
                continue
            if type(value) == list:
                for elem in value:
                    collprop = getattr(propgroup, key)
                    entry = collprop.get(elem['name'])
                    if not entry:
                        entry = collprop.add()
                    self.apply_prefs_from_dict_recursive(entry, elem)
            elif type(value) == dict:
                self.apply_prefs_from_dict_recursive(getattr(propgroup, key), value)
            else:
                setattr(propgroup, key, value)

    @staticmethod
    def get_prefs_filepath() -> Path:
        addon_name = __package__.split(".")[-1]
        return Path(bpy.utils.user_resource('CONFIG')) / Path(addon_name + ".json")

    def save_prefs_to_file(self, _context=None):
        data_dict = self.prefs_to_dict_recursive(propgroup=self)

        filepath = self.get_prefs_filepath()

        with open(filepath, "w") as f:
            json.dump(data_dict, f, indent=4)

        return filepath, json.dumps(data_dict, indent=4)

    def load_prefs_from_file(self) -> bool:
        filepath = self.get_prefs_filepath()
        if not filepath.exists():
            return False

        success = True
        with open(filepath, "r") as f:
            addon_data = json.load(f)
            type(self).loading = True
            try:
                self.apply_prefs_from_dict_recursive(self, addon_data)
            except Exception as exc:
                # If we get an error raised here, and it isn't handled,
                # the add-on seems to break.
                print(
                    f"{base_package}: Failed to load {__package__} preferences from file."
                )
                raise exc
            type(self).loading = False
        return success
