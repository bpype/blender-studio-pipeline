# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from typing import List, Dict, Set, Optional, Tuple
from bpy.types import Collection, Object, Operator


def outliner_get_active_id(context):
    """Helper function for Blender 3.6 and 4.0 cross-compatibility."""
    if not context.area.type == 'OUTLINER':
        return

    if hasattr(context, 'id'):
        # Blender 4.0: Active ID is explicitly exposed to PyAPI, yay.
        return context.id
    elif len(context.selected_ids) > 0:
        # Blender 3.6 and below: We can only hope first selected ID happens to be the active one.
        return context.selected_ids[0]


class OUTLINER_OT_relink_overridden_asset(Operator):
    """Relink an overridden asset. Can be useful to recover assets from all sorts of broken states, but may lose un-keyed overridden values. Should preserve bone constraints, active actions of armatures, and any outside references to objects within the asset. Will also purge the .blend file and unlink the OVERRIDE_HIDDEN collection if present, out of necessity"""

    bl_idname = "object.relink_overridden_asset"
    bl_label = "Relink Overridden Asset"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return cls.get_id(context)

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self)

    @staticmethod
    def get_id(context) -> Optional[bpy.types.ID]:
        if context.area.type == 'OUTLINER':
            active_id = outliner_get_active_id(context)
            if not active_id:
                return
            if active_id.override_library:
                return active_id
        else:
            if context.object and context.object.override_library:
                return context.object
            elif context.collection and context.collection.override_library:
                return context.collection

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Relink this asset? Un-keyed values may get reset!")
        id = self.get_id(context)
        layout.prop(id.override_library, 'hierarchy_root')

    def execute(self, context):
        id = self.get_id(context)

        old_hierarchy_root = id.override_library.hierarchy_root
        relink_single_override_hierarchy(context, old_hierarchy_root)

        return {'FINISHED'}


def relink_all_override_hierarchies(context):
    hierarchy_roots = get_override_hierarchy_roots()
    new_hierarchy_roots = []

    for hierarchy_root in hierarchy_roots:
        print("Relinking override hierarchy: ", hierarchy_root.name)
        new_hierarchy_root = recreate_override_hierarchy(context, hierarchy_root)
        relink_data(new_hierarchy_root, hierarchy_root)
        insert_missing_keys(new_hierarchy_root, hierarchy_root)
        empty_map = remap_users_to_temp_empties(new_hierarchy_root, hierarchy_root)
        clear_collection_hierarchy_fake_user(hierarchy_root)
        remap_users_from_temp_empties(empty_map, new_hierarchy_root)
        new_hierarchy_roots.append(new_hierarchy_root)

    nuke_override_hidden()
    better_purge(context)

    for new_hierarchy_root in new_hierarchy_roots:
        restore_names(new_hierarchy_root)


def get_override_hierarchy_roots():
    hierarchy_roots = set()
    for coll in bpy.data.collections:
        if coll.override_library:
            parents = get_parent_collections(coll)
            if any([parent.library or parent.override_library for parent in parents]):
                # If this is a collection nested inside another override library, it is NOT considered a hierarchy root in this scene.
                continue
            hierarchy_roots.add(coll.override_library.hierarchy_root)
    return hierarchy_roots


def relink_single_override_hierarchy(context, hierarchy_root: Collection):
    new_hierarchy_root = recreate_override_hierarchy(context, hierarchy_root)

    relink_data(new_hierarchy_root, hierarchy_root)
    insert_missing_keys(new_hierarchy_root, hierarchy_root)
    empty_map = remap_users_to_temp_empties(new_hierarchy_root, hierarchy_root)

    clear_collection_hierarchy_fake_user(hierarchy_root)
    nuke_override_hidden()
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True, do_linked_ids=True)

    remap_users_from_temp_empties(empty_map, new_hierarchy_root)

    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True, do_linked_ids=True)
    restore_names(new_hierarchy_root)


def relink_data(new_hierarchy_root, old_hierarchy_root):
    new_to_old_obj_map = map_new_to_old_objects(new_hierarchy_root, old_hierarchy_root)

    for new_obj, old_obj in new_to_old_obj_map.items():
        # Re-link Object Constraints.
        if old_obj:
            for old_con in old_obj.constraints:
                if old_con.name not in new_obj.constraints:
                    new_obj.constraints.copy(old_con)
                    # Mark Object with added constraints as editable.
                    new_obj.override_library.is_system_override = False

        if new_obj.type == 'ARMATURE':
            # Re-link Action.
            if old_obj.animation_data and old_obj.animation_data.action:
                new_obj.animation_data_create()
                new_obj.animation_data.action = old_obj.animation_data.action

            # Re-link Pose Constraints.
            for pb_old in old_obj.pose.bones:
                pb_new = new_obj.pose.bones[pb_old.name]
                for old_con in pb_old.constraints:
                    if old_con.name not in pb_new.constraints:
                        pb_new.constraints.copy(old_con)


