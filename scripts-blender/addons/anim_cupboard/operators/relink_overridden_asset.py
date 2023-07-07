import bpy
from typing import List, Dict, Set, Optional, Tuple


class OUTLINER_OT_better_purge(bpy.types.Operator):
    """Like Blender's purge, but clears fake users from linked IDs and collections"""
    bl_idname = "outliner.better_purge"
    bl_label = "Better Purge"

    def execute(self, context):
        better_purge(context)
        return {'FINISHED'}


class OUTLINER_OT_relink_overridden_asset(bpy.types.Operator):
    """Relink an overridden asset. Can be useful to recover assets from all sorts of broken states, but may lose un-keyed overridden values. Should preserve bone constraints, active actions of armatures, and any outside references to objects within the asset. Will also purge the .blend file and unlink the OVERRIDE_HIDDEN collection if present, out of necessity"""
    bl_idname = "object.relink_overridden_asset"
    bl_label = "Relink Overridden Asset"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.override_library

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Relink this asset?")
        layout.prop(context.object.override_library, 'hierarchy_root')

    def execute(self, context):
        outliners = [
            area for area in bpy.context.screen.areas if area.type == 'OUTLINER']
        if not outliners:
            self.report(
                {'ERROR'}, "This operation requires an Outliner to be present somewhere on the screen.")
            return {'CANCELLED'}

        active_ob = context.object
        old_hierarchy_root = active_ob.override_library.hierarchy_root
        linked_hierarchy_root = old_hierarchy_root.override_library.reference

        parent_colls = collection_unlink_from_parents(old_hierarchy_root)
        assert parent_colls, "Expected the override hierarchy root to be assigned to at least one parent collection."
        clear_collection_hierarchy_fake_user(old_hierarchy_root)
        # action_map = map_actions_to_armatures(hierarchy_root)

        # Create an override of the collection hierarchy.
        # By default, this creates non-editable, aka "System" overrides.
        new_hierarchy_root = linked_hierarchy_root.override_hierarchy_create(
            context.scene, context.view_layer)
        # By default, this gets linked to the scene's root.
        context.scene.collection.children.unlink(new_hierarchy_root)

        # Link the collection to the parent collections.
        for parent_coll in parent_colls:
            parent_coll.children.link(new_hierarchy_root)

        old_link_map = map_objects_of_linked_to_override_hierarchy(
            old_hierarchy_root)

        new_to_old_obj_map = {}
        for new_obj in new_hierarchy_root.all_objects:
            if not new_obj.override_library:
                # Some objects could still be directly linked, ie. rig widgets.
                continue
            ref = old_link_map.get(new_obj.override_library.reference)
            if ref:
                new_to_old_obj_map[new_obj] = ref

        for new_obj in new_hierarchy_root.all_objects:
            if new_obj.type != 'ARMATURE':
                continue
            # Mark Armature object overrides as editable.
            new_obj.override_library.is_system_override = False

            # Re-link Action.
            old_obj = new_to_old_obj_map.get(new_obj)
            if not old_obj:
                continue

            if old_obj.animation_data and old_obj.animation_data.action:
                new_obj.animation_data_create()
                new_obj.animation_data.action = old_obj.animation_data.action

            # Re-link Constraints.
            for pb_old in old_obj.pose.bones:
                pb_new = new_obj.pose.bones[pb_old.name]
                for idx, old_con in enumerate(pb_old.constraints):
                    if old_con.name not in pb_new.constraints:
                        pb_new.constraints.copy(pb_old.constraints[idx])

        # We need to remap users from the old to the new objects, but doing 
        # that in a straight forward way causes a crash.
        # So, let's create placeholder objects for each old object, that will 
        # get user remapped to, then delete all the old stuff, then user remap from the placeholders to the new objects.

        empty_map = {}

        old_objs = list(old_hierarchy_root.all_objects) + get_objects_in_override_hidden(new_hierarchy_root)

        for old_obj in old_objs:
            if not old_obj.override_library:
                continue
            # Create an empty object corresponding to each old object...
            name = "REMAP_" + str(old_obj.name)
            empty = bpy.data.objects.new(name=name, object_data=None)
            empty.use_fake_user = True
            old_obj.user_remap(empty)
            empty_map[old_obj.override_library.reference] = empty

        nuke_override_hidden()
        better_purge(context)

        for new_obj in list(new_hierarchy_root.all_objects):
            if not new_obj.override_library:
                continue
            # Map users from empty to new obj, then delete the empty
            empty = empty_map.get(new_obj.override_library.reference)
            if not empty:
                continue
            empty.user_remap(new_obj)
            empty_map.pop(new_obj.override_library.reference)
            bpy.data.objects.remove(empty)

        for empty in empty_map.values():
            # This usually won't do anything, but since we gave them fake users, let's keep it here just in case.
            bpy.data.objects.remove(empty)

        better_purge(context)
        restore_names(new_hierarchy_root)

        for new_obj in new_hierarchy_root.all_objects:
            if new_obj.type == 'ARMATURE':
                # Mark Armature object overrides as editable. (Why doesn't the earlier copy of this code not work??)
                new_obj.override_library.is_system_override = False

        return {'FINISHED'}


