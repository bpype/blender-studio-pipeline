import bpy
from bpy.props import StringProperty
from .names import get_blender_number_suffix
from ..id_types import get_id


def get_desired_override_name(id):
    override = id.override_library
    if not override:
        return id.name
    suffix = get_blender_number_suffix(override.hierarchy_root.name)
    return override.reference.name + suffix


class BLENLOG_OT_report_library_overrides(bpy.types.Operator):
    """Report various issues relating to library overrides"""

    bl_idname = "blenlog.report_library_overrides"
    bl_label = "Report Library Overrides"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    def execute(self, context):
        blenlog = context.scene.blender_log

        leftovers = report_leftover_overrides(context)
        if leftovers:
            self.report(
                {'WARNING'}, f"There are override leftover collections in the file: {leftovers}"
            )

        cat_name_taken = "Override Name Occupied"
        blenlog.clear_category(cat_name_taken)

        cat_name_wrong = "Override Name Mismatch"
        blenlog.clear_category(cat_name_wrong)

        cat_name_conflict = "Override Name Conflict"
        blenlog.clear_category(cat_name_conflict)

        objects = [obj for obj in bpy.data.objects if obj.override_library]
        collections = [coll for coll in bpy.data.collections if coll.override_library]
        iter_stuff = [
            ('OBJECT', bpy.data.objects, objects),
            ('COLLECTION', bpy.data.collections, collections),
        ]
        counter = 0
        for id_type, propcoll, ids in iter_stuff:
            for id in ids:
                desired_name = get_desired_override_name(id)
                if id.name == desired_name:
                    continue
                counter += 1
                occupied = propcoll.get((desired_name, None))
                if occupied:
                    if get_desired_override_name(occupied) == occupied.name:
                        blenlog.add(
                            description=f"Inherent override name conflict! {id.name} should be named {desired_name}, which is already taken by an object that is named correctly. This issue cannot be fixed locally. The number suffix in the name must be removed in the original library ({id.override_library.reference.library.filepath}), or one of the overridden objects must be deleted.",
                            icon='LIBRARY_DATA_OVERRIDE',
                            name=id.name,
                            category=cat_name_conflict,
                        )
                    else:
                        blenlog.add(
                            description=f"Desired overridden {id_type} name '{desired_name}' is already taken from {id.name}. All names should be fixed recursively such that each ID is named after its reference library ID, plus the number suffix of the override hierarchy root.",
                            icon='LIBRARY_DATA_OVERRIDE',
                            name=id.name,
                            category=cat_name_taken,
                            operator=BLENLOG_OT_recursive_override_name_fix.bl_idname,
                            op_kwargs={'id_name': id.name, 'id_type': id_type},
                        )
                else:
                    blenlog.add(
                        description=f"Overridden object name doesn't match referenced library object name.",
                        icon='LIBRARY_DATA_OVERRIDE',
                        name=id.name,
                        category=cat_name_wrong,
                        operator='blenlog.rename_id',
                        op_kwargs={
                            'id_name': id.name,
                            'id_type': id_type,
                            'new_name': desired_name,
                        },
                    )

        if counter > 0:
            self.report({'WARNING'}, f"Found {counter} wrong override names.")
        else:
            self.report({'INFO'}, f"All overrides are named correctly.")

        return {'FINISHED'}


def report_leftover_overrides(context):
    blenlog = context.scene.blender_log
    category = 'Leftover Overrides'
    blenlog.clear_category(category)
    leftovers = [
        c
        for c in bpy.data.collections
        if c.name in {'OVERRIDE_RESYNC_LEFTOVERS', 'OVERRIDE_HIDDEN'}
    ]
    for leftover in leftovers:
        blenlog.add(
            description=f"Override Resync Leftovers are left behind when an override data hierarchy became ambiguous. This should be extremely rare. Check your overrides for any issues, then you can delete these leftovers.",
            icon='LIBRARY_DATA_OVERRIDE',
            name=leftover.name,
            category=category,
            operator=BLENLOG_OT_delete_collection_hierarchy.bl_idname,
            op_kwargs={
                'coll_name': leftover.name,
            },
        )
    return leftovers


class BLENLOG_OT_delete_collection_hierarchy(bpy.types.Operator):
    """Delete a collection hierarchy"""

    bl_idname = "blenlog.delete_collection_hierarchy"
    bl_label = "Delete Collection Hierarchy"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    coll_name: StringProperty()

    def execute(self, context):
        coll = bpy.data.objects.get((self.coll_name, None))
        if not coll:
            self.report({'INFO'}, f'Collection "{self.coll_name}" had already been removed.')
            return {'CANCELLED'}

        bpy.data.collections.remove(coll)
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)

        self.report(
            {'INFO'},
            f"Removed collection {self.coll_name} and purged the blend file of any unused datablocks.",
        )

        logs = context.scene.blender_log
        logs.remove(logs.active_log)

        return {'FINISHED'}


class BLENLOG_OT_recursive_override_name_fix(bpy.types.Operator):
    """Recursively rename override object names that occupy each other's names, to the correct suffixes. Useful when the object names of duplicated overrides get tangled up"""

    bl_idname = "blenlog.recursive_override_name_fix"
    bl_label = "Recursive Override Name Fix"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    id_name: StringProperty()
    id_type: StringProperty()

    def execute(self, context):
        blenlog = context.scene.blender_log

        id = get_id(self.id_name, self.id_type)
        if not id:
            self.report({'ERROR'}, f"{self.id_type} '{self.id_name}' no longer exists.")
            blenlog.remove_active()
            return {'CANCELLED'}

        override_recursive_rename(id)
        blenlog.remove_active()

        return {'FINISHED'}


def override_recursive_rename(override_id):
    """Try to rename an override object to its desired name, which is the name of its
    referenced link ID, plus this override's root hierarchy number suffix, if any."""
    desired_name = get_desired_override_name(override_id)
    if desired_name == override_id.name:
        return
    occupying = get_id(desired_name, override_id.id_type)
    if occupying:
        override_recursive_rename(occupying)
    print("Renaming ", override_id.name, "to", desired_name)
    override_id.name = desired_name


registry = [
    BLENLOG_OT_report_library_overrides,
    BLENLOG_OT_delete_collection_hierarchy,
    BLENLOG_OT_recursive_override_name_fix,
]
