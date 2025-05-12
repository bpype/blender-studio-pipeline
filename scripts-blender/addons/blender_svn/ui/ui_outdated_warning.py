# SPDX-License-Identifier: GPL-3.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import bpy


def draw_outdated_file_warning(self, context):
    repo = context.scene.svn.get_repo(context)
    current_file = None
    if not repo:
        return
    try:
        current_file = repo.current_blend_file
    except ValueError:
        # This can happen if the svn_directory property wasn't updated yet (not enough time has passed since opening the file)
        pass
    if not current_file:
        # If the current file is not in an SVN repository.
        return

    layout = self.layout
    row = layout.row()
    row.alert = True

    if current_file.status == 'conflicted':
        row.operator('svn.resolve_conflict',
                     text="SVN: This .blend file is conflicted.", icon='ERROR')
    elif current_file.repos_status != 'none' or context.scene.svn.file_is_outdated:
        op = row.operator('svn.revert_and_update_file', text="SVN: This .blend file may be outdated.", icon='ERROR')
        op.file_rel_path = repo.current_blend_file.svn_path


def register():
    bpy.types.TOPBAR_MT_editor_menus.append(draw_outdated_file_warning)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(draw_outdated_file_warning)
