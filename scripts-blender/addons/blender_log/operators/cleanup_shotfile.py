"""
This script is meant to be executed by Blender Crawl on every single shot file,
hopefully removing any useless data, fixing some names, reporting missing links,
resyncing overrides, all without breaking anything.
"""

import bpy
from typing import Set
from bpy.types import Library
from bpy.props import BoolProperty
import os
from .relink_overridden_asset import relink_all_override_hierarchies


def clean_file(
    context, allow_remove_suffix=False, allow_replace_suffix=False, only_warn_local_issues=False
) -> int:
    # Reset frame to start.
    context.scene.frame_current = context.scene.frame_start

    # Enable Simplify (only in .anim files)
    if '.anim' in bpy.data.filepath:
        context.scene.render.use_simplify = True
        context.scene.render.simplify_subdivision = 0

    nuke_addon_properties()

    issue_counter = 0
    issue_counter += warn_primitive_names(only_local=only_warn_local_issues)
    issue_counter += warn_number_names(
        only_local=only_warn_local_issues,
        allow_remove_suffix=allow_remove_suffix,
        allow_replace_suffix=allow_replace_suffix,
    )
    issue_counter += warn_bad_libs()
    issue_counter += warn_broken_links()

    fix_local_obdata_names()

    return issue_counter


def nuke_override_hidden():
    nukelist = [c for c in bpy.data.collections if 'OVERRIDE_HIDDEN' in c.name]
    for coll in nukelist:
        bpy.data.collections.remove(coll)


def resync_overrides(context):
    ui_type = context.area.ui_type
    context.area.ui_type = 'OUTLINER'

    for coll in get_override_roots():
        with context.temp_override(collection=coll):
            bpy.ops.outliner.liboverride_troubleshoot_operation(
                type='OVERRIDE_LIBRARY_RESYNC_HIERARCHY', selection_set='SELECTED'
            )

    context.area.ui_type = ui_type


def get_override_roots():
    override_roots = set()
    for coll in bpy.data.collections:
        if coll.override_library:
            override_roots.add(coll.override_library.hierarchy_root)
    return override_roots


def warn_primitive_names(only_local=False) -> int:
    issue_counter = 0
    primitive_names = [
        "Plane",
        "Cube",
        "Circle",
        "Sphere",
        "Icosphere",
        "Cylinder",
        "Cone",
        "Torus",
        "Suzanne",
        "BezierCurve",
        "BezierCircle",
        "Empty",
        "Key",
        "Material",
    ]
    for id in bpy.data.user_map().keys():
        if (id.library or id.override_library) and only_local:
            continue
        if "WGT" in id.name:
            # Widgets are allowed to be named after primitives.
            continue
        for prim_name in primitive_names:
            if prim_name in id.name:
                msg = f"WARNING: Primitive name: {id.name}, {type(id)}"
                if id.override_library:
                    msg += " " + id.override_library.reference.library.filepath
                print(msg)
                issue_counter += 1
    return issue_counter


def warn_number_names(
    only_local=False, allow_remove_suffix=False, allow_replace_suffix=False
) -> int:
    issue_counter = 0
    all_ids = {id.name: id for id in bpy.data.user_map().keys()}
    all_local_ids = {id.name: id for id in all_ids.values() if not id.library}
    for name, id in all_ids.items():
        if (id.library or id.override_library) and only_local:
            continue

        if len(id.name) < 4:
            if type(id) == bpy.types.Brush:
                continue
            print("WARNING: Very short ID name: ", id.name, type(id))
            issue_counter += 1
            continue

        if id.name[-4] == ".":
            try:
                int(id.name[-3:])
            except:
                # Suffix is not a number, so it's fine.
                continue
            msg = "WARNING: Number suffix in name: " + id.name
            if id.override_library:
                msg += " " + id.override_library.reference.library.filepath
            if id.library:
                msg += " " + id.library.filepath
            if not id.override_library and not id.library:
                if allow_remove_suffix:
                    name_without_suffix = id.name[:-4]
                    existing = all_local_ids.get(name_without_suffix)
                    if not existing:
                        id.name = name_without_suffix
                elif allow_replace_suffix:
                    id.name = id.name[:-4] + "_" + id.name[-3:]
                else:
                    print(msg)
                    issue_counter += 1
            else:
                print(msg)
                issue_counter += 1

    return issue_counter


