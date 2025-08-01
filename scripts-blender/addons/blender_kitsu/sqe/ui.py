# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .. import cache, prefs, ui, bkglobals
from ..sqe import checkstrip
from ..context import core as context_core
from ..logger import LoggerFactory
from ..sqe.ops import (
    KITSU_OT_sqe_push_new_sequence,
    KITSU_OT_sqe_push_new_shot,
    KITSU_OT_sqe_push_shot_meta,
    KITSU_OT_sqe_uninit_strip,
    KITSU_OT_sqe_unlink_shot,
    KITSU_OT_sqe_init_strip,
    KITSU_OT_sqe_link_shot,
    KITSU_OT_sqe_link_sequence,
    KITSU_OT_sqe_set_thumbnail_task_type,
    KITSU_OT_sqe_set_sqe_render_task_type,
    KITSU_OT_sqe_push_render_still,
    KITSU_OT_sqe_push_render,
    KITSU_OT_sqe_push_del_shot,
    KITSU_OT_sqe_pull_shot_meta,
    KITSU_OT_sqe_multi_edit_strip,
    KITSU_OT_sqe_debug_duplicates,
    KITSU_OT_sqe_debug_not_linked,
    KITSU_OT_sqe_debug_multi_project,
    KITSU_OT_sqe_pull_edit,
    KITSU_OT_sqe_init_strip_start_frame,
    KITSU_OT_sqe_create_metadata_strip,
    KITSU_OT_sqe_fix_metadata_strips,
    KITSU_OT_sqe_add_sequence_color,
    KITSU_OT_sqe_scan_for_media_updates,
    KITSU_OT_sqe_change_strip_source,
    KITSU_OT_sqe_clear_update_indicators,
    KITSU_OT_sqe_import_image_sequence,
    KITSU_OT_sqe_import_playblast,
)
from pathlib import Path

logger = LoggerFactory.getLogger()


def get_selshots_noun(nr_of_shots: int, prefix: str = "Active") -> str:
    if not nr_of_shots:
        noun = "All"
    elif nr_of_shots == 1:
        noun = f"{prefix} Shot"
    else:
        noun = "%i Shots" % nr_of_shots
    return noun


class KITSU_MT_sqe_advanced_delete(bpy.types.Menu):
    bl_label = "Advanced Delete"

    def draw(self, context: bpy.types.Context) -> None:
        selshots = context.selected_sequences
        strips_to_unlink = [s for s in selshots if s.kitsu.linked]

        layout = self.layout
        layout.operator(
            KITSU_OT_sqe_push_del_shot.bl_idname,
            text=f"Unlink and Delete {len(strips_to_unlink)} Shots",
            icon="CANCEL",
        )


