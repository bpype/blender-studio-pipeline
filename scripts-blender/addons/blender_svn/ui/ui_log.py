# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import IntProperty, BoolProperty
from bpy.types import UIList, Panel, Operator
from ..util import get_addon_prefs


class SVN_UL_log(UIList):
    show_all_logs: BoolProperty(
        name='Show All Logs',
        description='Show the complete SVN Log, instead of only entries that affected the currently selected file',
        default=False
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type != 'DEFAULT':
            raise NotImplemented

        svn = data
        log_entry = item

        num, auth, date, msg = layout_log_split(layout.row())

        active_file = svn.active_file
        num.label(text=str(log_entry.revision_number))
        if item.revision_number == active_file.revision:
            num.operator('svn.tooltip_log', text="", icon='LAYER_ACTIVE',
                         emboss=False).log_rev = log_entry.revision_number
        elif log_entry.changes_file(active_file):
            get_older = num.operator(
                'svn.download_file_revision', text="", icon='IMPORT', emboss=False)
            get_older.revision = log_entry.revision_number
            get_older.file_rel_path = active_file.svn_path
        auth.label(text=log_entry.revision_author)
        date.label(text=log_entry.revision_date_simple)

        commit_msg = log_entry.commit_message
        commit_msg = commit_msg.split(
            "\n")[0] if "\n" in commit_msg else commit_msg
        commit_msg = commit_msg[:50] + \
            "..." if len(commit_msg) > 52 else commit_msg
        msg.alignment = 'LEFT'
        msg.operator("svn.display_commit_message", text=commit_msg,
                     emboss=False).log_rev = log_entry.revision_number

    def filter_items(self, context, data, propname):
        """Custom filtering functionality:
        - Always sort by descending revision number
        - Allow searching for various criteria
        """
        svn = data
        log_entries = getattr(data, propname)

        # Start off with all entries flagged as visible.
        flt_flags = [self.bitflag_filter_item] * len(log_entries)
        # Always sort by descending revision number
        flt_neworder = sorted(range(len(log_entries)),
                              key=lambda i: log_entries[i].revision_number)
        flt_neworder.reverse()

        if not self.show_all_logs:
            flt_flags = [
                log_entry.affects_active_file * self.bitflag_filter_item
                for log_entry in log_entries
            ]

        if self.filter_name:
            # Filtering: Allow comma-separated keywords.
            # ALL keywords must be found somewhere in the log entry for it to show up.
            filter_words = [word.strip().lower()
                            for word in self.filter_name.split(",")]
            for idx, log_entry in enumerate(log_entries):
                for filter_word in filter_words:
                    if filter_word not in log_entry.text_to_search:
                        flt_flags[idx] = 0
                        break

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        """Custom filtering UI.
        """
        main_row = layout.row()
        main_row.prop(self, 'filter_name', text="")
        main_row.prop(self, 'show_all_logs', text="",
                      toggle=True, icon='ALIGN_JUSTIFY')


def is_log_useful(context) -> bool:
    """Return whether the log has any useful info to display."""

    prefs = get_addon_prefs(context)
    repo = prefs.active_repo

    if not repo or not repo.authenticated:
        return False

    if len(repo.log) == 0 or len(repo.external_files) == 0:
        return False
    active_file = repo.active_file
    if active_file.status in ['unversioned', 'added']:
        return False

    any_visible = any([file.show_in_filelist for file in repo.external_files])
    if not any_visible:
        return False

    return True


class VIEW3D_PT_svn_log(Panel):
    """Display the revision history of the selected file."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVN'
    bl_label = 'Revision History'
    bl_parent_id = "VIEW3D_PT_svn_files"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return is_log_useful(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        draw_svn_log(context, layout)


def layout_log_split(layout):
    main = layout.split(factor=0.4)
    num_and_auth = main.row()
    date_and_msg = main.row()

    num_and_auth_split = num_and_auth.split(factor=0.5)
    num = num_and_auth_split.row()
    auth = num_and_auth_split.row()

    date_and_msg_split = date_and_msg.split(factor=0.3)
    date = date_and_msg_split.row()
    msg = date_and_msg_split.row()

    return num, auth, date, msg


def draw_svn_log(context, layout):
    num, auth, date, msg = layout_log_split(layout.row())
    num.label(text="Rev. #")
    auth.label(text="Author")
    date.label(text="Date")
    msg.label(text="Message")

    prefs = get_addon_prefs(context)
    repo = prefs.active_repo
    layout.template_list(
        "SVN_UL_log",
        "svn_log",
        repo,
        "log",
        repo,
        "log_active_index",
    )

    active_log = repo.active_log
    if not active_log:
        return
    layout.label(text="Revision Date: " + active_log.revision_date)

    layout.label(
        text=f"Files changed in revision `r{active_log.revision_number}`:")

    col = layout.column(align=True)
    row = col.row()
    split = row.split(factor=0.80)
    split.label(text="          Filepath")
    row = split.row()
    row.alignment = 'RIGHT'
    row.label(text="Action")
    for f in active_log.changed_files:
        row = col.row()
        split = row.split(factor=0.90)
        split.prop(f, 'name', emboss=False, text="", icon=f.file_icon)
        row = split.row()
        row.alignment = 'RIGHT'
        row.operator('svn.explain_status', text="",
                     icon=f.status_icon, emboss=False).status = f.status


def execute_tooltip_log(self, context):
    """Set the index on click, to act as if this operator button was 
    click-through in the UIList."""
    repo = context.scene.svn.get_repo(context)
    tup = repo.get_log_by_revision(self.log_rev)
    if tup:
        repo.log_active_index = tup[0]
    return {'FINISHED'}


class SVN_OT_log_tooltip(Operator):
    bl_idname = "svn.tooltip_log"
    bl_label = ""  # Don't want the first line of the tooltip on mouse hover.
    # bl_description = "An operator to be drawn in the log list, that can display a dynamic tooltip"
    bl_options = {'INTERNAL'}

    log_rev: IntProperty(
        description="Revision number of the log entry to show in the tooltip"
    )

    @classmethod
    def description(cls, context, properties):
        return "This is the currently checked out version of the file"

    execute = execute_tooltip_log


class SVN_OT_log_show_commit_msg(Operator):
    bl_idname = "svn.display_commit_message"
    bl_label = ""  # Don't want the first line of the tooltip on mouse hover.
    # bl_description = "Show the currently active commit, using a dynamic tooltip"
    bl_options = {'INTERNAL'}

    log_rev: IntProperty(
        description="Revision number of the log entry to show in the tooltip"
    )

    @classmethod
    def description(cls, context, properties):
        log_entry = context.scene.svn.get_repo(context).get_log_by_revision(properties.log_rev)[
            1]
        commit_msg = log_entry.commit_message

        # Prettify the tooltips.
        pretty_msg = ""
        for line in commit_msg.split("\n"):
            # Remove leading/trailing whitespace
            line = line.strip()

            # Add punctuation mark
            if not (line.endswith(".") or line.endswith("!") or line.endswith("?")):
                line = line + "."

            # Split long lines into several
            limit = 300
            if len(line) > limit:
                words = line.split(" ")
                sub_lines = []

                new_line = ""
                for word in words:
                    if len(new_line) + len(word) < limit:
                        new_line += " "+word
                    else:
                        sub_lines.append(new_line)
                        new_line = word
                else:
                    sub_lines.append(new_line)
                line = "\n".join(sub_lines)

            pretty_msg += "\n"+line

        # Remove last period because Blender adds it.
        if pretty_msg.endswith("."):
            pretty_msg = pretty_msg[:-1]

        return pretty_msg

    execute = execute_tooltip_log


registry = [
    VIEW3D_PT_svn_log,
    SVN_UL_log,
    SVN_OT_log_tooltip,
    SVN_OT_log_show_commit_msg
]