def better_purge(context, clear_coll_fake_users=True):
    """Call Blender's purge function, but first Python-override all library IDs' 
    use_fake_user to False.
    Otherwise, linked IDs essentially do not get purged properly.
    """

    if clear_coll_fake_users:
        for coll in bpy.data.collections:
            coll.use_fake_user = False

    id_list = list(bpy.data.user_map().keys())
    for id in id_list:
        if id.library:
            id.use_fake_user = False

    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=True)


def rename_override_objects():
    """Try renaming overridden objects back to the name of the linked ID they are overriding."""
    for o in bpy.data.objects:
        if not o.override_library:
            continue
        desired_name = o.override_library.reference.name
        if o.name == desired_name:
            continue

        occupier = bpy.data.objects.get((desired_name, None))
        if occupier:
            new_name = occupier.name + ".temp"
            occupier.name = new_name

        print("Renaming ob: ", o.name, " -> ", desired_name)
        o.name = desired_name

        if occupier:
            occupier.name = o.name


def get_mapping_from_linked_to_overriding_ids() -> Dict[bpy.types.ID, List[bpy.types.ID]]:
    """Build a mapping from linked datablocks to their override IDs."""
    override_map = {}
    for o in bpy.data.objects:
        if o.override_library:
            linked_id = o.override_library.reference
            if linked_id not in override_map:
                override_map[linked_id] = []
            override_map[linked_id].append(o)
    return override_map


def reassign_objects_to_collections():
    """This function would re-assign objects to the right collections; 
    This is blocked by the PyAPI though, so this code doesn't actually work."""
    override_map = get_mapping_from_linked_to_overriding_ids()

    for coll in bpy.context.scene.collection.children_recursive:
        if not coll.override_library:
            continue
        linked_coll = coll.override_library.reference
        for linked_id in linked_coll.objects:
            override_ids = override_map.get(linked_id)
            if not override_ids:
                continue
            if len(override_ids) == 1:
                override = override_ids[0]
                if not override.name in coll.objects:
                    coll.objects.link(override)
            else:
                print(
                    "Multiple overriding IDs, not sure which one to assign:", linked_id)


def get_parent_collections(target_coll: bpy.types.Collection) -> Set[bpy.types.Collection]:
    """Return a set of the parents of a collection."""
    parent_colls = set()
    for parent_coll in [scene.collection for scene in bpy.data.scenes] + list(bpy.data.collections):
        for child_coll in parent_coll.children:
            if child_coll == target_coll:
                parent_colls.add(parent_coll)
    return parent_colls


def collection_unlink_from_parents(coll: bpy.types.Collection) -> Set[bpy.types.Collection]:
    """Unlink a collection from all of its parents, and return a set of those parents."""
    parent_colls = get_parent_collections(coll)
    for parent_coll in parent_colls:
        parent_coll.children.unlink(coll)
    return parent_colls


