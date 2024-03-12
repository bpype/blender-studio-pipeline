import bpy, os, sys, traceback, addon_utils
from bpy import types
from bpy.types import Object
from typing import Dict, List, Tuple

# NOTE: This file should not import anything from this add-on!


def get_pretty_stack() -> str:
    """Make a pretty looking string out of the current execution stack,
    or the exception stack if this is called from a stack which is handling an exception.
    (Python is cool in that way - We can tell when this function is being called by
    a stack which originated in a try/except block!)
    """
    ret = ""

    exc_type, exc_value, tb = sys.exc_info()
    if exc_value:
        # If the stack we're currently on is handling an exception,
        # use the stack of that exception instead of our stack
        stack = traceback.extract_tb(exc_value.__traceback__)
    else:
        stack = traceback.extract_stack()

    lines = []
    after_generator = False
    for i, frame in enumerate(stack):
        if 'generator' in frame.filename:
            after_generator = True
        if not after_generator:
            continue
        if frame.name in (
            "log",
            "add_log",
            "log_fatal_error",
            "raise_generation_error",
        ):
            break

        # Shorten the file name; All files are in blender's "scripts" folder, so
        # that part of the path contains no useful information, just clutter.
        short_file = frame.filename
        if 'scripts' in short_file:
            short_file = frame.filename.split("scripts")[1]

        if i > 0 and frame.filename == stack[i - 1].filename:
            short_file = " " * int(len(frame.filename) / 2)

        lines.append(f"{short_file} -> {frame.name} -> line {frame.lineno}")

    ret += f" {chr(8629)}\n".join(lines)
    ret += f":\n          {frame.line}\n"
    if exc_value:
        ret += f"{exc_type.__name__}: {exc_value}"
    return ret


def get_datablock_type_icon(datablock):
    """Return the icon string representing a datablock type"""
    # It's beautiful.
    # There's no proper way to get the icon of a datablock, so we use the
    # RNA definition of the id_type property of the DriverTarget class,
    # which is an enum with a mapping of each datablock type to its icon.
    # TODO: It would unfortunately be nicer to just make my own mapping.
    if not hasattr(datablock, "type"):
        # shape keys...
        return 'NONE'
    typ = datablock.type
    if datablock.type == 'SHADER':
        typ = 'NODETREE'
    return bpy.types.DriverTarget.bl_rna.properties['id_type'].enum_items[typ].icon


def get_sidebar_size(context):
    for region in context.area.regions:
        if region.type == 'UI':
            return region.width


def draw_label_with_linebreak(context, layout, text, alert=False):
    """Attempt to simulate a proper textbox by only displaying as many
    characters in a single label as fits in the UI.
    This only works well on specific UI zoom levels.
    """

    if text == "":
        return
    col = layout.column(align=True)
    col.alert = alert
    paragraphs = text.split("\n")

    # Try to determine maximum allowed characters per line, based on pixel width of the area.
    # Not a great metric, but I couldn't find anything better.

    max_line_length = get_sidebar_size(context) / 8
    for p in paragraphs:
        lines = [""]
        for word in p.split(" "):
            if len(lines[-1]) + len(word) + 1 > max_line_length:
                lines.append("")
            lines[-1] += word + " "

        for line in lines:
            col.label(text=line)
    return col


def get_object_hierarchy_recursive(obj: Object, all_objects=[]):
    if obj not in all_objects:
        all_objects.append(obj)

    for c in obj.children:
        get_object_hierarchy_recursive(c, all_objects)

    return all_objects


def check_addon(context, addon_name: str) -> bool:
    """Same as addon_utils.check() but account for workspace-specific disabling.
    Return whether an addon is enabled in this context.
    """
    addon_enabled_in_userprefs = addon_utils.check(addon_name)[1]
    if addon_enabled_in_userprefs and context.workspace.use_filter_by_owner:
        # Not sure why it's called owner_ids, but it contains a list of enabled addons in this workspace.
        addon_enabled_in_workspace = addon_name in context.workspace.owner_ids
        return addon_enabled_in_workspace

    return addon_enabled_in_userprefs


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    return context.preferences.addons[__package__.split(".")[0]].preferences


### ID utilities
# (ID Python type, identifier string, database name)
def generate_id_info() -> List[Tuple[type, str, str]]:
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


