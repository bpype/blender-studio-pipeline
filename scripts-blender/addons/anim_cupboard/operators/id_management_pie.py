import bpy
from bpy import types
from typing import List, Tuple, Dict, Optional
from bpy.props import StringProperty, CollectionProperty
from bpy_extras import id_map_utils

import os
from ..utils import hotkeys
from .relink_overridden_asset import OUTLINER_OT_relink_overridden_asset, outliner_get_active_id


### Pie Menu UI
class IDMAN_MT_relationship_pie(bpy.types.Menu):
    # bl_label is displayed at the center of the pie menu
    bl_label = 'Datablock Relationships'
    bl_idname = 'IDMAN_MT_relationship_pie'

    @staticmethod
    def get_id(context) -> Optional[bpy.types.ID]:
        return outliner_get_active_id(context)

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # <
        pie.operator(OUTLINER_OT_list_users_of_datablock.bl_idname, icon='LOOP_BACK')
        # >
        pie.operator(
            OUTLINER_OT_list_dependencies_of_datablock.bl_idname, icon='LOOP_FORWARDS'
        )
        # V
        pie.operator('outliner.better_purge', icon='TRASH')

        id = self.get_id(context)
        if id:
            # ^
            id_type = ID_CLASS_TO_IDENTIFIER.get(type(id))
            if id_type:
                remap = pie.operator(
                    'outliner.remap_users', icon='FILE_REFRESH', text="Remap Users"
                )
                remap.id_type = id_type
                remap.id_name_source = id.name
                if id.library:
                    remap.library_path_source = id.library.filepath
            else:
                pie.label(text="Cannot remap unknwon ID type: " + str(type(id)))

            # ^>
            id = OUTLINER_OT_relink_overridden_asset.get_id(context)
            if id:
                pie.operator('object.relink_overridden_asset', icon='LIBRARY_DATA_OVERRIDE')
            else:
                pie.separator()

            # <^
            if id and id.override_library:
                pie.operator(
                    'outliner.liboverride_troubleshoot_operation',
                    icon='UV_SYNC_SELECT',
                    text="Resync Override Hierarchy",
                ).type = 'OVERRIDE_LIBRARY_RESYNC_HIERARCHY_ENFORCE'
            else:
                pie.separator()
        else:
            pie.separator()
            pie.separator()
            pie.separator()

        # v>
        if OUTLINER_OT_instancer_empty_to_collection.should_draw(context):
            pie.operator(OUTLINER_OT_instancer_empty_to_collection.bl_idname, icon='LINKED')
        else:
            pie.separator()


### Relationship visualization operators
class RelationshipOperatorMixin:
    datablock_name: StringProperty()
    datablock_storage: StringProperty()
    library_filepath: StringProperty()

    def get_datablock(self, context) -> Optional[bpy.types.ID]:
        if self.datablock_name and self.datablock_storage:
            storage = getattr(bpy.data, self.datablock_storage)
            lib_path = self.library_filepath or None
            return storage.get((self.datablock_name, lib_path))
        elif context.area.type == 'OUTLINER':
            return outliner_get_active_id(context)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'OUTLINER' and len(context.selected_ids) > 0

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self, width=600)

    def get_datablocks_to_display(self, id: bpy.types.ID) -> List[bpy.types.ID]:
        raise NotImplementedError

    def get_label(self):
        return "Listing datablocks that reference this:"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        datablock = self.get_datablock(context)
        if not datablock:
            layout.alert = True
            layout.label(
                text=f"Failed to find datablock: {self.datablock_storage}, {self.datablock_name}, {self.library_filepath}"
            )
            return

        row = layout.row()
        split = row.split()
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text=self.get_label())
        id_row = split.row(align=True)
        name_row = id_row.row()
        name_row.enabled = False
        name_row.prop(datablock, 'name', icon=get_datablock_icon(datablock), text="")
        fake_user_row = id_row.row()
        fake_user_row.prop(datablock, 'use_fake_user', text="")

        layout.separator()

        datablocks = self.get_datablocks_to_display(datablock)
        if not datablocks:
            layout.label(text="There are none.")
            return

        for user in self.get_datablocks_to_display(datablock):
            if user == datablock:
                # Scenes are users of themself for technical reasons,
                # I think it's confusing to display that.
                continue
            row = layout.row()
            name_row = row.row()
            name_row.enabled = False
            name_row.prop(user, 'name', icon=get_datablock_icon(user), text="")
            op_row = row.row()
            op = op_row.operator(type(self).bl_idname, text="", icon='LOOP_FORWARDS')
            op.datablock_name = user.name
            storage = ID_CLASS_TO_STORAGE.get(type(user))
            if not storage:
                print("Error: Can't find storage: ", type(user))
            op.datablock_storage = storage
            if user.library:
                op.library_filepath = user.library.filepath
                name_row.prop(
                    user.library,
                    'filepath',
                    icon=get_library_icon(user.library.filepath),
                    text="",
                )

    def execute(self, context):
        return {'FINISHED'}


class OUTLINER_OT_list_users_of_datablock(
    RelationshipOperatorMixin, bpy.types.Operator
):
    """Show list of users of this datablock"""

    bl_idname = "object.list_datablock_users"
    bl_label = "List Datablock Users"

    datablock_name: StringProperty()
    datablock_storage: StringProperty()
    library_filepath: StringProperty()

    def get_datablocks_to_display(self, datablock: bpy.types.ID) -> List[bpy.types.ID]:
        user_map = bpy.data.user_map()
        users = user_map[datablock]
        return sorted(users, key=lambda u: (str(type(u)), u.name))