def map_new_to_old_objects(
    new_hierarchy_root: Collection,
    old_hierarchy_root: Collection,
) -> Dict[Object, Object]:
    """Use the common linked ID reference of two override collection hierarchies to
    construct a name-agnostic object mapping from one to the other."""
    assert (
        new_hierarchy_root.override_library.reference.library
        == old_hierarchy_root.override_library.reference.library
    ), "The two collections must be an override of the same linked collection."

    new_to_old_obj_map = {}

    old_link_map = map_objects_of_linked_to_override_hierarchy(old_hierarchy_root)

    for new_obj in new_hierarchy_root.all_objects:
        if not new_obj.override_library:
            # Some objects could still be directly linked, ie. rig widgets.
            continue
        ref = old_link_map.get(new_obj.override_library.reference)
        if ref:
            new_to_old_obj_map[new_obj] = ref

    return new_to_old_obj_map


def recreate_override_hierarchy(context, old_hierarchy_root: Collection) -> Collection:
    """Create a fresh overridden copy of an existing overridden collection,
    replacing it in existing collections with the fresh copy.
    - All collection assignments are preserved
    - Only Armature objects are marked as editable
    """
    linked_hierarchy_root = old_hierarchy_root.override_library.reference

    parent_colls = collection_unlink_from_parents(old_hierarchy_root)
    assert (
        parent_colls
    ), "Expected the override hierarchy root to be assigned to at least one parent collection."

    override_hierarchy_root = linked_hierarchy_root.override_hierarchy_create(
        context.scene, context.view_layer
    )

    # By default, this gets linked to the scene's root. We don't want that.
    context.scene.collection.children.unlink(override_hierarchy_root)

    # Link the collection to the parent collections.
    for parent_coll in parent_colls:
        parent_coll.children.link(override_hierarchy_root)

    for obj in override_hierarchy_root.all_objects:
        if obj.type == 'ARMATURE':
            obj.override_library.is_system_override = False

    return override_hierarchy_root


def get_overridden_but_not_animated_properties(
    hierarchy_root: Collection,
) -> Dict[Object, List[str]]:
    obj_to_prop_list_map = {}
    for obj in hierarchy_root.all_objects:
        props_that_need_keying = []
        if not obj.override_library or not obj.override_library.reference:
            continue
        all_overridden_props = [prop.rna_path for prop in obj.override_library.properties]

        driven_props = []
        animated_props = []
        if obj.animation_data and obj.animation_data.drivers:
            driven_props = [fcurve.data_path for fcurve in obj.animation_data.drivers]
        if obj.animation_data and obj.animation_data.action:
            animated_props = [fcurve.data_path for fcurve in obj.animation_data.action.fcurves]

        for overridden_prop in all_overridden_props:
            if overridden_prop not in driven_props and overridden_prop not in animated_props:
                props_that_need_keying.append(overridden_prop)

        if props_that_need_keying:
            obj_to_prop_list_map[obj.override_library.reference] = props_that_need_keying

    return obj_to_prop_list_map


def insert_missing_keys(new_hierarchy_root, old_hierarchy_root):
    old_overridden_not_animated = get_overridden_but_not_animated_properties(old_hierarchy_root)
    new_overridden_not_animated = get_overridden_but_not_animated_properties(new_hierarchy_root)

    old_link_map = map_objects_of_linked_to_override_hierarchy(old_hierarchy_root)
    new_link_map = map_objects_of_linked_to_override_hierarchy(new_hierarchy_root)

    for linked_obj, old_prop_list in old_overridden_not_animated.items():
        if not old_prop_list or linked_obj not in new_overridden_not_animated:
            continue

        new_prop_list = new_overridden_not_animated[linked_obj]
        missing = []
        for rna_path in old_prop_list:
            if rna_path in ['animation_data.action']:
                # This should be overridden by now, not sure why it shows up here...
                continue
            if "is_active" in rna_path:
                continue
            owner_path, prop_name = rna_path_split_owner(rna_path)
            if prop_name in ["", "name", "mute", "lock", "nla_tracks"]:
                continue
            if rna_path not in new_prop_list:
                missing.append(rna_path)

        if missing:
            old_override_obj = old_link_map[linked_obj]
            new_override_obj = new_link_map[linked_obj]
            print(f"{old_override_obj.name} had manually overridden but not animated RNA paths: ")
            for rna_path in missing:
                old_value = old_override_obj.path_resolve(rna_path)
                owner_path, prop_name = rna_path_split_owner(rna_path)
                new_owner = new_override_obj.path_resolve(owner_path)
                setattr(new_owner, prop_name, old_value)
                success = new_owner.keyframe_insert(prop_name)
                if success:
                    print("    Inserted keyframe:", rna_path, old_value)
                else:
                    print("    Failed to insert keyframe ", rna_path, old_value)


