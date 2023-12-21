from pathlib import Path
import bpy


def save_shot_builder_file(file_path: str):
    """Save Shot File within Folder of matching name.
    Set Shot File to relative Paths."""
    if Path(file_path).exists():
        raise Exception(f"Cannot Overwrite Existing Shot File {file_path}")
    dir_path = Path(file_path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_mainfile(filepath=file_path, relative_remap=True)