class OUTLINER_OT_list_dependencies_of_datablock(
    RelationshipOperatorMixin, bpy.types.Operator
):
    """Show list of dependencies of this datablock"""

    bl_idname = "object.list_datablock_dependencies"
    bl_label = "List Datablock Dependencies"

    def get_label(self):
        return "Listing datablocks that are referenced by this:"

    def get_datablocks_to_display(self, datablock: bpy.types.ID) -> List[bpy.types.ID]:
        dependencies = id_map_utils.get_id_reference_map().get(datablock)
        if not dependencies:
            return []
        return sorted(dependencies, key=lambda u: (str(type(u)), u.name))


### Remap Users
class RemapTarget(bpy.types.PropertyGroup):
    pass


class OUTLINER_OT_remap_users(bpy.types.Operator):
    """A wrapper around Blender's built-in Remap Users operator"""

    bl_idname = "outliner.remap_users"
    bl_label = "Remap Users"
    bl_options = {'INTERNAL', 'UNDO'}

    def update_library_path(self, context):
        # Prepare the ID selector.
        remap_targets = context.scene.remap_targets
        remap_targets.clear()
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        for id in get_id_storage(self.id_type):
            if id == source_id:
                continue
            if (self.library_path == 'Local Data' and not id.library) or (
                id.library and (self.library_path == id.library.filepath)
            ):
                id_entry = remap_targets.add()
                id_entry.name = id.name

    library_path: StringProperty(
        name="Library",
        description="Library path, if we want to remap to a linked ID",
        update=update_library_path,
    )
    id_type: StringProperty(description="ID type, eg. 'OBJECT' or 'MESH'")
    library_path_source: StringProperty()
    id_name_source: StringProperty(
        name="Source ID Name", description="Name of the ID we're remapping the users of"
    )
    id_name_target: StringProperty(
        name="Target ID Name", description="Name of the ID we're remapping users to"
    )

    def invoke(self, context, _event):
        # Populate the remap_targets string list with possible options based on
        # what was passed to the operator.

        assert (
            self.id_type and self.id_name_source
        ), "Error: UI must provide ID and ID type to this operator."

        # Prepare the library selector.
        remap_target_libraries = context.scene.remap_target_libraries
        remap_target_libraries.clear()
        local = remap_target_libraries.add()
        local.name = "Local Data"
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        for lib in bpy.data.libraries:
            for id in lib.users_id:
                if type(id) == type(source_id):
                    lib_entry = remap_target_libraries.add()
                    lib_entry.name = lib.filepath
                    break
        if source_id.name[-4] == ".":
            storage = get_id_storage(self.id_type)
            suggestion = storage.get(source_id.name[:-4])
            if suggestion:
                self.id_name_target = suggestion.name
                if suggestion.library:
                    self.library_path = suggestion.library.filepath
        else:
            self.library_path = "Local Data"

        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        row = layout.row()
        id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        id_icon = get_datablock_icon(id)
        split = row.split()
        split.row().label(text="Anything that was referencing this:")
        row = split.row()
        row.prop(self, 'id_name_source', text="", icon=id_icon)
        row.enabled = False

        layout.separator()
        col = layout.column()
        col.label(text="Will now reference this instead: ")
        if len(scene.remap_target_libraries) > 1:
            col.prop_search(
                self,
                'library_path',
                scene,
                'remap_target_libraries',
                icon=get_library_icon(self.library_path),
            )
        col.prop_search(
            self,
            'id_name_target',
            scene,
            'remap_targets',
            text="Datablock",
            icon=id_icon,
        )

    def execute(self, context):
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        target_id = get_id(self.id_name_target, self.id_type, self.library_path)
        assert source_id and target_id, "Error: Failed to find source or target."

        source_id.user_remap(target_id)
        return {'FINISHED'}


### Instance Collection To Scene
class OUTLINER_OT_instancer_empty_to_collection(bpy.types.Operator):
    """Replace an Empty that instances a collection, with the collection itself"""
    bl_idname = "outliner.instancer_empty_to_collection"
    bl_label = "Instancer Empty To Collection"
    bl_options = {'UNDO'}

    @staticmethod
    def should_draw(context):
        return (
            context.area.ui_type == 'OUTLINER' and \
            context.id and \
            type(context.id) == bpy.types.Object and \
            context.id.type == 'EMPTY' and \
            context.id.instance_type == 'COLLECTION' and \
            context.id.instance_collection and \
            context.id.instance_collection not in set(context.scene.collection.children)
        )

    @classmethod
    def poll(cls, context):
        return cls.should_draw(context)

    def execute(self, context):
        coll = context.id.instance_collection
        bpy.data.objects.remove(context.id)
        context.scene.collection.children.link(coll)

        return {'FINISHED'}


### ID utilities
# (ID Python type, identifier string, database name)
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


registry = [
    IDMAN_MT_relationship_pie,
    OUTLINER_OT_list_users_of_datablock,
    OUTLINER_OT_list_dependencies_of_datablock,
    RemapTarget,
    OUTLINER_OT_remap_users,
    OUTLINER_OT_instancer_empty_to_collection
]


addon_hotkeys = []

def register():
    addon_hotkeys.append(
        hotkeys.addon_hotkey_register(
            op_idname='wm.call_menu_pie',
            keymap_name='Outliner',
            key_id='Y',
            op_kwargs={'name': IDMAN_MT_relationship_pie.bl_idname},
            add_on_conflict=True,
            warn_on_conflict=True,
        )
    )

    bpy.types.Scene.remap_targets = CollectionProperty(type=RemapTarget)
    bpy.types.Scene.remap_target_libraries = CollectionProperty(type=RemapTarget)

def unregister():
    for pykmi in addon_hotkeys:
        pykmi.unregister()
