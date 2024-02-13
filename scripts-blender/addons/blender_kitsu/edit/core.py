import bpy
from .. import prefs
import re
from pathlib import Path


def edit_export_get_latest(context: bpy.types.Context):
    """Find latest export in editorial export directory"""
    addon_prefs = prefs.addon_prefs_get(context)

    edit_export_path = Path(addon_prefs.edit_export_dir)

    files_list = [
        f
        for f in edit_export_path.iterdir()
        if f.is_file()
        and edit_export_is_valid_edit_name(addon_prefs.edit_export_file_pattern, f.name)
    ]
    if len(files_list) >= 1:
        files_list = sorted(files_list, reverse=True)
        return files_list[0]
    return None


def edit_export_is_valid_edit_name(file_pattern: str, filename: str) -> bool:
    """Verify file name matches file pattern set in preferences"""
    # Prevents un-expected matches
    file_pattern = re.escape(file_pattern)
    # Replace `#` with `\d` to represent digits
    match = re.search(file_pattern.replace('\#', '\d'), filename)
    if match:
        return True
    return False
