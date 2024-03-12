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

from typing import Dict, Any, Tuple, Generator
from .. import constants
import bpy
from bpy import types

ID_INFO = {
    (types.WindowManager, 'WINDOWMANAGER', 'window_managers'),
    (types.Scene, 'SCENE', 'scenes'),
    (types.World, 'WORLD', 'worlds'),
    (types.Collection, 'COLLECTION', 'collections'),
    (types.Armature, 'ARMATURE', 'armatures'),
    (types.Mesh, 'MESH', 'meshes'),
    (types.Camera, 'CAMERA', 'cameras'),
    (types.Lattice, 'LATTICE', 'lattices'),
    (types.Light, 'LIGHT', 'lights'),
    (types.Speaker, 'SPEAKER', 'speakers'),
    (types.Volume, 'VOLUME', 'volumes'),
    (types.GreasePencil, 'GREASEPENCIL', 'grease_pencils'),
    (types.GreasePencilv3, 'GREASEPENCIL_V3', 'grease_pencils_v3'),
    (types.Curve, 'CURVE', 'curves'),
    (types.LightProbe, 'LIGHT_PROBE', 'lightprobes'),
    (types.MetaBall, 'METABALL', 'metaballs'),
    (types.Object, 'OBJECT', 'objects'),
    (types.Action, 'ACTION', 'actions'),
    (types.Key, 'KEY', 'shape_keys'),
    (types.Sound, 'SOUND', 'sounds'),
    (types.Material, 'MATERIAL', 'materials'),
    (types.NodeTree, 'NODETREE', 'node_groups'),
    (types.Image, 'IMAGE', 'images'),
    (types.Mask, 'MASK', 'masks'),
    (types.FreestyleLineStyle, 'LINESTYLE', 'linestyles'),
    (types.Library, 'LIBRARY', 'libraries'),
    (types.VectorFont, 'FONT', 'fonts'),
    (types.CacheFile, 'CACHE_FILE', 'cache_files'),
    (types.PointCloud, 'POINT_CLOUD', 'pointclouds'),
    (types.Curves, 'HAIR_CURVES', 'hair_curves'),
    (types.Text, 'TEXT', 'texts'),
    # (types.Simulation, 'SIMULATION', 'simulations'),
    (types.ParticleSettings, 'PARTICLE', 'particles'),
    (types.Palette, 'PALETTE', 'palettes'),
    (types.PaintCurve, 'PAINT_CURVE', 'paint_curves'),
    (types.MovieClip, 'MOVIE_CLIP', 'movieclips'),
    (types.WorkSpace, 'WORKSPACE', 'workspaces'),
    (types.Screen, 'SCREEN', 'screens'),
    (types.Brush, 'BRUSH', 'brushes'),
    (types.Texture, 'TEXTURE', 'textures'),
}

# Map datablock Python classes to their string representation.
ID_CLASS_TO_IDENTIFIER: Dict[type, Tuple[str, int]] = dict(
    [(tup[0], (tup[1])) for tup in ID_INFO]
)

# Map datablock Python classes to the name of their bpy.data container.
ID_CLASS_TO_STORAGE_NAME: Dict[type, str] = dict(
    [(tup[0], (tup[2])) for tup in ID_INFO]
)


def get_fundamental_id_type(datablock: bpy.types.ID) -> Any:
    """Certain datablocks have very specific types.
    This function should return their fundamental type, ie. parent class."""
    for id_type in ID_CLASS_TO_IDENTIFIER.keys():
        if isinstance(datablock, id_type):
            return id_type


def get_storage_of_id(datablock: bpy.types.ID) -> 'bpy_prop_collection':
    """Return the storage collection property of the datablock.
    Eg. for an object, returns bpy.data.objects.
    """

    fundamental_type = get_fundamental_id_type(datablock)
    return getattr(bpy.data, ID_CLASS_TO_STORAGE_NAME[fundamental_type])


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def data_type_from_transfer_data_key(obj: bpy.types.Object, td_type: str):
    """Returns the data on an object that is referred to by the Transferable Data type"""
    if td_type == constants.VERTEX_GROUP_KEY:
        return obj.vertex_groups
    if td_type == constants.MODIFIER_KEY:
        return obj.modifiers
    if td_type == constants.CONSTRAINT_KEY:
        return obj.constraints
    if td_type == constants.MATERIAL_SLOT_KEY:
        return obj.material_slots
    if td_type == constants.SHAPE_KEY_KEY:
        return obj.data.shape_keys.key_blocks
    if td_type == constants.ATTRIBUTE_KEY:
        return obj.data.attributes
    if td_type == constants.PARENT_KEY:
        return obj.parent