def clear_collection_hierarchy_fake_user(coll: bpy.types.Collection):
    """Set the Fake User flag of a collection and all of its children to False,
    so that it can be purged."""
    for coll in [coll] + coll.children_recursive:
        coll.use_fake_user = False


def map_actions_to_armatures(coll: bpy.types.Collection) -> Dict[str, Tuple[bpy.types.Action, bool]]:
    """Give Actions a fake user, and then map each armature's name to the action it's assigned."""
    action_map = {}
    for obj in coll.all_objects:
        if obj.type != 'ARMATURE':
            continue
        if obj.animation_data and obj.animation_data.action:
            action_map[obj.override_library.reference.name] = (
                obj.animation_data.action, obj.animation_data.action.use_fake_user)
            obj.animation_data.action.use_fake_user = True

    return action_map


def map_objects_of_linked_to_override_hierarchy(
        root_override: bpy.types.Collection) -> Dict[bpy.types.Object, bpy.types.Object]:
    """Map linked objects to their overrides, given a hierarchy root of that override."""
    obj_map = {}
    for obj in root_override.all_objects:
        if not obj.override_library:
            continue
        obj_map[obj.override_library.reference] = obj
    return obj_map


def restore_names(override_root: bpy.types.Collection):
    for obj in override_root.all_objects:
        if obj.override_library:
            obj.name = obj.override_library.reference.name
    for coll in [override_root] + override_root.children_recursive:
        if coll.override_library:
            coll.name = coll.override_library.reference.name

def __cleanup_override_hidden(override_root: bpy.types.Collection):
    """This sadly doesn't work.
    It was meant to unlink only those objects from the OVERRIDE_HIDDEN collection,
    which have copies in the passet override_root collection (override referencing same linked ID)

    But I don't have time to troubleshoot it; It's easier to just nuke the OVERRIDE_HIDDEN collection.
    """
    override_hidden = bpy.data.collections.get('OVERRIDE_HIDDEN')
    if not override_hidden:
        return
    
    link_map = map_objects_of_linked_to_override_hierarchy(
            override_hidden)

    print("LINK MAP:")
    for key, value in link_map.items():
        print(key, " : ", value)

    objs_to_remove = []

    for obj in override_root.all_objects:
        if not obj.override_library:
            continue
        hidden_obj = link_map.get(obj.override_library.reference)
        if not hidden_obj:
            continue
        print("MATCH: ", obj, " : ", hidden_obj)
        objs_to_remove.append(hidden_obj)

    for obj in objs_to_remove:
        override_hidden.objects.unlink(obj)

def nuke_override_hidden():
    override_hidden = bpy.data.collections.get('OVERRIDE_HIDDEN')
    if not override_hidden:
        return
    bpy.data.collections.remove(override_hidden)

def get_objects_in_override_hidden(linked_collection: bpy.types.Collection) -> List[bpy.types.Object]:
    override_hidden = bpy.data.collections.get('OVERRIDE_HIDDEN')
    if not override_hidden:
        return []

    all_linked_objs = list(linked_collection.all_objects)
    ret = []

    for obj in override_hidden.all_objects:
        if not obj.override_library:
            continue
        if obj.override_library.reference in all_linked_objs:
            ret.append(obj)

    return ret


def draw_relink_ui(self, context):
    self.layout.separator()
    self.layout.operator(OUTLINER_OT_relink_overridden_asset.bl_idname, text="Purge & Re-link")

def draw_purge_ui(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(OUTLINER_OT_better_purge.bl_idname)


registry = [
    OUTLINER_OT_better_purge,
    OUTLINER_OT_relink_overridden_asset,
]


def register():
    bpy.types.TOPBAR_MT_file_cleanup.append(draw_purge_ui)

    bpy.types.VIEW3D_MT_object_liboverride.append(draw_relink_ui)
    bpy.types.OUTLINER_MT_liboverride.append(draw_relink_ui)

def unregister():
    bpy.types.TOPBAR_MT_file_cleanup.remove(draw_purge_ui)

    bpy.types.OUTLINER_MT_liboverride.append(draw_relink_ui)
    bpy.types.OUTLINER_MT_liboverride.remove(draw_relink_ui)
