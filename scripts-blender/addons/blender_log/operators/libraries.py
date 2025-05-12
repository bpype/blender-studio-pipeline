# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import StringProperty

from pathlib import Path


def report_missing_libraries(context, libraries=[]):
    if not libraries:
        libraries = bpy.data.libraries

    blenlog = context.scene.blender_log
    cat_missing = "Missing Library"
    blenlog.clear_category(cat_missing)

    for lib in libraries:
        if lib.is_missing:
            blenlog.add(
                name=lib.filepath,
                description="Library file is not found on file system.",
                category=cat_missing,
                category_icon='LIBRARY_DATA_BROKEN',
                # operator='outliner.lib_operation',    # This operator demands to be run in the outliner for no particular reason.
                # op_kwargs={'type': 'RELOCATE'},
            )

    return blenlog.categories.get(cat_missing)


def report_absolute_libraries(context, libraries=[]):
    if not libraries:
        libraries = bpy.data.libraries

    blenlog = context.scene.blender_log
    cat_absolute = "Absolute Library"
    blenlog.clear_category(cat_absolute)

    for lib in libraries:
        if not lib.filepath.startswith("//"):
            blenlog.add(
                name=lib.filepath,
                description=f"{lib.filepath}\nLibrary path is not relative to this .blend, but absolute.",
                category=cat_absolute,
                category_icon='FILEBROWSER',
                # operator='outliner.lib_operation',
                # op_kwargs={'type': 'RELOCATE'},
            )

    return blenlog.categories.get(cat_absolute)


def report_libraries_out_of_folder(context, project_path: Path or str, libraries=[]):
    if type(project_path) == str:
        project_path = Path(project_path)

    if not libraries:
        libraries = bpy.data.libraries

    blenlog = context.scene.blender_log
    cat_not_prod = "Library Outside Project"
    blenlog.clear_category(cat_not_prod)

    for lib in libraries:
        abs_path = Path(bpy.path.abspath(lib.filepath)).resolve()
        if project_path not in abs_path.parents:
            blenlog.add(
                name=lib.filepath,
                description=f"{lib.filepath}\nLibrary is not a part of this project.",
                category=cat_not_prod,
                category_icon='ERROR',
                # operator='outliner.lib_operation',
                # op_kwargs={'type': 'RELOCATE'},
            )

    return blenlog.categories.get(cat_not_prod)


class BLENLOG_OT_report_missing_libraries(bpy.types.Operator):
    """Report libraries whose files don't exist on the system"""

    bl_idname = "blenlog.report_missing_libraries"
    bl_label = "Report Missing Libraries"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        category = report_missing_libraries(context, bpy.data.libraries)

        if len(category.logs) > 0:
            self.report({'WARNING'}, f"Found {len(category.logs)} missing libraries.")
        else:
            self.report({'INFO'}, f"No missing libraries found.")

        return {'FINISHED'}


class BLENLOG_OT_report_absolute_libraries(bpy.types.Operator):
    """Report libraries whose filepath is referenced absolute rather than relative"""

    bl_idname = "blenlog.report_absolute_libraries"
    bl_label = "Report Absolute Libraries"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        category = report_absolute_libraries(context, bpy.data.libraries)

        if len(category.logs) > 0:
            self.report({'WARNING'}, f"Found {len(category.logs)} absolute libraries.")
        else:
            self.report({'INFO'}, f"No absolute libraries found.")

        return {'FINISHED'}


class BLENLOG_OT_report_libraries_out_of_folder(bpy.types.Operator):
    """Report libraries whose filepath is outside of a specified folder"""

    bl_idname = "blenlog.report_libraries_out_of_folder"
    bl_label = "Report Libraries Out of Folder"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    project_root_path: StringProperty(
        name="Project Root Path",
        subtype='DIR_PATH',
        description="Your project's root directory. Any libraries outside of this will be reported",
    )

    def execute(self, context):
        category = report_libraries_out_of_folder(
            context, bpy.data.libraries, self.project_root_path
        )

        if len(category.logs) > 0:
            self.report(
                {'WARNING'}, f"Found {len(category.logs)} libraries outside of the project root."
            )
        else:
            self.report({'INFO'}, f"No libraries outside of project found.")

        return {'FINISHED'}


registry = [
    BLENLOG_OT_report_missing_libraries,
    BLENLOG_OT_report_absolute_libraries,
    BLENLOG_OT_report_libraries_out_of_folder,
]
