# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from pathlib import Path
from . import config


def list_dir_blend_files(p: Path) -> list[Path]:
    return list(p.glob('*.blend'))


def get_template_for_task_type(task_type_name: str) -> Path:
    # Find Custom Template in Config Dir if available
    for file in list_dir_blend_files(config.template_dir_get()):
        if file.stem.lower() == task_type_name.lower():
            return file
    # Fall back to example templates if no custom templates found
    for file in list_dir_blend_files(config.template_example_dir_get()):
        if file.stem.lower() == task_type_name.lower():
            return file


def replace_workspace_with_template(context: bpy.types.Context, task_type_name: str):
    if task_type_name is None:
        return
    file_path = get_template_for_task_type(task_type_name).resolve().absolute()
    remove_prefix = "REMOVE-"
    if not file_path.exists():
        return

    # Mark Existing Workspaces for Removal
    for workspace in bpy.data.workspaces:
        if workspace.name.startswith(remove_prefix):
            continue
        workspace.name = remove_prefix + workspace.name

    # Add EXEC_DEFAULT to all bpy,ops calls to ensure they are "blocking" calls
    file_path_str = file_path.__str__()
    with bpy.data.libraries.load(file_path_str) as (data_from, data_to):
        for workspace in data_from.workspaces:
            bpy.ops.wm.append(
                'EXEC_DEFAULT',
                filepath=file_path_str,
                directory=file_path_str + "/" + 'WorkSpace',
                filename=str(workspace),
            )

    for lib in bpy.data.libraries:
        if lib.filepath == file_path_str:
            bpy.data.libraries.remove(bpy.data.libraries.get(lib.name))
            break

    workspaces_to_remove = []
    for workspace in bpy.data.workspaces:
        if workspace.name.startswith(remove_prefix):
            workspaces_to_remove.append(workspace)

    # context.window.workspace = workspace
    for workspace in workspaces_to_remove:
        with context.temp_override(workspace=workspace):
            bpy.ops.workspace.delete('EXEC_DEFAULT')
    return True
