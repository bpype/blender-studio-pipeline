import bpy
from bpy import types
from typing import List, Tuple, Dict


# List of datablock type information tuples:
# (type_class, type_enum_string, bpy.data.<collprop_name>)
def get_id_info() -> List[Tuple[type, str, str]]:
	bpy_prop_collection = type(bpy.data.objects)
	id_info = []
	for prop_name in dir(bpy.data):
		prop = getattr(bpy.data, prop_name)
		if type(prop) == bpy_prop_collection:
			if len(prop) == 0:
				# We can't get full info about the ID type if there isn't at least one entry of it.
				# But we shouldn't need it, since we don't have any entries of it!
				continue
			id_info.append((type(prop[0]), prop[0].id_type, prop_name))
	return id_info


def get_id_storage_by_type_str(typ_name: str):
	for typ, typ_str, container_str in get_id_info():
		if typ_str == typ_name:
			return getattr(bpy.data, container_str)

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


def get_id(name, type, libpath=None):
	container = get_id_storage_by_type_str(type)
	id = container.get((name, libpath))
	return id
