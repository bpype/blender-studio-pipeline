# SPDX-License-Identifier: GPL-2.0-or-later
# (c) 2023, Blender Foundation - Demeter Dzadik

import time

import bpy
from bpy.types import UIList
from bpy.props import BoolProperty

from .. import constants
from ..util import get_addon_prefs, dots
from ..threaded.background_process import Processes


class SVN_UL_file_list(UIList):
    # Value that indicates that this item has passed the filter process successfully. See rna_ui.c.
    UILST_FLT_ITEM = 1 << 30

    show_file_paths: BoolProperty(
        name="Show File Paths",
        description="Show file paths relative to the SVN root, instead of just the file name"
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # As long as there are any items, always draw the filters.
        self.use_filter_show = True

        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        file_entry = item
        prefs = get_addon_prefs(context)

        main_row = layout.row()
        split = main_row.split(factor=0.6)
        filepath_ui = split.row()
        split = split.split(factor=0.4)
        status_ui = split.row(align=True)

        ops_ui = split.row(align=True)
        ops_ui.alignment = 'RIGHT'

        ops_ui.enabled = file_entry.status_prediction_type == 'NONE' and not prefs.is_busy

        if self.show_file_paths:
            filepath_ui.prop(file_entry, 'name', text="",
                             emboss=False, icon=file_entry.file_icon)
        else:
            filepath_ui.label(text=file_entry.file_name, icon=file_entry.file_icon)

        statuses = [file_entry.status]
        # SVN operations
        ops = []
        if file_entry.status in ['missing', 'deleted']:
            ops.append(ops_ui.operator(
                'svn.restore_file', text="", icon='LOOP_BACK'))
            if file_entry.status == 'missing':
                ops.append(ops_ui.operator(
                    'svn.remove_file', text="", icon='TRASH'))
        elif file_entry.status == 'added':
            ops.append(ops_ui.operator(
                'svn.unadd_file', text="", icon='REMOVE'))
        elif file_entry.status == 'unversioned':
            ops.append(ops_ui.operator('svn.add_file', text="", icon='ADD'))
            ops.append(ops_ui.operator(
                'svn.trash_file', text="", icon='TRASH'))

        elif file_entry.status == 'modified':
            ops.append(ops_ui.operator(
                'svn.revert_file', text="", icon='LOOP_BACK'))
            if file_entry.repos_status == 'modified':
                # The file isn't actually `conflicted` yet, by SVN's definition,
                # but it will be as soon as we try to commit or update.
                # I think it's better to let the user know in advance.
                statuses.append('conflicted')
                # Updating the file will create an actual conflict.
                ops.append(ops_ui.operator(
                    'svn.update_single', text="", icon='IMPORT'))

        elif file_entry.status == 'conflicted':
            ops.append(ops_ui.operator('svn.resolve_conflict',
                       text="", icon='TRACKING_CLEAR_FORWARDS'))
        elif file_entry.status in ['incomplete', 'obstructed']:
            ops.append(ops_ui.operator(
                'svn.cleanup', text="", icon='BRUSH_DATA'))
        elif file_entry.status == 'none':
            if file_entry.repos_status == 'added':
                # From user POV it makes a bit more sense to call a file that doesn't
                # exist yet "added" instead of "outdated".
                statuses.append('added')
            ops.append(ops_ui.operator(
                'svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status == 'normal' and file_entry.repos_status == 'modified':
            # From user POV, this file is outdated, not 'normal'.
            statuses = ['none']
            ops.append(ops_ui.operator(
                'svn.update_single', text="", icon='IMPORT'))
        elif file_entry.status in ['normal', 'external', 'ignored']:
            pass
        else:
            print("Unknown file status: ", file_entry.svn_path,
                  file_entry.status, file_entry.repos_status)

        for op in ops:
            if hasattr(op, 'file_rel_path'):
                op.file_rel_path = file_entry.svn_path

        # Populate the status icons.
        for status in statuses:
            icon = constants.SVN_STATUS_DATA[status][0]
            explainer = status_ui.operator(
                'svn.explain_status', text="", icon=icon, emboss=False)
            explainer.status = status
            explainer.file_rel_path = file_entry.svn_path

    @classmethod
    def cls_filter_items(cls, context, data, propname):
        """By moving all of this logic to a classmethod (and all the filter 
        properties to the addon preferences) we can find a visible entry
        from other UI code, allowing us to avoid situations where the active
        element becomes hidden."""
        flt_neworder = []
        list_items = getattr(data, propname)
        flt_flags = [file.show_in_filelist *
                     cls.UILST_FLT_ITEM for file in list_items]

        helper_funcs = bpy.types.UI_UL_list

        # This list should ALWAYS be sorted alphabetically.
        flt_neworder = helper_funcs.sort_items_by_name(list_items, "name")

        repo = context.scene.svn.get_repo(context)
        if not repo:
            return flt_flags, flt_neworder

        return flt_flags, flt_neworder

    def filter_items(self, context, data, propname):
        return type(self).cls_filter_items(context, data, propname)

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        Toggles are stored in addon preferences, see cls_filter_items().
        """
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'show_file_paths', text="",
                 toggle=True, icon="FILE_FOLDER")

        repo = context.scene.svn.get_repo(context)
        if repo:
            row.prop(repo, 'file_search_filter', text="")


def draw_process_info(context, layout):
    prefs = get_addon_prefs(context)
    process_message = ""
    any_error = False
    col = layout.column()
    for process in Processes.processes.values():
        if process.name not in {'Commit', 'Update', 'Log', 'Status', 'Authenticate'}:
            continue

        if process.error:
            row = col.row()
            row.alert = True
            warning = row.operator(
                'svn.clear_error', text=f"SVN {process.name}: Error Occurred. Hover to view", icon='ERROR')
            warning.process_id = process.name
            any_error = True
            break

        if process.is_running:
            message = process.get_ui_message(context)
            if message:
                message = message.replace("...", dots())
                process_message = f"SVN: {message}"

    if not any_error and process_message:
        col.label(text=process_message)
    if prefs.debug_mode:
        col.label(text="Processes: " +
                  ", ".join([p.name for p in Processes.running_processes]))


def draw_file_list(context, layout):
    prefs = get_addon_prefs(context)
    repo = prefs.active_repo
    if not repo:
        return

    if not repo.authenticated:
        row = layout.row()
        row.alert=True
        row.label(text="Repository is not authenticated.", icon='ERROR')
        return

    main_col = layout.column()
    main_row = main_col.row()
    split = main_row.split(factor=0.6)
    filepath_row = split.row()
    filepath_row.label(text="          Filepath")

    status_row = split.row()
    status_row.label(text="         Status")

    ops_row = main_row.row()
    ops_row.alignment = 'RIGHT'
    ops_row.label(text="Operations")

    row = main_col.row()
    row.template_list(
        "SVN_UL_file_list",
        "svn_file_list",
        repo,
        "external_files",
        repo,
        "external_files_active_index",
    )

    col = row.column()

    col.separator()
    col.operator("svn.commit", icon='EXPORT', text="")
    col.operator("svn.update_all", icon='IMPORT', text="").revision = 0

    col.separator()
    col.operator("svn.cleanup", icon='BRUSH_DATA', text="")


registry = [
    SVN_UL_file_list,
]
