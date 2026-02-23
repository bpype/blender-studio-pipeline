# SPDX-FileCopyrightText: 2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from rna_prop_ui import rna_idprop_value_item_type


# Function taken from cloudrig.py
def reset_armature(
    rig,
    *,
    viewport_display=True,
    bone_visibility=True,
    action=True,
    transforms=True,
    custom_props=True,
    pose_bones=[],
):
    if viewport_display:
        rig.show_name = False
        rig.show_axis = False
        rig.show_in_front = False

    if not pose_bones:
        pose_bones = rig.pose.bones

    if action:
        if rig.animation_data:
            rig.animation_data.action = None

    for pbone in pose_bones:
        if bone_visibility:
            pbone.hide = False
            if pbone.bone:
                pbone.bone.hide = False

        if transforms:
            pbone.location = (0, 0, 0)
            pbone.rotation_euler = (0, 0, 0)
            pbone.rotation_quaternion = (1, 0, 0, 0)
            pbone.scale = (1, 1, 1)

        if not custom_props or len(pbone.keys()) == 0:
            continue

        rna_properties = [prop.identifier for prop in pbone.bl_rna.properties if prop.is_runtime]

        # Reset custom property values to their defaults.
        for key in pbone.keys():
            if key.startswith("$"):
                continue
            if key in rna_properties:
                continue  # Addon defined property.

            property_settings = None
            try:
                property_settings = pbone.id_properties_ui(key)
                if not property_settings:
                    continue
                property_settings = property_settings.as_dict()
                if 'default' not in property_settings:
                    continue
            except TypeError:
                # Some properties don't support UI data, and so don't have a default value. (like addon PropertyGroups)
                pass

            if not property_settings:
                continue

            value_type, _is_array = rna_idprop_value_item_type(pbone[key])

            if value_type not in (float, int, bool):
                continue
            pbone[key] = property_settings['default']
