import bpy
from bpy import types
from typing import List, Tuple, Dict

# List of datablock type information tuples:
# (type_class, type_enum_string, bpy.data.<collprop_name>)
ID_INFO = [
	# High level containers
	(types.WindowManager,		'WINDOWMANAGER',	'window_managers'),
	(types.Scene,				'SCENE',			'scenes'),
	(types.World,				'WORLD',			'worlds'),
	(types.Collection,			'COLLECTION',		'collections'),
	(types.WorkSpace,			'WORKSPACE',		'workspaces'),
	(types.Screen,				'SCREEN',			'screens'),
	(types.Library,				'LIBRARY',			'libraries'),

	# Object Datas
	(types.Object,				'OBJECT',			'objects'),
	(types.Armature,			'ARMATURE',			'armatures'),
	(types.Mesh,				'MESH',				'meshes'),
	(types.Curve,				'CURVE',			'curves'),
	(types.Curves,				'CURVES',			'hair_curves'),
	(types.Camera,				'CAMERA',			'cameras'),
	(types.Lattice,				'LATTICE',			'lattices'),
	(types.GreasePencil,		'GREASEPENCIL',		'grease_pencils'),
	(types.Light,				'LIGHT',			'lights'),
	(types.LightProbe,			'LIGHT_PROBE',		'lightprobes'),
	(types.Speaker,				'SPEAKER',			'speakers'),
	(types.Volume,				'VOLUME',			'volumes'),
	(types.MetaBall,			'METABALL',			'metaballs'),

	# Sub-data
	(types.Action,				'ACTION',			'actions'),
	(types.Key,					'KEY',				'shape_keys'),
	(types.Material,			'MATERIAL',			'materials'),
	(types.NodeTree,			'NODETREE',			'node_groups'),
	(types.PointCloud,			'POINT_CLOUD',		'pointclouds'),
	(types.ParticleSettings,	'PARTICLE',			'particles'),
	(types.CacheFile,			'CACHE_FILE',		'cache_files'),

	# 2D
	(types.Image,				'IMAGE',			'images'),
	(types.Brush,				'BRUSH',			'brushes'),
	(types.Texture,				'TEXTURE',			'textures'),
	(types.Palette,				'PALETTE',			'palettes'),
	(types.PaintCurve,			'PAINT_CURVE',		'paint_curves'),
	(types.FreestyleLineStyle,	'LINESTYLE',		'linestyles'),
	(types.VectorFont,			'FONT',				'fonts'),

	# Misc
	(types.Sound,				'SOUND',			'sounds'),
	(types.MovieClip,			'MOVIECLIP',		'movieclips'),
	(types.Mask,				'MASK',				'masks'),
	(types.Text,				'TEXT',				'texts'),
]

# Map datablock type enum strings to the name of the collprop in bpy.data that stores such datablocks.
ID_IDENTIFIER_TO_STORAGE: Dict[str, str] = {tup[1] : tup[2] for tup in ID_INFO}

def get_datablock_types_enum_items() -> List[Tuple[str, str, str, str, int]]:
	"""Return the items needed to define an EnumProperty representing a datablock type selector."""
	enum_items = types.DriverTarget.bl_rna.properties['id_type'].enum_items
	ret = []
	for i, typ in enumerate(enum_items):
		ret.append((typ.identifier, typ.name, typ.name, typ.icon, i))
	ret.append(('SCREEN', 		'Screen', 		'Screen', 		'RESTRICT_VIEW_OFF', 		len(ret)))
	ret.append(('METABALL', 	'Metaball', 	'Metaball', 	'OUTLINER_OB_META', 		len(ret)))
	ret.append(('CACHE_FILE', 	'Cache File', 	'Cache File', 	'MOD_MESHDEFORM', 			len(ret)))
	ret.append(('POINT_CLOUD', 	'Point Cloud', 	'Point Cloud', 	'OUTLINER_OB_POINTCLOUD', 	len(ret)))
	ret.append(('HAIR_CURVES', 	'Hair Curves', 	'Hair Curves', 	'OUTLINER_OB_CURVES', 		len(ret)))
	ret.append(('PAINT_CURVE', 	'Paint Curve', 	'Paint Curve', 	'FORCE_CURVE', 				len(ret)))
	ret.append(('MOVIE_CLIP', 	'Movie Clip', 	'Movie Clip', 	'FILE_MOVIE', 				len(ret)))
	return ret

# List of 5-tuples that can be used to define the items of an EnumProperty.
ID_TYPE_ENUM_ITEMS: List[Tuple[str, str, str, str, int]] = get_datablock_types_enum_items()

# Map datablock type enum strings to their name and icon strings.
ID_TYPE_INFO: Dict[str, Tuple[str, str]] = {tup[0] : (tup[1], tup[3]) for tup in ID_TYPE_ENUM_ITEMS}


def get_id(name, type):
	container = ID_IDENTIFIER_TO_STORAGE[type]
	container = getattr(bpy.data, container)
	id = container.get((name, None))
	return id