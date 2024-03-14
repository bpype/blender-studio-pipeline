import bpy
from bpy import types
from typing import List, Optional
from bpy.props import StringProperty
from bpy_extras import id_map_utils

from .relink_overridden_asset import OUTLINER_OT_relink_overridden_asset, outliner_get_active_id
from .. import hotkeys
from ..id_types import get_datablock_icon, get_library_icon, get_id_storage_by_type_str


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
        pie.operator(OUTLINER_OT_list_dependencies_of_datablock.bl_idname, icon='LOOP_FORWARDS')
        # V
        pie.operator('outliner.better_purge', icon='TRASH')

        id = self.get_id(context)
        if id:
            # ^
            remap = pie.operator(
                'outliner.remap_users', icon='FILE_REFRESH', text="Remap Users"
            )
            remap.id_type = id.id_type
            remap.id_name_source = id.name
            if id.library:
                remap.library_path_source = id.library.filepath

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
            storage = get_id_storage_by_type_str(user.id_type)[1]
            if not storage:
                print("Error: Can't find storage: ", user.name, user.id_type)
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


class OUTLINER_OT_list_users_of_datablock(RelationshipOperatorMixin, bpy.types.Operator):
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


class OUTLINER_OT_list_dependencies_of_datablock(RelationshipOperatorMixin, bpy.types.Operator):
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


### Instance Collection To Scene
class OUTLINER_OT_instancer_empty_to_collection(bpy.types.Operator):
    """Replace an Empty that instances a collection, with the collection itself"""

    bl_idname = "outliner.instancer_empty_to_collection"
    bl_label = "Instancer Empty To Collection"
    bl_options = {'UNDO'}

    @staticmethod
    def should_draw(context):
        return (
            context.area.ui_type == 'OUTLINER'
            and context.id
            and type(context.id) == bpy.types.Object
            and context.id.type == 'EMPTY'
            and context.id.instance_type == 'COLLECTION'
            and context.id.instance_collection
            and context.id.instance_collection not in set(context.scene.collection.children)
        )

    @classmethod
    def poll(cls, context):
        return cls.should_draw(context)

    def execute(self, context):
        coll = context.id.instance_collection
        bpy.data.objects.remove(context.id)
        context.scene.collection.children.link(coll)

        return {'FINISHED'}


registry = [
    IDMAN_MT_relationship_pie,
    OUTLINER_OT_list_users_of_datablock,
    OUTLINER_OT_list_dependencies_of_datablock,
    OUTLINER_OT_instancer_empty_to_collection,
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


def unregister():
    for pykmi in addon_hotkeys:
        pykmi.unregister()