def rna_path_split_owner(rna_path: str) -> Tuple[str, str]:
    """Split the last part of an RNA path from the rest.
    This supports 2 cases:
    Either the path ends in `.some_prop`
    Or it ends in a custom property name which looks `["like this"]`.
    """
    if rna_path.endswith('"]'):
        owner, prop = rna_path.rsplit('["', maxsplit=1)
        prop = '["' + prop
        return owner, prop
    elif "." in rna_path:
        return rna_path.rsplit(".", maxsplit=1)
    else:
        return rna_path, ""


def remap_users_to_temp_empties(new_hierarchy_root, old_hierarchy_root) -> Dict[Object, Object]:
    # We need to remap users from the old to the new objects, but doing
    # that in a straight forward way causes a crash.
    # So, let's create placeholder objects for each old object, that will
    # get user remapped to, then delete all the old stuff, then user remap from the placeholders to the new objects.

    empty_map = {}

    old_objs = list(old_hierarchy_root.all_objects) + get_objects_in_override_hidden(
        new_hierarchy_root
    )

    for old_obj in old_objs:
        if not old_obj.override_library or not old_obj.override_library.reference:
            continue
        # Create an empty object corresponding to each old object...
        name = "REMAP_" + str(old_obj.name)
        empty = bpy.data.objects.new(name=name, object_data=None)
        empty.use_fake_user = True
        old_obj.user_remap(empty)
        empty_map[old_obj.override_library.reference] = empty

    return empty_map


def remap_users_from_temp_empties(empty_map, new_hierarchy_root):
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
                print("Multiple overriding IDs, not sure which one to assign:", linked_id)


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


def map_objects_of_linked_to_override_hierarchy(
    root_override: bpy.types.Collection,
) -> Dict[bpy.types.Object, bpy.types.Object]:
    """Map linked objects to their overrides, given a hierarchy root of that override."""
    obj_map = {}
    for obj in root_override.all_objects:
        if not obj.override_library:
            continue
        obj_map[obj.override_library.reference] = obj
    return obj_map


def restore_names(override_root: bpy.types.Collection):
    for obj in override_root.all_objects:
        if obj.override_library and obj.name != obj.override_library.reference.name:
            obj.name = obj.override_library.reference.name
    for coll in [override_root] + override_root.children_recursive:
        if coll.override_library and coll.name != coll.override_library.reference.name:
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

    link_map = map_objects_of_linked_to_override_hierarchy(override_hidden)

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
    nukelist = [c for c in bpy.data.collections if 'OVERRIDE_HIDDEN' in c.name]
    for coll in nukelist:
        bpy.data.collections.remove(coll)


def get_objects_in_override_hidden(
    linked_collection: bpy.types.Collection,
) -> List[bpy.types.Object]:
    override_hidden_list = [c for c in bpy.data.collections if 'OVERRIDE_HIDDEN' in c.name]
    if not override_hidden_list:
        return []

    all_linked_objs = list(linked_collection.all_objects)
    ret = []

    for coll in override_hidden_list:
        for obj in coll.all_objects:
            if not obj.override_library:
                continue
            if obj.override_library.reference in all_linked_objs:
                ret.append(obj)

    return ret


def draw_relink_ui(self, context):
    self.layout.separator()
    self.layout.operator(OUTLINER_OT_relink_overridden_asset.bl_idname, text="Purge & Re-link")


registry = [
    OUTLINER_OT_relink_overridden_asset,
]


def register():
    bpy.types.VIEW3D_MT_object_liboverride.append(draw_relink_ui)
    bpy.types.OUTLINER_MT_liboverride.append(draw_relink_ui)


def unregister():
    bpy.types.OUTLINER_MT_liboverride.append(draw_relink_ui)
    bpy.types.OUTLINER_MT_liboverride.remove(draw_relink_ui)