ID_INFO = [
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
    (types.Curve, 'CURVE', 'curves'),
    (types.LightProbe, 'LIGHT_PROBE', 'lightprobes'),
    (types.MetaBall, 'METABALL', 'metaballs'),
    (types.Object, 'OBJECT', 'objects'),
    (types.Action, 'ACTION', 'actions'),
    (types.Key, 'KEY', 'shape_keys'),
    (types.Sound, 'SOUND', 'sounds'),
    (types.Material, 'MATERIAL', 'materials'),
    (types.NodeTree, 'NODETREE', 'node_groups'),
    (types.GeometryNodeTree, 'GEOMETRY', 'node_groups'),
    (types.ShaderNodeTree, 'SHADER', 'node_groups'),
    (types.Image, 'IMAGE', 'images'),
    (types.Mask, 'MASK', 'masks'),
    (types.FreestyleLineStyle, 'LINESTYLE', 'linestyles'),
    (types.Library, 'LIBRARY', 'libraries'),
    (types.VectorFont, 'FONT', 'fonts'),
    (types.CacheFile, 'CACHE_FILE', 'cache_files'),
    (types.PointCloud, 'POINT_CLOUD', 'pointclouds'),
    (types.Curves, 'HAIR_CURVES', 'hair_curves'),
    (types.Text, 'TEXT', 'texts'),
    (types.ParticleSettings, 'PARTICLE', 'particles'),
    (types.Palette, 'PALETTE', 'palettes'),
    (types.PaintCurve, 'PAINT_CURVE', 'paint_curves'),
    (types.MovieClip, 'MOVIECLIP', 'movieclips'),
    (types.WorkSpace, 'WORKSPACE', 'workspaces'),
    (types.Screen, 'SCREEN', 'screens'),
    (types.Brush, 'BRUSH', 'brushes'),
    (types.Texture, 'TEXTURE', 'textures'),
]


def get_datablock_icon_map() -> Dict[str, str]:
    """Create a mapping from datablock type identifiers to their icon.
    We can get most of the icons from the Driver Type selector enum,
    the rest we have to enter manually.
    """
    enum_items = types.DriverTarget.bl_rna.properties['id_type'].enum_items
    icon_map = {typ.identifier: typ.icon for typ in enum_items}
    icon_map.update(
        {
            'SCREEN': 'RESTRICT_VIEW_OFF',
            'METABALL': 'OUTLINER_OB_META',
            'CACHE_FILE': 'MOD_MESHDEFORM',
            'POINT_CLOUD': 'OUTLINER_OB_POINTCLOUD',
            'HAIR_CURVES': 'OUTLINER_OB_CURVES',
            'PAINT_CURVE': 'FORCE_CURVE',
            'MOVIE_CLIP': 'FILE_MOVIE',
            'GEOMETRY': 'GEOMETRY_NODES',
            'SHADER': 'NODETREE',
        }
    )

    return icon_map


# Map datablock identifier strings to their icon.
ID_TYPE_STR_TO_ICON: Dict[str, str] = get_datablock_icon_map()
# Map datablock identifier strings to the string of their bpy.data database name.
ID_TYPE_TO_STORAGE: Dict[type, str] = {tup[1]: tup[2] for tup in ID_INFO}

# Map Python ID classes to their string representation.
ID_CLASS_TO_IDENTIFIER: Dict[type, str] = {tup[0]: tup[1] for tup in ID_INFO}
# Map Python ID classes to the string of their bpy.data database name.
ID_CLASS_TO_STORAGE: Dict[type, str] = {tup[0]: tup[2] for tup in ID_INFO}


def get_datablock_icon(id) -> str:
    identifier_str = ID_CLASS_TO_IDENTIFIER.get(type(id))
    if not identifier_str:
        return 'NONE'
    icon = ID_TYPE_STR_TO_ICON.get(identifier_str)
    if not icon:
        return 'NONE'
    return icon


def get_id_storage(id_type) -> "bpy.data.something":
    """Return the database of a certain ID Type, for example if you pass in an
    Object, this will return bpy.data.objects."""
    storage = ID_TYPE_TO_STORAGE.get(id_type)
    assert storage and hasattr(bpy.data, storage), (
        "Error: Storage not found for id type: " + id_type
    )
    return getattr(bpy.data, storage)


def get_id(id_name: str, id_type: str, lib_path="") -> bpy.types.ID:
    storage = get_id_storage(id_type)
    if lib_path and lib_path != 'Local Data':
        return storage.get((id_name, lib_path))
    return storage.get((id_name, None))


### Library utilities
def get_library_icon(lib_path: str) -> str:
    """Return the library or the broken library icon, as appropriate."""
    if lib_path == 'Local Data':
        return 'FILE_BLEND'
    filepath = os.path.abspath(bpy.path.abspath(lib_path))
    if not os.path.exists(filepath):
        return 'LIBRARY_DATA_BROKEN'

    return 'LIBRARY_DATA_DIRECT'
