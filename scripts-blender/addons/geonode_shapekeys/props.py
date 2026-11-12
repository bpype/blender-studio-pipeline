# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from bpy.props import CollectionProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Modifier, Object, PropertyGroup

from .operators import geomod_get_param_value


_is_renaming = False


def _replace_name(current: str, old_name: str | None, new_name: str) -> str:
    """Return `current` with `old_name` replaced by `new_name`, so that any prefix or
    suffix that was added to it (for example by the user) is preserved.

    If `old_name` can't be found in `current`, fall back to using `new_name` as-is.
    """
    if old_name:
        # The modifier name may have a .001 suffix that the storage object doesn't have.
        candidates = [old_name, re.sub(r"\.\d{3,}$", "", old_name)]
        for candidate in candidates:
            if candidate and candidate in current:
                return current.replace(candidate, new_name, 1)
    return new_name


def _update_gnsk_name(self, _context):
    """Keep the modifier, storage object, and the entries of all other objects sharing
    this shape in sync with the name that was just set on this entry."""
    global _is_renaming
    if _is_renaming or not self.storage_object:
        # Not fully set up yet (see OBJECT_OT_gnsk_add_shape), or we are the ones renaming.
        return

    _is_renaming = True
    try:
        new_name = self.name
        storage = self.storage_object

        entries = [self]
        for target in storage.geonode_shapekey_targets:
            if not target.obj:
                continue
            for other in target.obj.geonode_shapekeys:
                if other.storage_object == storage and other.as_pointer() != self.as_pointer():
                    entries.append(other)

        # The modifier still has the old name at this point, so use it to find out
        # what the shape was called before the rename.
        old_mod = self.modifier
        old_name = old_mod.name if old_mod else None

        for gnsk in entries:
            mod = gnsk.modifier
            if mod:
                mod.name = new_name
                # The name may have gotten a .001 suffix to stay unique on this object.
                gnsk.name = mod.name
            else:
                gnsk.name = new_name

        storage.name = _replace_name(storage.name, old_name, new_name)
    finally:
        _is_renaming = False


class GeoNodeShapeKey(PropertyGroup):
    name: StringProperty(
        description="Name of the modifier, storage object, etc. Renaming it renames those as well",
        override={'LIBRARY_OVERRIDABLE'},
        update=_update_gnsk_name,
    )

    # On target objects, this stores the local object for sculpting.
    # Used for deletion and back and forth switching.
    storage_object: PointerProperty(
        name="Storage Object", type=Object, override={'LIBRARY_OVERRIDABLE'}
    )

    @property
    def ob_name(self) -> str:
        return self.id_data.name + "." + self.name

    @property
    def modifier(self) -> Modifier:
        for mod in self.id_data.modifiers:
            if mod.type == 'NODES':
                sculpt_ob = geomod_get_param_value(mod, "Sculpt")
                if not sculpt_ob:
                    continue
                if sculpt_ob == self.storage_object:
                    return mod

    @property
    def other_affected_objects(self) -> list[Object]:
        if not self.storage_object:
            return []

        ret = []
        for target in self.storage_object.geonode_shapekey_targets:
            if target.obj in [None, self.id_data]:
                continue
            ret.append(target.obj)

        return ret

    @property
    def index(self):
        obj = self.id_data
        for i, gnsk in enumerate(obj.geonode_shapekeys):
            if gnsk == self:
                return i

    @property
    def shapekey_targets(self):
        return self.storage_object.geonode_shapekey_targets


class GNSK_TargetObject(PropertyGroup):
    obj: PointerProperty(name="Target Object", type=Object)


registry = [GeoNodeShapeKey, GNSK_TargetObject]


def register():
    Object.geonode_shapekeys = CollectionProperty(
        type=GeoNodeShapeKey, override={'LIBRARY_OVERRIDABLE', 'USE_INSERTION'}
    )
    Object.geonode_shapekey_index = IntProperty(
        options={'LIBRARY_EDITABLE'}, override={'LIBRARY_OVERRIDABLE'}
    )

    # On local objects for sculpting, this stores the target objects.
    # Used for switching context between source and target objects.
    Object.geonode_shapekey_targets = CollectionProperty(type=GNSK_TargetObject)