def fix_local_obdata_names():
    for o in bpy.data.objects:
        if o.library or o.override_library:
            continue

        if o.data:
            if (
                o.data.name != o.name
            ):  # This matters because for some reason, sometimes setting the name to what it already is, gives it a .001... lol.
                o.data.name = o.name
            if (
                hasattr(o.data, 'shape_keys')
                and o.data.shape_keys
                and o.data.shape_keys.name != o.name
            ):
                o.data.shape_keys.name = o.name


def warn_broken_links():
    issue_counter = 0
    for id in bpy.data.user_map().keys():
        if id.is_missing:
            msg = "MISSING ID: " + id.name
            if id.library:
                msg += " " + id.library.filepath
            print(msg)
            issue_counter += 1
    return issue_counter


def warn_bad_libs() -> int:
    issue_counter = 0

    invalid_libs = get_invalid_libraries()
    for invalid_lib in invalid_libs:
        print("INVALID LIBRARY: ", invalid_lib.filepath)
        issue_counter += 1

    absolute_libs = get_absolute_libraries()
    for absolute_lib in absolute_libs:
        print("ABSOLUTE LIBRARY: ", absolute_lib.filepath)
        issue_counter += 1

    return issue_counter


def get_invalid_libraries() -> Set[Library]:
    """Return a set of library datablocks whose filepath does not exist."""
    invalid_libs: Set[Library] = set()
    for l in bpy.data.libraries:
        if not os.path.exists(bpy.path.abspath(l.filepath)):
            invalid_libs.add(l)
    return invalid_libs


def get_absolute_libraries() -> Set[Library]:
    """Return a set of library datablocks whose filepaths are not relative."""
    abs_libs: Set[Library] = set()
    for lib in bpy.data.libraries:
        if not lib.filepath.startswith("//"):
            abs_libs.add(lib)
    return abs_libs


def nuke_addon_properties():
    property_blacklist = {"hops"}
    for id in bpy.data.user_map().keys():
        if id.library or id.override_library:
            continue
        for key in list(id.keys()):
            if key in property_blacklist:
                del id[key]


class OUTLINER_OT_cleanup_shotfile(bpy.types.Operator):
    bl_idname = "outliner.cleanup_shotfile"
    bl_label = "Cleanup Shotfile"

    bl_options = {'REGISTER', 'UNDO'}

    allow_remove_suffix: BoolProperty(
        name="Allow Removing Number Suffix",
        description="If a local ID has a .00x suffix, and it can be removed without conflicting with another existing ID, just do it",
        default=True,
    )
    allow_replace_suffix: BoolProperty(
        name="Allow Replacing Suffix Separator",
        description="If a local ID has a .00x suffix, change it to _00x instead. It's best to manually look over these cases first",
        default=False,
    )
    only_warn_local_issues: BoolProperty(
        name="Only Warn Local Issues",
        description="If an issue relates to a linked ID, don't warn about it",
        default=False,
    )
    relink_overrides: BoolProperty(
        name="Relink Overrides",
        description="Relink all overridden hierarchy roots. Keyframe any overridden RNA Paths that were overridden but not keyed. Preserve the assigned action, constraints, pointers. Only armatures will be editable overrides, unless there was an actual override on a non-armature object",
        default=False,
    )

    def execute(self, context):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True, do_linked_ids=True)

        if self.relink_overrides:
            # Relink ALL overridden assets from scratch, while (hopefully)
            # preserving all intentionally created data on them.
            relink_all_override_hierarchies(context)

        issue_count = clean_file(
            context,
            allow_remove_suffix=self.allow_remove_suffix,
            allow_replace_suffix=self.allow_replace_suffix,
            only_warn_local_issues=self.only_warn_local_issues,
        )

        if issue_count > 0:
            self.report(
                {'WARNING'},
                f"Cleanup complete. {issue_count} issues still need attention. See terminal for details.",
            )
        else:
            self.report({'INFO'}, "Cleanup complete. No remaining issues detected.")

        return {'FINISHED'}


registry = [OUTLINER_OT_cleanup_shotfile]
