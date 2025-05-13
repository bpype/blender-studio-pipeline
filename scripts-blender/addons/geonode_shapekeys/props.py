# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Modifier, Object, PropertyGroup
from bpy.props import StringProperty, CollectionProperty, IntProperty, PointerProperty
from .operators import geomod_get_identifier


class GeoNodeShapeKey(PropertyGroup):
    name: StringProperty(
        description="Name of the modifier, storage object, etc", override={'LIBRARY_OVERRIDABLE'}
    )

    # On overridden objects, this stores the local object for sculpting.
    # Used for deletion and back and forth switching.
    storage_object: PointerProperty(
        name="Storage Object", type=Object, override={'LIBRARY_OVERRIDABLE'}
    )

    @property
    def ob_name(self) -> str:
        return self.id_data.name + "." + self.name

    @property
    def modifier(self) -> Modifier:
        for m in self.id_data.modifiers:
            if m.type == 'NODES':
                identifier = geomod_get_identifier(m, 'Sculpt')
                if not identifier:
                    continue
                sculpt_ob = m[identifier]
                if not sculpt_ob:
                    continue
                if sculpt_ob == self.storage_object:
                    return m

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

    # On local objects for sculpting, this stores the overridden object.
    # Used for swapping back and forth between the two objects.
    Object.geonode_shapekey_targets = CollectionProperty(type=GNSK_TargetObject)
