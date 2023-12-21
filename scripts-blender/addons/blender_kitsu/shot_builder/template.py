import bpy
from pathlib import Path
from .core import link_data_block


# TODO add ability for custom templates
def get_template_dir() -> Path:
    return Path(__file__).absolute().parent.joinpath("templates")


def get_template_files() -> list[Path]:
    dir = get_template_dir()
    return list(dir.glob('*.blend'))


def get_template_for_task_type(task_type_short_name: str) -> Path:
    for file in get_template_files():
        if file.stem == task_type_short_name:
            return file


def replace_workspace_with_template(
    context: bpy.types.Context, task_type_short_name: str
):
    file_path = get_template_for_task_type(task_type_short_name).resolve().absolute()
    remove_prefix = "REMOVE-"
    if not file_path.exists():
        return

    # Mark Existing Workspaces for Removal
    for workspace in bpy.data.workspaces:
        if workspace.name.startswith(remove_prefix):
            continue
        workspace.name = remove_prefix + workspace.name

    file_path_str = file_path.__str__()
    with bpy.data.libraries.load(file_path_str) as (data_from, data_to):
        for workspace in data_from.workspaces:
            bpy.ops.wm.append(
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
            bpy.ops.workspace.delete()
    return True
