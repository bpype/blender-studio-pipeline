import bpy
from bpy.props import StringProperty, CollectionProperty
from ..id_types import get_id, get_id_storage_by_type_str, get_datablock_icon, get_library_icon


class BLENLOG_OT_report_fake_users(bpy.types.Operator):
    """Report Fake User IDs. Ignores Text and Brush IDs"""

    bl_idname = "blenlog.report_fake_users"
    bl_label = "Report Fake Users"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        user_map = bpy.data.user_map()

        blenlog = context.scene.blender_log

        category = "Fake User ID"
        blenlog.clear_category(category)

        for id, users in user_map.items():
            if id.library or id.override_library:
                continue
            if id.id_type not in {'BRUSH', 'TEXT'} and id.use_fake_user:
                blenlog.add(
                    name=f"{id.id_type}: {id.name} (Users: {len(users)})",
                    category=category,
                    description="Datablocks with fake users can cause further referenced datablocks to linger in the file. It is recommended not to use fake users, in order to keep files clear of trash data.",
                    icon='FAKE_USER_ON',
                    operator=BLENLOG_OT_clear_fake_user.bl_idname,
                    op_kwargs={'id_name': id.name, 'id_type': id.id_type},
                    op_icon='FAKE_USER_OFF',
                )

        return {'FINISHED'}


class BLENLOG_OT_remap_users(bpy.types.Operator):
    """Remap users of an ID to another of the same type"""

    bl_idname = "blenlog.remap_users"
    bl_label = "Remap Users"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    redundant_id: StringProperty()
    id_type: StringProperty()
    preserved_id: StringProperty()

    def execute(self, context):
        redundant_id = get_id(self.redundant_id, self.id_type)
        if not redundant_id:
            self.report({'ERROR'}, f"ID no longer exists: {self.redundant_id}.")
            return {'CANCELLED'}
        preserved_id = get_id(self.preserved_id, self.id_type)
        if not preserved_id:
            self.report({'ERROR'}, f"ID no longer exists: {self.preserved_id}.")
            return {'CANCELLED'}

        redundant_id.user_remap(preserved_id)
        redundant_id.use_fake_user = False
        self.report({'INFO'}, f"{self.redundant_id} has been replaced with {self.preserved_id}")

        context.scene.blender_log.remove_active()

        return {'FINISHED'}


### Remap Users
class RemapTarget(bpy.types.PropertyGroup):
    pass


class BLENLOG_OT_remap_users_ui(bpy.types.Operator):
    """Remap users of a selected ID to any other ID of the same type"""

    bl_idname = "outliner.remap_users"
    bl_label = "Remap Users"
    bl_options = {'INTERNAL', 'UNDO'}

    def update_library_path(self, context):
        # Prepare the ID selector.
        remap_targets = context.scene.remap_targets
        remap_targets.clear()
        source_id = get_id(self.id_name_source, self.id_type, self.library_path_source)
        for id in get_id_storage_by_type_str(self.id_type):
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
            storage = get_id_storage_by_type_str(self.id_type)
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


class BLENLOG_OT_clear_fake_user(bpy.types.Operator):
    """Clear the fake user flag of an ID."""

    bl_idname = "blenlog.clear_fake_user"
    bl_label = "Clear Fake User"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    id_name: StringProperty()
    id_type: StringProperty()

    def execute(self, context):
        id = get_id(self.id_name, self.id_type)
        if not id:
            self.report({'INFO'}, f"{self.id_type} {self.id_name} had already been removed.")
        else:
            id.use_fake_user = False
            self.report(
                {'INFO'}, f"{self.id_type} {self.id_name} no longer marked with a fake user."
            )

        context.scene.blender_log.remove_active()

        return {'FINISHED'}


class BLENLOG_OT_report_missing_IDs(bpy.types.Operator):
    """Report Fake User IDs. Ignores Text and Brush IDs"""

    bl_idname = "blenlog.report_missing_ids"
    bl_label = "Report Missing IDs"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        user_map = bpy.data.user_map()

        blenlog = context.scene.blender_log

        category = "Missing ID"
        blenlog.clear_category(category)

        for id, users in user_map.items():

            if id.library or id.override_library:
                continue
            if id.id_type not in {'BRUSH', 'TEXT'} and id.use_fake_user:
                blenlog.add(
                    name=f"{id.id_type}: {id.name} (Users: {len(users)})",
                    category=category,
                    description="A linked ID was being referenced locally, and then removed from its library. The missing ID can be remapped to another.",
                    icon='LIBRARY_DATA_BROKEN',
                    operator=BLENLOG_OT_clear_fake_user.bl_idname,
                    op_kwargs={'id_name': id.name, 'id_type': id.id_type},
                    op_icon='FAKE_USER_OFF',
                )

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_fake_users,
    BLENLOG_OT_remap_users,
    RemapTarget,
    BLENLOG_OT_remap_users_ui,
    BLENLOG_OT_clear_fake_user,
]


def register():
    bpy.types.Scene.remap_targets = CollectionProperty(type=RemapTarget)
    bpy.types.Scene.remap_target_libraries = CollectionProperty(type=RemapTarget)


def unregister():
    del bpy.types.Scene.remap_targets
    del bpy.types.Scene.remap_target_libraries