class KITSU_PT_sqe_shot_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows all kinds of tools related to Kitsu and sequence strips
    """

    # TODO: Because each draw function was previously a seperate Panel there might be a lot of
    # code duplication now, needs to be refactored at some point

    bl_category = "Kitsu"
    bl_label = "Shot Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context_core.is_edit_context():
            return False
        sqe = context.scene.sequence_editor
        return bool(prefs.session_auth(context) or (sqe and sqe.sequences_all))

    def draw(self, context: bpy.types.Context) -> None:
        active_project = cache.project_active_get()
        if active_project.production_type == bkglobals.KITSU_TV_PROJECT:
            if not cache.episode_active_get():
                self.layout.label(text="Please Set Active Episode", icon="ERROR")
                return
        if self.poll_error(context):
            self.draw_error(context)

        if self.poll_setup(context):
            self.draw_setup(context)

        if self.poll_metadata(context):
            self.draw_metadata(context)

        if self.poll_offline_metadata(context):
            self.draw_offline_metadata(context)

        if self.poll_multi_edit(context):
            self.draw_multi_edit(context)

        if self.poll_push(context):
            self.draw_push(context)

        if self.poll_pull(context):
            self.draw_pull(context)
            self.draw_media(context)

        if self.poll_debug(context):
            self.draw_debug(context)

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        project_active = cache.project_active_get()
        addon_prefs = prefs.addon_prefs_get(context)

        if not prefs.session_auth(context):
            return False

        return bool(not project_active or not addon_prefs.is_project_root_valid)

    def draw_error(self, context: bpy.types.Context) -> None:
        layout = self.layout
        project_active = cache.project_active_get()
        box = ui.draw_error_box(layout)
        addon_prefs = prefs.addon_prefs_get(context)

        if not project_active:
            ui.draw_error_active_project_unset(box)

        if not addon_prefs.is_project_root_valid:
            ui.draw_error_invalid_project_root_dir(box)

    @classmethod
    def poll_setup(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_sequences)

    def draw_setup(self, context: bpy.types.Context) -> None:
        """
        Panel in SQE that shows operators to setup shots. That includes initialization,
        uninitizialization, linking and unlinking.
        """

        strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences
        nr_of_shots = len(selshots)
        noun = get_selshots_noun(nr_of_shots)
        project_active = cache.project_active_get()

        strips_to_init = []
        strips_to_uninit = []
        strips_to_unlink = []

        for s in selshots:
            if s.type not in checkstrip.VALID_STRIP_TYPES:
                continue
            if not s.kitsu.initialized:
                strips_to_init.append(s)
            elif s.kitsu.linked:
                strips_to_unlink.append(s)
            elif s.kitsu.initialized:
                strips_to_uninit.append(s)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Setup Shots", icon="TOOL_SETTINGS")

        # Production.
        if prefs.session_auth(context):
            box.row().label(text=f"Production: {project_active.name}")

        # Single Selection.
        if nr_of_shots == 1:
            row = box.row(align=True)

            # Initialize.
            if strip.type not in checkstrip.VALID_STRIP_TYPES:
                row.label(text=f"Only sequence strips of types: {checkstrip.VALID_STRIP_TYPES }")
                return

            if not strip.kitsu.initialized:
                # Init active.
                row.operator(KITSU_OT_sqe_init_strip.bl_idname, text=f"Init {noun}", icon="ADD")
                # Link active.
                row.operator(
                    KITSU_OT_sqe_link_shot.bl_idname,
                    text=f"Link {noun}",
                    icon="LINKED",
                )
                # Create metadata strip from uninitialized strip.
                row = box.row(align=True)
                row.operator(
                    KITSU_OT_sqe_create_metadata_strip.bl_idname,
                    text=f"Create Metadata Strip from {noun}",
                )

            # Unlink.
            elif strip.kitsu.linked:
                row = box.row(align=True)
                row.operator(
                    KITSU_OT_sqe_unlink_shot.bl_idname,
                    text=f"Unlink {noun}",
                    icon="UNLINKED",
                )
                row.menu("KITSU_MT_sqe_advanced_delete", icon="DOWNARROW_HLT", text="")

            # Uninitialize.
            else:
                row = box.row(align=True)
                # Unlink active.
                row.operator(
                    KITSU_OT_sqe_uninit_strip.bl_idname,
                    text=f"Uninitialize {noun}",
                    icon="REMOVE",
                )

        # Multiple Selection.
        elif nr_of_shots > 1:
            row = box.row(align=True)

            # Init.
            if strips_to_init:
                row.operator(
                    KITSU_OT_sqe_init_strip.bl_idname,
                    text=f"Init {len(strips_to_init)} Shots",
                    icon="ADD",
                )
                row = box.row(align=True)
                row.operator(
                    KITSU_OT_sqe_create_metadata_strip.bl_idname,
                    text=f"Create {len(strips_to_init)} Metadata Strips",
                )

            # Make row.
            if strips_to_uninit or strips_to_unlink:
                row = box.row(align=True)

            # Uninitialize.
            if strips_to_uninit:
                row.operator(
                    KITSU_OT_sqe_uninit_strip.bl_idname,
                    text=f"Uninitialize {len(strips_to_uninit)} Shots",
                    icon="REMOVE",
                )

            # Unlink all.
            if strips_to_unlink:
                row.operator(
                    KITSU_OT_sqe_unlink_shot.bl_idname,
                    text=f"Unlink {len(strips_to_unlink)} Shots",
                    icon="UNLINKED",
                )
                row.menu("KITSU_MT_sqe_advanced_delete", icon="DOWNARROW_HLT", text="")

    @classmethod
    def poll_metadata(cls, context: bpy.types.Context) -> bool:
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.kitsu.initialized
        return False

    def draw_metadata(self, context: bpy.types.Context) -> None:
        """
        Panel in sequence editor that shows .kitsu properties of active strip. (shot, sequence)
        """
        split_factor = 0.2

        strip = context.scene.sequence_editor.active_strip

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Metadata", icon="ALIGN_LEFT")

        col = box.column(align=True)

        # Sequence.
        split = col.split(factor=split_factor, align=True)
        split.label(text="Sequence")

        if not strip.kitsu.sequence_id:
            sub_row = split.row(align=True)
            sub_row.prop(strip.kitsu, "sequence_name", text="")
            sub_row.operator(KITSU_OT_sqe_push_new_sequence.bl_idname, text="", icon="ADD")

        else:
            # Lots of splitting because color prop is too big by default
            sub_split = split.split(factor=0.8, align=True)
            sub_split.prop(strip.kitsu, "sequence_name", text="")  # TODO Use new dropdown here too

            sub_sub_split = sub_split.split(factor=0.4, align=True)
            sub_sub_split.operator(KITSU_OT_sqe_push_new_sequence.bl_idname, text="", icon="ADD")

            try:
                sequence_color_item = context.scene.kitsu.sequence_colors[strip.kitsu.sequence_id]
            except KeyError:
                sub_sub_split.operator(
                    KITSU_OT_sqe_add_sequence_color.bl_idname, text="", icon="COLOR"
                )

            else:
                sub_sub_split.prop(sequence_color_item, "color", text="")

        # Shot.
        split = col.split(factor=split_factor, align=True)
        split.label(text="Shot")
        if not strip.kitsu.shot_id:
            placeholder = strip.kitsu.shot_name or ''
            split.prop(strip.kitsu, "manual_shot_name", text="", placeholder=placeholder)
        else:
            split.prop(strip.kitsu, "shot_name", text="")

        # Description.
        split = col.split(factor=split_factor, align=True)
        split.label(text="Description")
        split.prop(strip.kitsu, "shot_description_display", text="")
        split.enabled = False if not strip.kitsu.initialized else True

        # Frame range.
        split = col.split(factor=split_factor)
        split.label(text="Frame Range")
        row = split.row(align=False)
        row.prop(strip, "kitsu_3d_start", text="In")
        row.prop(strip, "kitsu_frame_end", text="Out")
        row.prop(strip, "kitsu_frame_duration", text="Duration")
        row.operator(KITSU_OT_sqe_init_strip_start_frame.bl_idname, text="", icon="FILE_REFRESH")

        """
        split = col.split(factor=split_factor)
        split.label(text="Offsets")
        row = split.row(align=False)
        row.prop(strip.kitsu, "frame_start_offset", text="In")
        """

    def poll_offline_metadata(cls, context: bpy.types.Context) -> bool:
        offline_metadata_strips = [
            strip
            for strip in context.scene.sequence_editor.sequences
            if strip.kitsu.shot_id != '' and not Path(strip.filepath).is_file()
        ]

        return len(offline_metadata_strips) > 0

    def draw_offline_metadata(self, context: bpy.types.Context) -> None:
        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Fix Metadata Strips", icon="ERROR")
        offline_metadata_strips = [
            strip
            for strip in context.selected_sequences
            if strip.kitsu.shot_id != '' and not Path(strip.filepath).is_file()
        ]
        if len(offline_metadata_strips) == 0:
            text = "Fix All Missing Media"
        else:
            text = f"Fix {len(offline_metadata_strips)} Missing Media"
        box.operator(KITSU_OT_sqe_fix_metadata_strips.bl_idname, text=text)

    @classmethod
    def poll_multi_edit(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            return False
        sel_shots = context.selected_sequences
        nr_of_shots = len(sel_shots)
        unvalid = [s for s in sel_shots if s.kitsu.linked or not s.kitsu.initialized]
        return bool(not unvalid and nr_of_shots > 1)

    def draw_multi_edit(self, context: bpy.types.Context) -> None:
        """
        Panel in sequence editor that can edit properties of multiple strips at one.
        Mostly used to quickly initialize lots of shots with an increasing counter.
        """

        addon_prefs = prefs.addon_prefs_get(context)

        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Multi Edit Metadata", icon="PROPERTIES")

        # Sequence
        col = box.column()
        sub_row = col.row(align=True)
        sub_row.prop(context.window_manager, "selected_sequence_name", text="Sequence")
        sub_row.operator(KITSU_OT_sqe_push_new_sequence.bl_idname, text="", icon="ADD")

        # Counter.
        row = box.row()
        row.prop(context.window_manager, "shot_counter_start", text="Shot Counter Start")
        row.prop(context.window_manager, "show_advanced", text="", icon="TOOL_SETTINGS")

        if context.window_manager.show_advanced:
            # Counter.
            box.row().prop(addon_prefs, "shot_counter_digits", text="Shot Counter Digits")
            box.row().prop(addon_prefs, "shot_counter_increment", text="Shot Counter Increment")

            # Variables.
            row = box.row(align=True)
            row.prop(
                context.window_manager,
                "var_use_custom_seq",
                text="Custom Sequence Variable",
            )
            if context.window_manager.var_use_custom_seq:
                row.prop(context.window_manager, "var_sequence_custom", text="")

            # Project.
            row = box.row(align=True)
            row.prop(
                context.window_manager,
                "var_use_custom_project",
                text="Custom Project Variable",
            )
            if context.window_manager.var_use_custom_project:
                row.prop(context.window_manager, "var_project_custom", text="")

            # Shot pattern.
            box.row().prop(addon_prefs, "shot_pattern", text="Shot Pattern")

        # Preview.
        row = box.row()
        row.prop(context.window_manager, "shot_preview", text="Preview")

        row = box.row(align=True)
        row.operator(
            KITSU_OT_sqe_multi_edit_strip.bl_idname,
            text=f"Set Metadata for {noun}",
            icon="ALIGN_LEFT",
        )

    @classmethod
    def poll_push(cls, context: bpy.types.Context) -> bool:
        # If only one strip is selected and it is not init then hide panel.
        if not prefs.session_auth(context):
            return False

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []
        strips_to_tb = []
        strips_to_submit = []

        for s in selshots:
            if s.kitsu.linked:
                strips_to_tb.append(s)
                strips_to_meta.append(s)

            elif s.kitsu.initialized and (s.kitsu.manual_shot_name != "" or s.kitsu.shot_name):
                strips_to_submit.append(s)

        return bool(strips_to_meta or strips_to_tb or strips_to_submit)

    def draw_push(self, context: bpy.types.Context) -> None:
        """
        Panel that shows operator to sync sequence editor metadata with backend.
        """
        nr_of_shots = len(context.selected_sequences)
        layout = self.layout
        strip = context.scene.sequence_editor.active_strip

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []
        strips_to_tb = []
        strips_to_submit = []
        strips_to_delete = []

        for s in selshots:
            if s.kitsu.linked:
                strips_to_tb.append(s)
                strips_to_meta.append(s)
                strips_to_delete.append(s)

            elif s.kitsu.initialized:
                if s.kitsu.shot_name and s.kitsu.sequence_name:
                    strips_to_submit.append(s)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Push", icon="EXPORT")
        # Special case if one shot is selected and it is init but not linked
        # shows the operator but it is not enabled until user types in required metadata.
        if nr_of_shots == 1 and not strip.kitsu.linked:
            # New operator.
            row = box.row()
            col = row.column(align=True)
            col.operator(
                KITSU_OT_sqe_push_new_shot.bl_idname,
                text="Submit New Shot",
                icon="ADD",
            )
            return

        # Either way no selection one selection but linked or multiple.

        # Metadata operator.
        row = box.row()
        if strips_to_meta:
            col = row.column(align=True)
            noun = get_selshots_noun(len(strips_to_meta), prefix=f"{len(strips_to_meta)}")
            col.operator(
                KITSU_OT_sqe_push_shot_meta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )

        # Thumbnail and seqeunce renderoperator.
        if strips_to_tb:
            # Upload thumbnail op.
            noun = get_selshots_noun(len(strips_to_tb), prefix=f"{len(strips_to_meta)}")
            split = col.split(factor=0.7, align=True)
            split.operator(
                KITSU_OT_sqe_push_render_still.bl_idname,
                text=f"Render Still {noun}",
                icon="IMAGE_DATA",
            )
            # Select task types op.
            noun = context.scene.kitsu.task_type_thumbnail_name or "Select Task Type"
            split.operator(
                KITSU_OT_sqe_set_thumbnail_task_type.bl_idname,
                text=noun,
                icon="DOWNARROW_HLT",
            )

            # Sqe render op.
            noun = get_selshots_noun(len(strips_to_tb), prefix=f"{len(strips_to_meta)}")
            split = col.split(factor=0.7, align=True)
            split.operator(
                KITSU_OT_sqe_push_render.bl_idname,
                text=f"Render Movie {noun}",
                icon="IMAGE_DATA",
            )
            # Select task types op.
            noun = context.scene.kitsu.task_type_sqe_render_name or "Select Task Type"
            split.operator(
                KITSU_OT_sqe_set_sqe_render_task_type.bl_idname,
                text=noun,
                icon="DOWNARROW_HLT",
            )

        # Submit operator.
        if nr_of_shots > 0:
            if strips_to_submit:
                noun = get_selshots_noun(len(strips_to_submit), prefix=f"{len(strips_to_submit)}")
                row = box.row()
                col = row.column(align=True)
                col.operator(
                    KITSU_OT_sqe_push_new_shot.bl_idname,
                    text=f"Submit {noun}",
                    icon="ADD",
                )

    @classmethod
    def poll_pull(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            return False

        selshots = context.selected_sequences
        all_shots = context.scene.sequence_editor.sequences_all

        if not selshots:  # Pull entire edit.
            return True

        strips_to_meta_sel = [s for s in selshots if s.kitsu.linked]
        strips_to_meta_all = [s for s in all_shots if s.kitsu.linked]

        if not selshots:
            return bool(strips_to_meta_all)
        return bool(strips_to_meta_sel)

    def draw_pull(self, context: bpy.types.Context) -> None:
        """
        Panel that shows operator to sync sequence editor metadata with backend.
        """

        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_meta = []

        for s in selshots:
            if s.kitsu.linked:
                strips_to_meta.append(s)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Pull", icon="IMPORT")

        layout = self.layout
        if strips_to_meta:
            noun = get_selshots_noun(len(strips_to_meta), prefix=f"{len(strips_to_meta)}")
            row = box.row()
            row.operator(
                KITSU_OT_sqe_pull_shot_meta.bl_idname,
                text=f"Metadata {noun}",
                icon="ALIGN_LEFT",
            )

        if not context.selected_sequences:
            row = box.row()
            row.operator(
                KITSU_OT_sqe_pull_edit.bl_idname,
                text=f"Pull entire Edit",
                icon="FILE_MOVIE",
            )

    @classmethod
    def poll_debug(cls, context: bpy.types.Context) -> bool:
        return prefs.addon_prefs_get(context).enable_debug

    def draw_debug(self, context: bpy.types.Context) -> None:
        nr_of_shots = len(context.selected_sequences)
        noun = get_selshots_noun(nr_of_shots)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Debug", icon="MODIFIER_ON")

        row = box.row()
        row.operator(
            KITSU_OT_sqe_debug_duplicates.bl_idname,
            text=f"Duplicates {noun}",
            icon="MODIFIER_ON",
        )
        row = box.row()
        row.operator(
            KITSU_OT_sqe_debug_not_linked.bl_idname,
            text=f"Not Linked {noun}",
            icon="MODIFIER_ON",
        )
        row = box.row()
        row.operator(
            KITSU_OT_sqe_debug_multi_project.bl_idname,
            text=f"Multi Projects {noun}",
            icon="MODIFIER_ON",
        )

    def draw_media(self, context: bpy.types.Context) -> None:
        sel_metadata_strips = [strip for strip in context.selected_sequences if strip.kitsu.linked]

        noun = get_selshots_noun(len(sel_metadata_strips), prefix=f"{len(sel_metadata_strips)}")
        playblast = "Playblast" if len(sel_metadata_strips) <= 1 else "Playblasts"

        sequence = "Sequence" if len(sel_metadata_strips) <= 1 else "Sequences"

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="Media", icon="RENDER_ANIMATION")
        box.operator(
            KITSU_OT_sqe_import_playblast.bl_idname,
            text=f"Import {noun} {playblast}",
            icon="FILE_MOVIE",
        )
        box.operator(
            KITSU_OT_sqe_import_image_sequence.bl_idname,
            text=f"Import {noun} Image {sequence}",
            icon="RENDER_RESULT",
        )


class KITSU_PT_sqe_general_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows tools that don't relate directly to Kitsu
    """

    bl_category = "Kitsu"
    bl_label = "General Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context_core.is_edit_context():
            return False
        selshots = context.selected_sequences

        sqe = context.scene.sequence_editor
        if not sqe:
            return False

        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all
        movie_strips = [s for s in selshots if s.type == "MOVIE"]
        return bool(movie_strips)

    def draw(self, context: bpy.types.Context) -> None:
        active_strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences
        if not selshots:
            selshots = context.scene.sequence_editor.sequences_all

        strips_to_update_media = []

        for s in selshots:
            if s.type == "MOVIE":
                strips_to_update_media.append(s)

        # Create box.
        layout = self.layout
        box = layout.box()
        box.label(text="General", icon="MODIFIER")

        # Scan for outdated media and reset operator.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_sqe_scan_for_media_updates.bl_idname,
            text=f"Check media update for {len(strips_to_update_media)} {'strip' if len(strips_to_update_media) == 1 else 'strips'}",
        )
        row.operator(KITSU_OT_sqe_clear_update_indicators.bl_idname, text="", icon="X")

        # Up down source operator. Check for to strips to accommodate linked strips
        if len(selshots) <= 2 and active_strip and active_strip.type == "MOVIE":
            row = box.row(align=True)
            row.prop(active_strip, "filepath_display", text="")
            row.operator(
                KITSU_OT_sqe_change_strip_source.bl_idname, text="", icon="TRIA_UP"
            ).direction = "UP"
            row.operator(
                KITSU_OT_sqe_change_strip_source.bl_idname, text="", icon="TRIA_DOWN"
            ).direction = "DOWN"
            row.operator(
                KITSU_OT_sqe_change_strip_source.bl_idname, text="", icon="FILE_PARENT"
            ).go_latest = True


# ---------REGISTER ----------.

classes = [
    KITSU_MT_sqe_advanced_delete,
    KITSU_PT_sqe_shot_tools,
    KITSU_PT_sqe_general_tools,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
