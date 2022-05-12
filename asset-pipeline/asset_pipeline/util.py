# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

from typing import List, Dict, Union, Any, Set, Optional, Tuple, Generator

import bpy


def redraw_ui() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_addon_prefs() -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons[__package__].preferences


def is_file_saved() -> bool:
    return bool(bpy.data.filepath)


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def del_collection(collection: bpy.types.Collection) -> None:
    collection.user_clear()
    bpy.data.collections.remove(collection)


def reset_armature_pose(
    rig: bpy.types.Object,
    only_selected=False,
    reset_transforms=True,
    reset_properties=True,
):
    bones = rig.pose.bones
    if only_selected:
        bones = [pb for pb in rig.pose.bones if pb.bone.select]

    for pb in bones:
        if reset_transforms:
            pb.location = (0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.scale = (1, 1, 1)

        if reset_properties and len(pb.keys()) > 0:
            rna_properties = [
                prop.identifier for prop in pb.bl_rna.properties if prop.is_runtime
            ]

            # Reset custom property values to their default value
            for key in pb.keys():
                if key.startswith("$"):
                    continue
                if key in rna_properties:
                    continue  # Addon defined property.

                ui_data = None
                try:
                    ui_data = pb.id_properties_ui(key)
                    if not ui_data:
                        continue
                    ui_data = ui_data.as_dict()
                    if not "default" in ui_data:
                        continue
                except TypeError:
                    # Some properties don't support UI data, and so don't have a
                    # default value. (like addon PropertyGroups)
                    pass

                if not ui_data:
                    continue

                if type(pb[key]) not in (float, int):
                    continue
                pb[key] = ui_data["default"]
