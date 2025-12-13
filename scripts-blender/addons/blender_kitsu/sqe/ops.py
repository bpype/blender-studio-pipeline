# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import re

from bpy.types import Context
import gazu
import contextlib
import colorsys
import random
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import datetime
import bpy
from .. import cache, util, prefs, bkglobals
from ..sqe import push, pull, checkstrip, opsdata, checksqe

from ..logger import LoggerFactory
from ..types import (
    Cache,
    Sequence,
    Shot,
    TaskType,
    TaskStatus,
    Task,
)

logger = LoggerFactory.getLogger()


class KITSU_OT_sqe_push_shot_meta(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_shot_meta"
    bl_label = "Push Shot Metadata"
    bl_options = {"INTERNAL"}
    bl_description = (
        "Pushes metadata of all selected strips to server. "
        "This includes frame information, name, project, sequence and description"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pushing Metadata")

        # Get strips.
        selected_strips = context.selected_strips
        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        # Sort strips.
        selected_strips = sorted(selected_strips, key=lambda strip: strip.frame_final_start)

        # Begin progress update.
        context.window_manager.progress_begin(0, len(selected_strips))

        # Clear cache.
        Cache.clear_all()

        # Track sequence ids that were processed to later update sequence.data["color"] on kitu.
        sequence_ids: List[str] = []

        # Shots.
        for idx, strip in enumerate(selected_strips):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # Failed.append(strip).
                continue

            # Only if strip is linked to sevrer.
            if not checkstrip.is_linked(strip):
                # Failed.append(strip).
                continue

            # Check if shot is still available by id.
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                logger.error(
                    "Strip '%s' does not have a valid shot id on Kitsu.",
                    strip.name,
                )
                continue

            # Push update to shot.
            push.shot_meta(strip, shot)

            # Append sequence id.
            if shot.parent_id not in sequence_ids:
                sequence_ids.append(shot.parent_id)

            succeeded.append(strip)

        # End progress update.
        context.window_manager.progress_update(len(selected_strips))
        context.window_manager.progress_end()

        # Sequences.

        # Begin second progress update for strips.
        context.window_manager.progress_begin(0, len(sequence_ids))
        for idx, seq_id in enumerate(sequence_ids):
            context.window_manager.progress_update(idx)

            sequence = Sequence.by_id(seq_id)
            opsdata.push_sequence_color(context, sequence)

        # End second progress update.
        context.window_manager.progress_update(len(sequence_ids))
        context.window_manager.progress_end()

        # Report.
        report_str = f"Pushed Metadata of {len(succeeded)} Shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Pushing Metadata")

        return {"FINISHED"}


class KITSU_OT_sqe_push_new_shot(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_new_shot"
    bl_label = "Submit New Shot"
    bl_description = "Creates a new shot for each selected sequence strip on server. Checks if shot already exists"

    confirm: bpy.props.BoolProperty(name="confirm")
    add_tasks: bpy.props.BoolProperty(name="Add Default Tasks")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Needs to be logged in, active project.
        strips = context.selected_strips
        if not strips:
            return False
        nr_of_shots = len(strips)
        if nr_of_shots == 1:
            strip = context.scene.sequence_editor.active_strip
            return bool(
                prefs.session_auth(context)
                and cache.project_active_get()
                and strip.kitsu.sequence_name
                and (strip.kitsu.manual_shot_name or strip.kitsu.shot_name)
            )

        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Submit new shots aborted")
            return {"CANCELLED"}

        project_active = cache.project_active_get()
        succeeded = []
        failed = []
        no_sequence_id = []
        logger.info("-START- Submitting new shots to: %s", project_active.name)

        # Clear cache.
        Cache.clear_all()

        # Get strips.
        selected_strips = context.selected_strips
        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        # Sort strips.
        selected_strips = sorted(selected_strips, key=lambda strip: strip.frame_final_start)

        # Begin progress update.
        context.window_manager.progress_begin(0, len(selected_strips))

        for idx, strip in enumerate(selected_strips):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # Failed.append(strip).
                continue

            # Check if user initialized shot.
            if not checkstrip.is_initialized(strip):
                # Failed.append(strip).
                continue

            # Check if strip is already linked to server.
            if checkstrip.is_linked(strip):
                failed.append(strip)
                logger.error(
                    "Strip '%s' is already linked to the kitsu server.",
                    strip.name,
                )
                continue

            # Check if user provided enough info.
            if not checkstrip.has_meta(strip):
                failed.append(strip)
                logger.error(
                    "Strip '%s' didn't have the required kitsu metadata.",
                    strip.name,
                )
                continue

            if strip.kitsu.sequence_id == "":
                no_sequence_id.append(strip)
                continue

            # Check if seq already to server  > create it.
            seq = checkstrip.seq_exists_by_id(strip, project_active, clear_cache=False)
            if not seq:
                seq = push.new_sequence(strip, project_active)

            # Check if shot already to server  > create it.
            shot = checkstrip.shot_exists_by_name(strip, project_active, seq, clear_cache=False)
            if shot:
                failed.append(strip)
                logger.error(
                    "The shot for strip '%s' couldn't be created on Kitsu.",
                    strip.name,
                )
                continue

            if strip.kitsu.manual_shot_name:
                strip.kitsu.shot_name = strip.kitsu.manual_shot_name

            # Push update to sequence.
            opsdata.push_sequence_color(context, seq)

            # Push update to shot.
            shot = push.new_shot(strip, seq, project_active, add_tasks=self.add_tasks)
            pull.shot_meta(strip, shot)
            succeeded.append(strip)

            # Rename strip.
            strip.name = shot.name

        # End progress update.
        context.window_manager.progress_update(len(selected_strips))
        context.window_manager.progress_end()

        # Clear cache.
        Cache.clear_all()

        # Report.
        report_str = f"Submitted {len(succeeded)} new shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"
        if no_sequence_id:
            report_state = "WARNING"
            report_str += f" | Sequence metadata was not set for: {len(failed)} strips"
        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Submitting new shots to: %s", project_active.name)
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        project_active = cache.project_active_get()
        selected_strips = context.selected_strips
        layout = self.layout

        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        strips_to_submit = [
            s
            for s in selected_strips
            if s.kitsu.initialized
            and not s.kitsu.linked
            and (s.kitsu.manual_shot_name or s.kitsu.sequence_name)
        ]

        if len(selected_strips) > 1:
            noun = "%i Shots" % len(strips_to_submit)
        else:
            noun = "this Shot"

        # Production.
        row = layout.row()
        row.label(text=f"Production: {project_active.name}", icon="FILEBROWSER")

        # Confirm dialog.
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit %s to server. Will skip shots if they already exist" % (noun.lower()),
        )
        col.prop(self, "add_tasks", text="Add Tasks with the default status to shot(s)")


class KITSU_OT_sqe_push_new_sequence(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_new_sequence"
    bl_label = "Submit New Sequence"
    bl_description = "Creates new sequence on server. Will skip if sequence already exists"

    sequence_name: bpy.props.StringProperty(
        name="Name", default="", description="Name of new sequence"
    )
    confirm: bpy.props.BoolProperty(name="confirm", default=True)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Needs to be logged in, active project.
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Submit new sequence aborted")
            return {"CANCELLED"}

        if not self.sequence_name:
            self.report({"WARNING"}, "Invalid sequence name")
            return {"CANCELLED"}

        project_active = cache.project_active_get()
        episode_active = cache.episode_active_get()

        sequence = project_active.get_sequence_by_name(self.sequence_name, episode_active)

        if sequence:
            self.report(
                {"WARNING"},
                f"Sequence: {sequence.name} already exists on server",
            )
            return {"CANCELLED"}

        # Create sequence.
        sequence = project_active.create_sequence(
            self.sequence_name,
            episode_active.id if episode_active else None,
        )

        # Push sequence color.
        opsdata.push_sequence_color(context, sequence)

        # Clear cache.
        Cache.clear_all()
        cache.reset_strips_enum_list()

        self.report(
            {"INFO"},
            f"Submitted new sequence: {sequence.name}",
        )

        # Avoids circular import
        from .ui import KITSU_PT_sqe_shot_tools as seq_tools

        # set newly created sequence as target for multi edit or active strip
        if seq_tools.poll_multi_edit(context):
            context.window_manager.selected_sequence_name = sequence.name
        else:
            context.active_strip.kitsu.sequence_name = sequence.name

        logger.info("Submitted new sequence: %s", sequence.name)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        project_active = cache.project_active_get()

        # Production.
        row = layout.row()
        row.label(text=f"Production: {project_active.name}", icon="FILEBROWSER")

        # Sequence name.
        row = layout.row()
        row.prop(self, "sequence_name")

        # Confirm dialog.
        col = layout.column()
        col.prop(
            self,
            "confirm",
            text="Submit sequence to server. Will skip if already exists",
        )


class KITSU_OT_sqe_init_strip(bpy.types.Operator):
    """
    Operator that initializes a regular sequence strip to a 'kitsu' shot.
    Only sets strip.kitsu.initialized = True. But this is required for further
    operations and to  differentiate between regular sequence strip and kitsu shot strip.
    """

    bl_idname = "kitsu.sqe_init_strip"
    bl_label = "Initialize Shot"
    bl_description = "Initializes selected sequence strip as kitsu strip"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Initializing shots")

        # Get strips.
        selected_strips = context.selected_strips
        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        # Sort strips.
        selected_strips = sorted(selected_strips, key=lambda strip: strip.frame_final_start)

        for strip in selected_strips:
            if not checkstrip.is_valid_type(strip):
                continue

            if strip.kitsu.initialized:
                logger.info("%s already initialized", strip.name)
                continue

            strip.kitsu.initialized = True

            # Apply strip.kitsu.frame_start_offset.
            opsdata.init_start_frame_offset(strip)

            succeeded.append(strip)
            logger.info("Initiated strip: %s as shot", strip.name)

        # Report.
        report_str = f"Initiated {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Initializing shots")
        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_link_sequence(bpy.types.Operator):
    """
    Gets all sequences that are available in server for active production and lets user select. Invokes a search popup on click.
    """

    bl_idname = "kitsu.sqe_link_sequence"
    bl_label = "Link Sequence"
    bl_options = {"REGISTER", "UNDO"}
    bl_property = "enum_prop"
    bl_description = "Links selected sequence strip to an existing sequence on server"

    enum_prop: bpy.props.EnumProperty(
        items=cache.get_sequences_enum_list,
    )  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        strip = sqe.active_strip
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and strip
            and context.selected_strips
            and checkstrip.is_valid_type(strip)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip
        sequence_id = self.enum_prop
        if not sequence_id:
            return {"CANCELLED"}

        # Set sequence properties.
        seq = Sequence.by_id(sequence_id)
        strip.kitsu.sequence_name = seq.name
        strip.kitsu.sequence_id = seq.id

        # Pull sequence color.
        opsdata.append_sequence_color(context, seq)

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_link_shot(bpy.types.Operator):
    """
    Operator that invokes ui which shows user all available shots on server.
    It is used to 'link' a sequence strip to an already existent shot on server.
    Pulls all metadata after selecting shot.
    """

    bl_idname = "kitsu.sqe_link_shot"
    bl_label = "Link Shot"
    bl_description = (
        "Links selected sequence strip to shot on server. Pulls all metadata of shot from server"
    )
    bl_options = {"REGISTER", "UNDO"}

    use_url: bpy.props.BoolProperty(
        name="Use URL",
        description="Use URL of shot on server to initiate strip. Paste complete URL",
    )
    url: bpy.props.StringProperty(
        name="URL",
        description="Complete URL of shot on server that will be used to initiate strip",
        default="",
    )

    _strip = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        strip = sqe.active_strip
        return bool(
            prefs.session_auth(context)
            and cache.project_active_get()
            and strip
            and context.selected_strips
            and checkstrip.is_valid_type(strip)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        shot_id = self._strip.kitsu.shot_id

        # By url.
        if self.use_url:
            # http://192.168.178.80/productions/4dda1c36-1f49-44c7-98c9-93b40ea37dcd/shots/5e69e2e0-c3c8-4fc2-a4a3-f18151adf9dc
            split = self.url.split("/")
            shot_id = split[-1]

        # By shot enum.
        else:
            shot_id = self._strip.kitsu.shot_id
            if shot_id == "":
                self.report({"WARNING"}, "Invalid selection. Please choose a shot")
                return {"CANCELLED"}

        # Check if id available on server (mainly for url option).
        try:
            shot = Shot.by_id(shot_id)

        except (TypeError, gazu.exception.ServerErrorException):
            self.report({"WARNING"}, "Invalid URL: %s" % self.url)
            return {"CANCELLED"}

        except gazu.exception.RouteNotFoundException:
            self.report({"WARNING"}, "ID not found on server: %s" % shot_id)
            return {"CANCELLED"}

        seq = Sequence.by_id(shot.parent_id)
        opsdata.link_metadata_strip(context, shot, seq, self._strip)

        # Log.
        t = "Linked strip: %s to shot: %s with ID: %s" % (
            self._strip.name,
            shot.name,
            shot.id,
        )
        logger.info(t)
        self.report({"INFO"}, t)
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if context.window_manager.clipboard:
            self.url = context.window_manager.clipboard
        self._strip = context.scene.sequence_editor.active_strip

        return context.window_manager.invoke_props_dialog(self, width=400)  # type: ignore

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "use_url")
        if self.use_url:
            row = layout.row()
            row.prop(self, "url", text="")
        else:
            row = layout.row()
            row.prop(self._strip.kitsu, "sequence_name")
            row = layout.row()
            row.prop(self._strip.kitsu, "shot_name")
            row = layout.row()


class KITSU_OT_sqe_multi_edit_strip(bpy.types.Operator):
    bl_idname = "kitsu.sqe_multi_edit_strip"
    bl_label = "Multi Edit Strip"
    bl_options = {"INTERNAL"}
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Multi edits shot name and sequence of selected sequence strips based on "
        "settings in addon preferences with auto shot counter incrementation. "
        "Useful to create a bulk of new shots"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Only if all selected strips are initialized but not linked
        # and they all have the same sequence name.
        sel_shots = context.selected_strips
        if not sel_shots:
            cls.poll_message_set("No strips are selected")
            return False
        nr_of_shots = len(sel_shots)

        if nr_of_shots < 1:
            cls.poll_message_set("Please more than one sequence")
            return False

        seq_name = sel_shots[0].kitsu.sequence_name
        for s in sel_shots:
            if s.kitsu.linked or not s.kitsu.initialized or not checkstrip.is_valid_type(s):
                cls.poll_message_set(
                    "Please select unlinked, initialized strips, of either MOVIE or COLOR type"
                )
                return False
            if s.kitsu.sequence_name != seq_name:
                cls.poll_message_set(
                    "Strips have conflicting sequence names. Please select strips with the same sequence name, or no sequence"
                )
                return False
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        shot_counter_increment = addon_prefs.shot_counter_increment
        shot_counter_digits = addon_prefs.shot_counter_digits
        shot_counter_start = context.window_manager.shot_counter_start
        shot_pattern = addon_prefs.shot_pattern
        strip = context.scene.sequence_editor.active_strip
        sequence = context.window_manager.selected_sequence_name
        var_project = (
            addon_prefs.var_project_custom
            if context.window_manager.var_use_custom_project
            else context.window_manager.var_project_active
        )
        var_sequence = (
            context.window_manager.var_sequence_custom
            if context.window_manager.var_use_custom_seq
            else sequence
        )
        succeeded = []
        failed = []
        logger.info("-START- Multi Edit Shot")

        # Sort sequence after frame in.
        selected_strips = context.selected_strips
        selected_strips = sorted(selected_strips, key=lambda x: x.frame_final_start)
        episode = cache.episode_active_get()

        for idx, strip in enumerate(selected_strips):
            # Gen data for resolver.
            counter_number = shot_counter_start + (shot_counter_increment * idx)
            counter = str(counter_number).rjust(shot_counter_digits, "0")
            var_lookup_table = {
                "Episode": episode.name,
                "Sequence": var_sequence,
                "Project": var_project,
                "Counter": counter,
            }

            # Run shot name resolver.
            shot = opsdata.resolve_pattern(shot_pattern, var_lookup_table)

            # Set metadata.
            strip.kitsu.sequence_name = sequence
            strip.kitsu.sequence_id = context.window_manager.selected_sequence_id
            strip.kitsu.shot_name = shot
            strip.name = shot

            succeeded.append(strip)
            logger.info(
                "Strip: %s Assign sequence: %s Assign shot: %s" % (strip.name, sequence, shot)
            )

        # Report.
        report_str = f"Assigned {len(succeeded)} Shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Multi Edit Shot")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_pull_shot_meta(bpy.types.Operator):
    """
    Operator that pulls metadata of all selected sequence strips from server
    after performing various checks. Metadata will be saved in strip.kitsu.
    """

    bl_idname = "kitsu.sqe_pull_shot_meta"
    bl_label = "Pull Shot Metadata"
    bl_options = {"INTERNAL"}
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Pulls metadata of all selected strips from server. "
        "This includes name, sequence, project and description. "
        "Frame range information will not be pulled"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Pulling shot metadata")

        # Get strips to process.
        selected_strips = context.selected_strips
        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        # Sort strips.
        selected_strips = sorted(selected_strips, key=lambda strip: strip.frame_final_start)

        # Begin progress update.
        context.window_manager.progress_begin(0, len(selected_strips))

        # Clear cache once.
        Cache.clear_all()

        # Track sequence ids that were processed to later update sequence.data["color"] on kitu.
        sequence_ids: List[str] = []

        # Shots.
        for idx, strip in enumerate(selected_strips):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                # Failed.append(strip).
                continue

            # Only if strip is linked to sevrer.
            if not checkstrip.is_linked(strip):
                # Failed.append(strip).
                continue

            # Check if shot is still available by id.
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                logger.error(
                    "Strip '%s' does not have a valid shot id on Kitsu.",
                    strip.name,
                )
                continue

            # Push update to shot.
            pull.shot_meta(strip, shot, clear_cache=False)

            # Append sequence id.
            if shot.parent_id not in sequence_ids:
                sequence_ids.append(shot.parent_id)

            succeeded.append(strip)

        # End progress update.
        context.window_manager.progress_update(len(selected_strips))
        context.window_manager.progress_end()

        # Sequences.
        # Begin second progress update for strips.
        context.window_manager.progress_begin(0, len(sequence_ids))
        for idx, seq_id in enumerate(sequence_ids):
            context.window_manager.progress_update(idx)
            sequence = Sequence.by_id(seq_id)
            opsdata.append_sequence_color(context, sequence)

        # End second progress update.
        context.window_manager.progress_update(len(sequence_ids))
        context.window_manager.progress_end()

        # Report.
        report_str = f"Pulled metadata for {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Pulling shot metadata")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_uninit_strip(bpy.types.Operator):
    bl_idname = "kitsu.sqe_uninit_strip"
    bl_label = "Uninitialize"
    bl_description = "Uninitialize selected strips. Only affects Sequence Editor. "
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Deletes all kitsu metadata of selected sequence strips. "
        "It does not delete anything on the server"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_strips)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed: List[bpy.types.Strip] = []
        succeeded: List[bpy.types.Strip] = []
        logger.info("-START- Uninitializing strips")

        for strip in context.selected_strips:
            if not checkstrip.is_valid_type(strip):
                continue

            if not checkstrip.is_initialized(strip):
                continue

            if checkstrip.is_linked(strip):
                continue

            # Clear kitsu properties.
            strip.kitsu.clear()
            succeeded.append(strip)
            logger.info("Uninitialized strip: %s", strip.name)

        # Report.
        report_str = f"Uninitialized {len(succeeded)} strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Uninitializing strips")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_unlink_shot(bpy.types.Operator):
    bl_idname = "kitsu.sqe_unlink_shot"
    bl_label = "Unlink"
    bl_description = (
        "Deletes link to the server for each selected sequence strip. "
        "Keeps some metadata. "
        "It does not change anything on the server"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_strips)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed: List[bpy.types.Strip] = []
        succeeded: List[bpy.types.Strip] = []
        logger.info("-START- Unlinking shots")

        for strip in context.selected_strips:
            if not checkstrip.is_valid_type(strip):
                continue

            if not checkstrip.is_initialized(strip):
                continue

            if not checkstrip.is_linked(strip):
                continue

            # Clear kitsu properties.
            shot_name = strip.kitsu.shot_name
            strip.kitsu.unlink()
            succeeded.append(strip)
            logger.info("Unlinked shot: %s", shot_name)

        # Report.
        report_str = f"Unlinked {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Unlinking shots")
        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_sqe_push_del_shot(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_del_shot"
    bl_label = "Delete Shot"
    bl_description = "Deletes shot on server and clears metadata of selected sequence strips"

    confirm: bpy.props.BoolProperty(name="Confirm")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context.selected_strips)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.confirm:
            self.report({"WARNING"}, "Push delete aborted")
            return {"CANCELLED"}

        succeeded = []
        failed = []
        logger.info("-START- Deleting shots")

        # Clear cache.
        Cache.clear_all()

        # Begin progress update.
        selected_strips = context.selected_strips

        context.window_manager.progress_begin(0, len(selected_strips))

        for idx, strip in enumerate(selected_strips):
            context.window_manager.progress_update(idx)

            if not checkstrip.is_valid_type(strip):
                continue

            # Check if strip is already linked to sevrer.
            if not checkstrip.is_linked(strip):
                continue

            # Check if shot still exists to sevrer.
            shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
            if not shot:
                failed.append(strip)
                logger.error(
                    "Strip '%s' does not have a valid shot id on Kitsu.",
                    strip.name,
                )
                continue

            # Delete shot.
            push.delete_shot(strip, shot)  # This clears all kitsu properties.
            succeeded.append(strip)

        # End progress update.
        context.window_manager.progress_update(len(selected_strips))
        context.window_manager.progress_end()

        # Report.
        report_str = f"Deleted {len(succeeded)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Deleting shots")
        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        selshots = context.selected_strips
        strips_to_delete = [s for s in selshots if s.kitsu.linked]

        if len(selshots) > 1:
            noun = "%i shots" % len(strips_to_delete)
        else:
            noun = "this shot"

        col.prop(
            self,
            "confirm",
            text="Delete %s on server" % noun,
        )


class KITSU_OT_sqe_set_thumbnail_task_type(bpy.types.Operator):
    bl_idname = "kitsu.set_thumbnail_task_type"
    bl_label = "Set Thumbnail Task Type"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"
    bl_description = "Sets kitsu task type that will be used when uploading thumbnails"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shot_task_types_enum)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Task type selected by user.
        task_type_id = self.enum_prop

        if not task_type_id:
            return {"CANCELLED"}

        task_type = TaskType.by_id(task_type_id)

        # Update scene properties.
        context.scene.kitsu.task_type_thumbnail_name = task_type.name
        context.scene.kitsu.task_type_thumbnail_id = task_type_id

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_set_sqe_render_task_type(bpy.types.Operator):
    bl_idname = "kitsu.set_sqe_render_task_type"
    bl_label = "Set Sqe Render Task Type"
    bl_options = {"INTERNAL"}
    bl_property = "enum_prop"
    bl_description = "Sets kitsu task type that will be used when uploading sequence editor renders"

    enum_prop: bpy.props.EnumProperty(items=cache.get_shot_task_types_enum)  # type: ignore

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Task type selected by user.
        task_type_id = self.enum_prop

        if not task_type_id:
            return {"CANCELLED"}

        task_type = TaskType.by_id(task_type_id)

        # Update scene properties.
        context.scene.kitsu.task_type_sqe_render_name = task_type.name
        context.scene.kitsu.task_type_sqe_render_id = task_type_id

        util.ui_redraw()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class KITSU_OT_sqe_push_render_still(bpy.types.Operator):
    bl_idname = "kitsu.seq_render_still"
    bl_label = "Push Still"
    bl_options = {"INTERNAL"}
    bl_description = (
        "Makes and saves one still for each shot. "
        "Uploads each still to server as a preview image for the selected task type"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context.scene.kitsu.task_type_thumbnail_id)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        nr_of_strips: int = len(context.selected_strips)
        do_multishot: bool = nr_of_strips > 1
        failed = []
        upload_queue: List[Path] = []  # Will be used as succeeded list
        # Get task type by id from user selection enum property.
        task_type = TaskType.by_id(context.scene.kitsu.task_type_thumbnail_id)

        logger.info("-START- Pushing shot thumbnails")

        # Clear cache.
        Cache.clear_all()

        with self.override_render_settings(context):
            with self.temporary_current_frame(context) as original_curframe:
                # ----RENDER AND SAVE THUMBNAILS ------.

                # Begin first progress update.
                selected_strips = context.selected_strips
                if not selected_strips:
                    selected_strips = context.scene.sequence_editor.strips_all

                # Sort strips.
                selected_strips = sorted(
                    selected_strips, key=lambda strip: strip.frame_final_start
                )

                context.window_manager.progress_begin(0, len(selected_strips))

                for idx, strip in enumerate(selected_strips):
                    context.window_manager.progress_update(idx)

                    if not checkstrip.is_valid_type(strip):
                        # Failed.append(strip).
                        continue

                    # Only if strip is linked to sevrer.
                    if not checkstrip.is_linked(strip):
                        # Failed.append(strip).
                        continue

                    # Check if shot is still available by id.
                    shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
                    if not shot:
                        failed.append(strip)
                        logger.error(
                            "Strip '%s' does not have a valid shot id on Kitsu.",
                            strip.name,
                        )
                        continue

                    # If only one strip is selected,.
                    if not do_multishot:
                        # If active strip is not contained in the current frame, use middle frame of active strip
                        # otherwise don't change frame and use current one.
                        if not checkstrip.contains(strip, original_curframe):
                            self.set_middle_frame(context, strip)
                    else:
                        self.set_middle_frame(context, strip)

                    path = self.make_thumbnail(context, strip)
                    upload_queue.append(path)

                # End first progress update.
                context.window_manager.progress_update(len(upload_queue))
                context.window_manager.progress_end()

        # ----ULPOAD THUMBNAILS ------.

        # Begin second progress update.
        context.window_manager.progress_begin(0, len(upload_queue))

        # Process thumbnail queue.
        for idx, filepath in enumerate(upload_queue):
            context.window_manager.progress_update(idx)
            opsdata.upload_preview(context, filepath, task_type, comment="Update thumbnail")

        # End second progress update.
        context.window_manager.progress_update(len(upload_queue))
        context.window_manager.progress_end()

        # Report.
        report_str = f"Created thumbnails for {len(upload_queue)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Pushing shot thumbnails")
        return {"FINISHED"}

    def make_thumbnail(self, context: bpy.types.Context, strip: bpy.types.Strip) -> Path:
        bpy.ops.render.render()
        file_name = f"{strip.kitsu.shot_id}_{str(context.scene.frame_current)}.jpg"
        path = self._save_render(bpy.data.images["Render Result"], file_name)
        logger.info(f"Saved thumbnail of shot {strip.kitsu.shot_name} to {path.as_posix()}")
        return path

    def _save_render(self, datablock: bpy.types.Image, file_name: str) -> Path:
        """Save the current render image to disk"""

        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.thumbnail_dir

        # Ensure folder exists.
        folder_path = Path(folder_name).absolute()
        folder_path.mkdir(parents=True, exist_ok=True)

        path = folder_path.joinpath(file_name)
        datablock.save_render(str(path))
        return path.absolute()

    @contextlib.contextmanager
    def override_render_settings(self, context, thumbnail_width=512):
        """Overrides the render settings for thumbnail size in a 'with' block scope"""

        rd = context.scene.render
        if bpy.app.version >= (5, 0, 0):
            # For Blender 5.0 and later, use the new media_type settings.
            media_type = rd.image_settings.media_type

        # Remember current render settings in order to restore them later.
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        quality = rd.image_settings.quality
        use_stamp_frame = rd.use_stamp_frame

        try:
            if bpy.app.version >= (5, 0, 0):
                # For Blender 5.0 and later, use the new media_type settings.
                rd.image_settings.media_type = "IMAGE"
            # Set the render settings to thumbnail size.
            # Update resolution % instead of the actual resolution to scale text strips properly.
            rd.resolution_percentage = round(thumbnail_width * 100 / rd.resolution_x)
            rd.image_settings.file_format = "JPEG"
            rd.image_settings.quality = 80
            rd.use_stamp_frame = False
            yield

        finally:
            # Return the render settings to normal.
            if bpy.app.version >= (5, 0, 0):
                # For Blender 5.0 and later, use the new media_type settings.
                rd.image_settings.media_type = media_type
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.image_settings.quality = quality
            rd.use_stamp_frame = use_stamp_frame

    @contextlib.contextmanager
    def temporary_current_frame(self, context):
        """Allows the context to set the scene current frame, restores it on exit.

        Yields the initial current frame, so it can be used for reference in the context.
        """
        current_frame = context.scene.frame_current
        try:
            yield current_frame
        finally:
            context.scene.frame_current = current_frame

    @staticmethod
    def set_middle_frame(
        context: bpy.types.Context,
        strip: bpy.types.Strip,
    ) -> int:
        """Sets the current frame to the middle frame of the strip"""

        middle = round((strip.frame_final_start + strip.frame_final_end) / 2)
        context.scene.frame_set(middle)
        return middle


class KITSU_OT_sqe_push_render(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_render"
    bl_label = "Push Render"
    bl_options = {"INTERNAL"}
    bl_description = (
        "Makes and saves a .mp4 for each shot. "
        "Uploads each render on server as a preview image for the selected task type"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context.scene.kitsu.task_type_sqe_render_id)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed = []
        upload_queue: List[Path] = []  # will be used as successed list
        # Get task stype by id from user selection enum property.
        task_type = TaskType.by_id(context.scene.kitsu.task_type_sqe_render_id)

        logger.info("-START- Pushing Sequence Render")

        # Clear cache.
        Cache.clear_all()

        with self.override_render_settings(context):
            # ----RENDER AND SAVE SQE ------.

            # Get strips.
            selected_strips = context.selected_strips
            if not selected_strips:
                selected_strips = context.scene.sequence_editor.strips_all

            # Sort strips.
            selected_strips = sorted(
                selected_strips, key=lambda strip: strip.frame_final_start
            )

            # Begin first progress update.
            context.window_manager.progress_begin(0, len(selected_strips))

            for idx, strip in enumerate(selected_strips):
                context.window_manager.progress_update(idx)

                if not checkstrip.is_valid_type(strip):
                    continue

                # Only if strip is linked to sevrer.
                if not checkstrip.is_linked(strip):
                    continue

                # Check if shot is still available by id.
                shot = checkstrip.shot_exists_by_id(strip, clear_cache=False)
                if not shot:
                    failed.append(strip)
                    logger.error(
                        "Strip '%s' does not have a valid shot id on Kitsu.",
                        strip.name,
                    )
                    continue

                # Output path.
                output_path = self._gen_output_path(strip, task_type)
                context.scene.render.filepath = output_path.as_posix()

                # Frame range.
                context.scene.frame_start = strip.frame_final_start
                context.scene.frame_end = strip.frame_final_end - 1

                # Ensure folder exists.
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Make opengl render.
                bpy.ops.render.opengl(animation=True, sequencer=True)

                # Append path to upload queue.
                upload_queue.append(output_path)

            # End first progress update.
            context.window_manager.progress_update(len(upload_queue))
            context.window_manager.progress_end()

        # ----UPLOAD SQE RENDER ------.

        # Begin second progress update.
        context.window_manager.progress_begin(0, len(upload_queue))

        # Process thumbnail queue.
        for idx, filepath in enumerate(upload_queue):
            context.window_manager.progress_update(idx)
            opsdata.upload_preview(context, filepath, task_type, comment="Sequence Editor Render")

        # End second progress update.
        context.window_manager.progress_update(len(upload_queue))
        context.window_manager.progress_end()

        # Report.
        report_str = f"Uploaded sequence editor render for {len(upload_queue)} shots"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Pushing Sequence Editor Render")
        return {"FINISHED"}

    def _gen_output_path(self, strip: bpy.types.Strip, task_type: TaskType) -> Path:
        addon_prefs = prefs.addon_prefs_get(bpy.context)
        folder_name = addon_prefs.sqe_render_dir
        file_name = f"{strip.kitsu.shot_id}_{strip.kitsu.shot_name}.{(task_type.name).lower()}.mp4"
        return Path(folder_name).absolute().joinpath(file_name)

    @contextlib.contextmanager
    def override_render_settings(self, context, thumbnail_width=256):
        """Overrides the render settings for thumbnail size in a 'with' block scope"""

        rd = context.scene.render

        # Remember current render settings in order to restore them later.

        # Filepath.
        filepath = rd.filepath

        # Format render settings.
        percentage = rd.resolution_percentage
        file_format = rd.image_settings.file_format
        ffmpeg_constant_rate = rd.ffmpeg.constant_rate_factor
        ffmpeg_codec = rd.ffmpeg.codec
        ffmpeg_format = rd.ffmpeg.format
        ffmpeg_audio_codec = rd.ffmpeg.audio_codec

        # Scene settings.
        use_preview_range = context.scene.use_preview_range
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        current_frame = context.scene.frame_current

        try:
            # Format render settings.
            rd.resolution_percentage = 100
            rd.image_settings.file_format = "FFMPEG"
            rd.ffmpeg.constant_rate_factor = "MEDIUM"
            rd.ffmpeg.codec = "H264"
            rd.ffmpeg.format = "MPEG4"
            rd.ffmpeg.audio_codec = "AAC"

            # Scene settings.
            context.scene.use_preview_range = False

            yield

        finally:
            # Filepath.
            rd.filepath = filepath

            # Return the render settings to normal.
            rd.resolution_percentage = percentage
            rd.image_settings.file_format = file_format
            rd.ffmpeg.codec = ffmpeg_codec
            rd.ffmpeg.constant_rate_factor = ffmpeg_constant_rate
            rd.ffmpeg.format = ffmpeg_format
            rd.ffmpeg.audio_codec = ffmpeg_audio_codec

            # Scene settings.
            context.scene.frame_start = frame_start
            context.scene.frame_end = frame_end
            context.scene.frame_current = current_frame
            context.scene.use_preview_range = use_preview_range


class KITSU_OT_sqe_push_shot(bpy.types.Operator):
    bl_idname = "kitsu.sqe_push_shot"
    bl_label = "Push Shot to Kitsu"
    bl_description = "Pushes the active strip to Kitsu"

    comment: bpy.props.StringProperty(
        name="Comment",
        description="Comment that will be appended to this video on Kitsu",
        default="",
    )
    task_type: bpy.props.EnumProperty(
        name="Task Type",
        description="Which task this video should be added to",
        items=cache.get_task_types_enum_for_current_context,
    )
    task_status: bpy.props.EnumProperty(
        name="Task Status",
        description="What to set the task's status to",
        items=cache.get_all_task_statuses_enum,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active_strip = context.scene.sequence_editor.active_strip
        if not hasattr(active_strip, 'filepath'):
            cls.poll_message_set("Selected Strip is not a Video")
            return False

        return bool(prefs.session_auth(context))

    def invoke(self, context, _event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, 'task_type')
        layout.prop(self, 'task_status')
        layout.prop(self, 'comment')

    def execute(self, context: bpy.types.Context) -> Set[str]:
        active_strip = context.scene.sequence_editor.active_strip

        # Find the metadata strip of this strip that contains Kitsu information
        # about what sequence and shot this strip belongs to.
        shot_name = active_strip.name.split(bkglobals.DELIMITER)[0]
        metadata_strip = context.scene.sequence_editor.strips.get(shot_name)
        if not metadata_strip:
            # The metadata strip should've been created by sqe_create_review_session,
            # if the Kitsu integration is enabled in the add-on preferences,
            # the Kitsu add-on is enabled, and valid Kitsu credentials were entered.
            self.report({"ERROR"}, f"Could not find Kitsu metadata strip: {shot_name}.")
            return {"CANCELLED"}

        if not self.task_status:
            self.report({"ERROR"}, "Failed to create playblast. Missing task status")
            return {"CANCELLED"}

        # Set the Kitsu sequence and shot information in the context
        cache.sequence_active_set_by_id(context, metadata_strip.kitsu.sequence_id)
        cache.shot_active_set_by_id(context, metadata_strip.kitsu.shot_id)

        # Upload render
        self.report({"INFO"}, f"Trying to upload render for {shot_name}")
        self._upload_render(context, Path(bpy.path.abspath(active_strip.filepath)))

        self.report({"INFO"}, f"Uploaded render for {shot_name}")
        return {'FINISHED'}

    def _upload_render(self, context: bpy.types.Context, filepath: Path) -> None:
        # Get shot.
        shot = cache.shot_active_get()

        # Get task status and type.
        task_status = TaskStatus.by_id(self.task_status)
        task_type = TaskType.by_id(self.task_type)

        if not task_type:
            raise RuntimeError(
                f"Failed to upload playblast. Task type: {self.task_type} was not found"
            )

        # Find / get latest task
        task = Task.by_name(shot, task_type)
        if not task:
            # An Entity on the server can have 0 tasks even tough task types exist.
            # We have to create a task first before being able to upload a thumbnail.
            task = Task.new_task(shot, task_type, task_status=task_status)

        # Create a comment
        comment = task.add_comment(
            task_status,
            comment=self.comment,
        )

        # Add_preview_to_comment
        task.add_preview_to_comment(comment, filepath.as_posix())

        logger.info(f"Uploaded render for shot: {shot.name} under: {task_type.name}")


class KITSU_OT_sqe_debug_duplicates(bpy.types.Operator):
    bl_idname = "kitsu.sqe_debug_duplicates"
    bl_label = "Debug Duplicates"
    bl_property = "duplicates"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Searches for sequence strips that are linked to the same "
        "shot id. Shows them in a drop down menu which triggers a selection"
    )

    duplicates: bpy.props.EnumProperty(items=opsdata.sqe_get_duplicates, name="Duplicates")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.duplicates

        if not strip_name:
            return {"CANCELLED"}

        # Deselect all if something is selected.
        if context.selected_strips:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.strips_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_duplicates[:] = opsdata.sqe_update_duplicates(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_debug_not_linked(bpy.types.Operator):
    bl_idname = "kitsu.sqe_debug_not_linked"
    bl_label = "Debug Not Linked"
    bl_property = "not_linked"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Searches for sequence strips that are initialized but not linked yet. "
        "Shows them in a drop down menu which triggers a selection"
    )

    not_linked: bpy.props.EnumProperty(items=opsdata.sqe_get_not_linked, name="Not Linked")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.not_linked

        if not strip_name:
            return {"CANCELLED"}

        # Deselect all if something is selected.
        if context.selected_strips:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.strips_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_not_linked[:] = opsdata.sqe_update_not_linked(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_debug_multi_project(bpy.types.Operator):
    bl_idname = "kitsu.sqe_debug_multi_project"
    bl_label = "Debug Multi Projects"
    bl_property = "multi_project"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Searches for sequence strips that come from different projects. "
        "Shows them in a drop down menu which triggers a selection"
    )

    multi_project: bpy.props.EnumProperty(items=opsdata.sqe_get_multi_project, name="Multi Project")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip_name = self.multi_project

        if not strip_name:
            return {"CANCELLED"}

        # Deselect all if something is selected.
        if context.selected_strips:
            bpy.ops.sequencer.select_all()

        strip = context.scene.sequence_editor.strips_all[strip_name]
        strip.select = True
        bpy.ops.sequencer.select()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        opsdata._sqe_multi_project[:] = opsdata.sqe_update_multi_project(context)
        return context.window_manager.invoke_props_popup(self, event)  # type: ignore


class KITSU_OT_sqe_pull_edit(bpy.types.Operator):
    bl_idname = "kitsu.sqe_pull_edit"
    bl_label = "Pull Edit"
    bl_description = (
        "Pulls the entire edit from kitsu and creates a metadata strip for each shot. "
        "Does not change existing strips. Only places new strips if there is space"
    )
    bl_options = {"REGISTER", "UNDO", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and cache.project_active_get())

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed = []
        created = []
        succeeded = []
        existing = []
        channel = context.scene.kitsu.pull_edit_channel
        active_project = cache.project_active_get()
        active_episode = cache.episode_active_get()
        strips = (
            active_episode.get_sequences_all()
            if active_episode
            else active_project.get_sequences_all()
        )
        shot_strips = checksqe.get_shot_strips(context)
        occupied_ranges = checksqe.get_occupied_ranges(context)
        all_shots = active_project.get_shots_all()
        selection = context.selected_strips

        logger.info("-START- Pulling Edit")

        context.window_manager.progress_begin(0, len(all_shots))
        progress_idx = 0

        # Process sequence after sequence.
        for seq in strips:
            print("\n" * 2)
            logger.info("Processing Sequence %s", seq.name)
            shots = seq.get_all_shots()

            # Extend context.scene.kitsu.sequence_colors property.
            opsdata.append_sequence_color(context, seq)

            for shot in shots:
                context.window_manager.progress_update(progress_idx)
                progress_idx += 1

                if not shot.data:
                    # Can happen, propably when shot is missing frame information on
                    # kitsu.
                    logger.warning(
                        "Shot %s, is missing 'data' dictionary. Can't determine frame_in and frame_out. Skip.",
                        shot.name,
                    )
                    continue

                # Get frame range information.
                frame_start = shot.data.get("frame_in", None)
                frame_end = shot.data.get("frame_out", None)

                if frame_start is None or frame_end is None:
                    failed.append(shot)
                    logger.error(
                        "Failed to create shot %s. Missing frame range information",
                        shot.name,
                    )
                    continue

                # Frame info comes in str format from kitsu.
                frame_start = int(frame_start)
                frame_end = int(frame_end)
                shot_range = range(frame_start, frame_end + 1)

                # Try to find existing strip that is already linked to that shot.
                strip = self._find_shot_strip(shot_strips, shot.id)

                # Check if on the specified channel there is space to put the strip.
                if str(channel) in occupied_ranges:
                    if checksqe.is_range_occupied(shot_range, occupied_ranges[str(channel)]):
                        failed.append(shot)
                        logger.error(
                            "Failed to create shot %s. Channel: %i Range: %i - %i is occupied",
                            shot.name,
                            channel,
                            frame_start,
                            frame_end,
                        )
                        continue
                # TODO Refactor as this reuses code from KITSU_OT_sqe_create_metadata_strip
                if not strip:
                    strip = opsdata.create_metadata_strip(
                        context.scene, shot.name, channel, frame_start, frame_end
                    )

                    # Apply slip to match offset.
                    self._apply_strip_slip_from_shot(context, strip, shot)

                    created.append(shot)
                    logger.info("Shot %s created new strip", shot.name)

                else:
                    # Update properties of existing strip.
                    strip.channel = channel
                    logger.info("Shot %s use existing strip: %s", shot.name, strip.name)
                    existing.append(strip)

                strip.blend_alpha = 0

                # Pull shot meta and link shot.
                pull.shot_meta(strip, shot, clear_cache=False)

                succeeded.append(shot)

        context.window_manager.progress_update(len(all_shots))
        context.window_manager.progress_end()

        bpy.ops.sequencer.select_all(action='DESELECT')

        for s in selection:
            s.select = True

        # Report.
        report_str = f"Shots: Succeded:{len(succeeded)} | Created  {len(created)} | Existing: {len(existing)}"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        logger.info("-END- Pulling Edit")

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return context.window_manager.invoke_props_dialog(self, width=300)  # type: ignore

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Set channel in which the entire edit should be created")
        row = layout.row()
        row.prop(context.scene.kitsu, "pull_edit_channel")

    def _find_shot_strip(
        self, shot_strips: List[bpy.types.Strip], shot_id: str
    ) -> Optional[bpy.types.Strip]:
        for strip in shot_strips:
            if strip.kitsu.shot_id == shot_id:
                return strip

        return None

    def _get_random_pastel_color_rgb(self) -> Tuple[float, float, float]:
        """Returns a randomly generated color with high brightness and low saturation"""

        hue = random.random()
        saturation = random.uniform(0.25, 0.33)
        brightness = random.uniform(0.75, 0.83)

        color = colorsys.hsv_to_rgb(hue, saturation, brightness)
        return (color[0], color[1], color[2])

    def _apply_strip_slip_from_shot(
        self, context: bpy.types.Context, strip: bpy.types.Strip, shot: Shot
    ) -> None:
        offset = strip.kitsu_3d_start - int(shot.get_3d_start())

        bpy.ops.sequencer.select_all(action='DESELECT')

        strip.select = True
        bpy.ops.sequencer.slip(offset=offset)


class KITSU_OT_sqe_init_strip_start_frame(bpy.types.Operator):
    bl_idname = "kitsu.sqe_init_strip_start_frame"
    bl_label = "Initialize Shot Start Frame"
    bl_description = "Calculates offset so the current shot starts at 101"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        succeeded = []
        failed = []
        logger.info("-START- Initializing strip start frame")

        selected_strips = context.selected_strips
        if not selected_strips:
            selected_strips = context.scene.sequence_editor.strips_all

        for strip in selected_strips:
            if not checkstrip.is_valid_type(strip):
                continue

            if not strip.kitsu.initialized:
                logger.info("%s not initialized", strip.name)
                continue

            # Apply strip.kitsu.frame_start_offset.
            opsdata.init_start_frame_offset(strip)

            succeeded.append(strip)
            logger.info(
                "%s initiated start frame to 101 by applying offset: %i ",
                strip.name,
                strip.kitsu.frame_start_offset,
            )

        # Report.
        report_str = f"Initiated start frame of {len(succeeded)} strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Log.
        logger.info("-END- Initializing strip start frame")
        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_create_metadata_strip(bpy.types.Operator):
    bl_idname = "kitsu.sqe_create_metadata_strip"
    bl_label = "Create Metadata Strip"
    bl_description = (
        "Adds metadata strip for each selected strip. "
        "Tries to place metadata strip one channel above selected "
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.selected_strips)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        failed = []
        created = []
        occupied_ranges = checksqe.get_occupied_ranges(context)
        logger.info("-START- Creating Metadata Strips")

        selected_strips = context.selected_strips
        # Check if metadata strip file actually exists.
        for strip in selected_strips:
            # Get frame range information from current strip.
            strip_range = range(strip.frame_final_start, strip.frame_final_end)
            channel = strip.channel + 1

            # Check if one channel above strip there is space to put the metadata strip.
            if str(channel) in occupied_ranges:
                if checksqe.is_range_occupied(strip_range, occupied_ranges[str(channel)]):
                    failed.append(strip)
                    logger.error(
                        "Failed to create metadata strip for %s. Channel: %i Range: %i - %i is occupied",
                        strip.name,
                        channel,
                        strip.frame_final_start,
                        strip.frame_final_end,
                    )
                    continue

            # Create new metadata strip.
            # TODO: frame range of metadata strip is 1000 which is problematic because it needs to fit
            # on the first try, EDIT: seems to work maybe per python overlaps of strips possible?

            metadata_strip = opsdata.create_metadata_strip(
                context.scene,
                f"{strip.name}{bkglobals.DELIMITER}metadata{bkglobals.SPACE_REPLACER}strip",
                strip.channel + 1,
                strip.frame_final_start,
                strip.frame_final_end,
            )

            created.append(metadata_strip)

            logger.info(
                "%s created metadata strip: %s",
                strip.name,
                metadata_strip.name,
            )

        # Report.
        report_str = f"Created {len(created)} metadata strips"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        # Deselect source strips after creating Metadata strips
        for strip in selected_strips:
            if strip not in created:
                strip.select = False

        # Log.
        logger.info("-END- Creating Metadata Strips")
        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_fix_metadata_strips(bpy.types.Operator):
    bl_idname = "kitsu.sqe_fix_metadata_strip"
    bl_label = "Fix Metadata Strip Missing Media"
    bl_description = "Fixes missing media error in metadata strips. "
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        addon_prefs = prefs.addon_prefs_get(context)

        if len(context.selected_strips) == 0:
            all_strips = context.scene.sequence_editor.strips
        else:
            all_strips = context.selected_strips

        offline_metadata_strips = [
            strip
            for strip in all_strips
            if strip.kitsu.shot_id != '' and not Path(strip.filepath).is_file()
        ]

        for strip in offline_metadata_strips:
            strip.filepath = addon_prefs.metadatastrip_file
        return {"FINISHED"}


class KITSU_OT_sqe_add_sequence_color(bpy.types.Operator):
    """
    Adds sequence of active strip to scene.kitsu.sequence_colors collection property
    """

    bl_idname = "kitsu.add_sequence_color"
    bl_label = "Add Sequence Color"
    bl_description = "Registers a sequence color for active sequence strip"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        active_strip = sqe.active_strip
        return bool(active_strip and active_strip.kitsu.sequence_id)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        sequence_colors = context.scene.kitsu.sequence_colors
        active_strip = context.scene.sequence_editor.active_strip
        sequence_id = active_strip.kitsu.sequence_id

        # Check if sequence_id is already in sequence color collection property
        if sequence_id in sequence_colors.keys():
            self.report(
                {"WARNING"},
                f"Sequence {sequence_id} (ID: {active_strip.kitsu.sequence_name}) already in scene.kitsu.sequence_colors",
            )
            return {"CANCELLED"}

        # Add new item to sequence color collection property
        item = context.scene.kitsu.sequence_colors.add()
        item.name = active_strip.kitsu.sequence_id
        self.report(
            {"INFO"},
            f"Added {sequence_id} (ID: {active_strip.kitsu.sequence_name}) to scene.kitsu.seqeuence_colors",
        )
        return {"FINISHED"}


class KITSU_OT_sqe_scan_for_media_updates(bpy.types.Operator):
    bl_idname = "kitsu.sqe_scan_for_media_updates"
    bl_label = "Scan for media updates"
    bl_description = (
        "Scans sequence editor for movie strips and highlights them if there is a more recent version of their source media. "
        "Source Media is located either in the Playblast Directory or the 'Media Update Search Paths' directories"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        return bool(sqe.strips_all)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = prefs.addon_prefs_get(context)
        outdated: List[bpy.types.Strip] = []
        invalid: List[bpy.types.Strip] = []
        no_version: List[bpy.types.Strip] = []
        up_to_date: List[bpy.types.Strip] = []
        checked: List[bpy.types.Strip] = []
        excluded: List[bpy.types.Strip] = []

        strips = context.selected_strips
        if not strips:
            strips = context.scene.sequence_editor.strips_all

        logger.info("-START- Scanning for media updates")

        for strip in strips:
            if not strip.type == "MOVIE":
                continue

            checked.append(strip)

            # Check if it has valid filepath key.
            if not strip.filepath:
                logger.info("%s has invalid filepath. Skip", strip.name)
                invalid.append(strip)
                continue

            media_path_old = Path(os.path.abspath(bpy.path.abspath(strip.filepath)))
            current_version = util.get_version(media_path_old.name)

            # Check if filepath is in include path.
            included = False
            paths = [item.filepath for item in addon_prefs.media_update_search_paths]
            paths.append(addon_prefs.shot_playblast_root_dir)
            for path in paths:
                filepath = Path(os.path.abspath(bpy.path.abspath(path)))
                if media_path_old.as_posix().startswith(filepath.as_posix()):
                    included = True
                    break

            if not included:
                logger.info("Not included in media update search list: %s", strip.filepath)
                excluded.append(strip)
                continue

            # Check if source media path contains version string.
            if not current_version:
                no_version.append(strip)
                continue

            # Gather valid files to compare source media to.
            media_folder = media_path_old.parent
            media_all: List[Path] = [
                f for f in media_folder.iterdir() if f.is_file() and util.get_version(f.name)
            ]
            # List of files that are named as source except for version str.
            valid_files: List[Path] = []

            for file in media_all:
                # Version should exists here, we already check for that in list comprehension.
                version = util.get_version(file.name)

                # We only want to consider files that have the same name except for version string.
                if file.name.replace(version, "") != media_path_old.name.replace(
                    current_version, ""
                ):
                    continue

                valid_files.append(file)

            valid_files.sort(reverse=True)

            # No valid files found, should not happen source file should be at least here.
            if not valid_files:
                continue

            if valid_files[0] == media_path_old:
                # Logger.info("%s already up to date: %s", strip.name, strip.filepath).
                strip.kitsu.media_outdated = False
                up_to_date.append(strip)
                continue

            # Load latest media.
            logger.info(
                "%s newer version of source media available: %s > %s",
                strip.name,
                current_version,
                util.get_version(valid_files[0].name),
            )

            # Append to outdated list.
            outdated.append(strip)

            # Set media outdatet property for gpu overlay.
            strip.kitsu.media_outdated = True

        # Report.
        self.report(
            {"INFO"},
            f"Scanned {len(checked)} | Outdatet: {len(outdated)} | Up-to-date: {len(up_to_date)} | Invalid: {len(invalid) + len(excluded) + len(no_version)}",
        )

        # Log.
        logger.info("-END- Scanning for outdated media")
        util.ui_redraw()
        return {"FINISHED"}


def get_used_channels(self: Any, context: bpy.types.Context, edit_text: str = "") -> List[str]:
    used_channels = []
    for strip in context.scene.sequence_editor.strips_all:
        used_channels.append(strip.channel)

    aval_channels = []
    for channel in range(1, 100):
        if channel not in used_channels:
            aval_channels.append(channel)

    return [f"{channel}" for channel in aval_channels]


def get_shot_task_types_enum_list(self, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    active_project = cache.project_active_get()
    return [
        (t.id, t.name, "")
        for t in TaskType.all_shot_task_types()
        if t.id in active_project.task_types
    ]


class KITSU_OT_sqe_import_playblast(bpy.types.Operator):
    bl_idname = "kitsu.sqe_import_playblast"
    bl_label = "Import Playblast"
    bl_description = "Import playblast for selected metadata strips"
    bl_options = {"REGISTER", "UNDO"}

    channel_selection: bpy.props.StringProperty(  # type: ignore
        name="Channel",
        description="Choose an empty target channel to place playblasts onto",
        search=get_used_channels,
        search_options={'SORT'},
    )

    task_type: bpy.props.EnumProperty(  # type: ignore
        name="Task Type",
        description="Choose a task type to import playblasts for",
        items=get_shot_task_types_enum_list,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        if not cache.project_active_get():
            cls.poll_message_set("No Kitsu Project Found check Add-on Preferences")
            return False
        for strip in context.selected_strips:
            if strip.kitsu.shot_id == "":
                cls.poll_message_set(f"Selected strip {strip.name} is not metadata strip'")
                return False
        if len(context.selected_strips) == 0:
            cls.poll_message_set("Please select one or more metadata strips")
            return False
        return True

    def invoke(self, context, event):
        channels = [int(x) for x in get_used_channels(self, context)]
        strip = context.selected_strips[0]
        channel = min(channels, key=lambda x: abs(x - strip.channel))
        self.channel_selection = f"{channel}"
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "channel_selection")
        layout.prop(self, "task_type")

    def execute(self, context: Context) -> Set[str] | Set[int]:
        succeeded: Set[str] = set()
        failed: Set[str] = set()
        strips = context.scene.sequence_editor.strips
        metadata_strips = [
            strip for strip in context.selected_strips if strip.kitsu.shot_id != ''
        ]
        for metadata_strip in metadata_strips:
            # TODO add try except if ID is not valid, do same for shot as image sequence.
            shot = Shot.by_id(metadata_strip.kitsu.shot_id)
            task_type_short_name = TaskType.by_id(self.task_type).get_short_name()
            filepath = shot.get_latest_playblast_file(context, task_type_short_name)
            if filepath:
                playblast = strips.new_movie(
                    name=Path(filepath).name,
                    filepath=filepath,
                    frame_start=int(metadata_strip.frame_start),
                    channel=int(self.channel_selection),
                )
                if playblast.frame_final_end > metadata_strip.frame_final_end:
                    playblast.frame_final_end = metadata_strip.frame_final_end

                succeeded.add(metadata_strip.name)
            else:
                failed.add(metadata_strip.name)

        # Convert Sets to Lists for easy access to contents
        succeeded = list(succeeded)
        failed = list(failed)

        if len(metadata_strips) == 1:
            if len(failed) == 1:
                self.report({"WARNING"}, f"Failed to import Playblast `{failed[0]}` does not exist")
                return {"CANCELLED"}
            if len(succeeded) == 1:
                self.report({"INFO"}, f"Imported Playblast from `{succeeded[0]}`")
                return {"FINISHED"}

        report_str = f"Imported {len(succeeded)} Playblast"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )

        self.report(
            {report_state},
            report_str,
        )
        return {'FINISHED'}


class KITSU_OT_sqe_import_image_sequence(bpy.types.Operator):
    bl_idname = "kitsu.sqe_import_image_sequence"
    bl_label = "Import Image Sequence"
    bl_description = "Import Image Sequence for selected metadata strips"
    bl_options = {"REGISTER", "UNDO"}

    channel_selection: bpy.props.StringProperty(
        name="Channel",
        description="Choose an empty target channel to place image strips onto",
        search=get_used_channels,
        search_options={'SORT'},
    )
    file_type: bpy.props.EnumProperty(
        name="File Type",
        description="Choose an empty target channel to place image strips onto",
        items=[
            ('.jpg', 'JPG', '', '', 0),
            ('.exr', 'EXR', '', '', 1),
        ],
    )

    set_color_space: bpy.props.BoolProperty(
        name="Match Scene Color",
        description="Match scene color space to image sequence file type. \n JPG: sGRB with no look, EXR: Linear with Medium Contrast look",
        default=True,
    )

    task_type: bpy.props.EnumProperty(  # type: ignore
        name="Task Type",
        description="Choose a task type to import playblasts for",
        items=get_shot_task_types_enum_list,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        if not cache.project_active_get():
            cls.poll_message_set("No Kitsu Project Found check Add-on Preferences")
            return False
        for strip in context.selected_strips:
            if strip.kitsu.shot_id == "":
                cls.poll_message_set(f"Selected strip {strip.name} is not metadata strip'")
                return False
        if len(context.selected_strips) == 0:
            cls.poll_message_set("Please select a 'MOVIE' strip")
            return False
        return True

    def set_scene_colorspace(self, context):
        color_space_name = "Linear Rec.709"

        scene = context.scene
        if self.file_type == ".jpg":
            scene.sequencer_colorspace_settings.name = "sRGB"
            scene.view_settings.look = "None"
            scene.view_settings.view_transform = 'Standard'
        if self.file_type == ".exr":
            scene.sequencer_colorspace_settings.name = color_space_name
            scene.view_settings.look = 'Medium High Contrast'
            scene.view_settings.view_transform = 'Filmic'

    def invoke(self, context, event):
        channels = [int(x) for x in get_used_channels(self, context)]
        strip = context.selected_strips[0]
        channel = min(channels, key=lambda x: abs(x - strip.channel))
        self.channel_selection = f"{channel}"
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "task_type")
        layout.prop(self, "channel_selection")
        layout.prop(self, "file_type")
        layout.prop(self, "set_color_space")

    def get_shot_name(self, strip):
        filepath = strip.filepath
        name = Path(filepath).name
        match = re.search(r"^(\w+)-", name)
        if match:
            return match.group(1)
        return

    def import_strip(self, context, metadata_strip, directory, channel):
        # https://blender.stackexchange.com/questions/286946/how-to-add-image-sequence-in-sequencer-via-python
        frame_start = metadata_strip.frame_final_start
        frame_end = metadata_strip.frame_final_end

        files = []
        
        prefs = util.addon_prefs_get(context)
        shot = Shot.by_id(metadata_strip.kitsu.shot_id)
        start_frame = (
            shot.data.get('3d_start') if shot.data.get('3d_start') else prefs.shot_builder_frame_offset
        )
        for file in sorted(list(directory.iterdir())):
            if file.name.endswith("mp4"):
                continue
            frame_number = int(file.name.split(".")[0])
            duration = metadata_strip.frame_duration + start_frame
            if self.file_type in file.name and frame_number < duration:
                files.append({"name": file.name})

        area_type = 'SEQUENCE_EDITOR'
        areas = [area for area in bpy.context.window.screen.areas if area.type == area_type]

        if files == []:
            self.report({'ERROR'}, "No files found")
            return {'CANCELLED'}

        num_strips = len(context.scene.sequence_editor.strips_all)

        with context.temp_override(
            window=context.window,
            area=areas[0],
            regions=[region for region in areas[0].regions if region.type == 'WINDOW'][0],
            screen=context.window.screen,
        ):
            bpy.ops.sequencer.image_strip_add(
                directory=directory._str,
                files=files,
                relative_path=True,
                show_multiview=False,
                frame_start=frame_start,
                frame_end=frame_end,
                channel=channel,
                fit_method='FIT',
            )
        if num_strips + 1 != len(context.scene.sequence_editor.strips_all):
            print(f"Failed to import image sequence for {metadata_strip.name}")
            return

        new_strip = context.selected_strips[0]

        new_strip.animation_offset_end = metadata_strip.animation_offset_end
        new_strip.animation_offset_start = metadata_strip.animation_offset_start

        new_strip.frame_offset_end = metadata_strip.frame_offset_end
        new_strip.frame_offset_start = metadata_strip.frame_offset_start
        new_strip.frame_start = metadata_strip.frame_start
        new_strip.channel = channel
        new_strip.name = f"{self.get_shot_name(metadata_strip)}{self.file_type.lower()}"
        new_strip.colorspace_settings.name = new_strip.colorspace_settings.name

    def get_shot_seq_directory(self, context, filepath):
        addon_prefs = prefs.addon_prefs_get(context)
        path_string = os.path.realpath(bpy.path.abspath(filepath))
        path = Path(
            path_string.replace(addon_prefs.shot_playblast_root_dir, addon_prefs.frames_root_dir)
        )
        return path.parent

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Get closest empty channel.
        succeeded = []
        failed = []
        channel = int(self.channel_selection)
        addon_prefs = prefs.addon_prefs_get(context)
        if not (Path(addon_prefs.frames_root_dir).is_dir() and addon_prefs.frames_root_dir != ''):
            self.report({"ERROR"}, f"Frames Directory does not exist, check add-on preferences")
            return {"CANCELLED"}

        if self.set_color_space:
            self.set_scene_colorspace(context)

        metadata_strips = [
            strip for strip in context.selected_strips if strip.kitsu.shot_id != ''
        ]

        for strip in metadata_strips:
            shot = Shot().by_id(strip.kitsu.shot_id)
            # TODO pass task type as variable
            task_type_short_name = TaskType.by_id(self.task_type).get_short_name()
            filepath = shot.get_latest_playblast_file(context, task_type_short_name)
            directory = self.get_shot_seq_directory(context, filepath)
            if not directory.exists():
                failed.append(str(directory))
                continue
            self.import_strip(context, strip, directory, channel)
            succeeded.append(str(directory))

        if len(metadata_strips) == 1:
            if len(failed) == 1:
                self.report(
                    {"WARNING"}, f"Failed to import Image Sequence `{failed[0]}` does not exist"
                )
                return {"CANCELLED"}
            if len(succeeded) == 1:
                self.report({"INFO"}, f"Imported Image Sequence from `{succeeded[0]}`")
                return {"FINISHED"}

        report_str = f"Imported {len(succeeded)} Image Sequences"
        report_state = "INFO"
        if failed:
            report_state = "WARNING"
            report_str += f" | Failed: {len(failed)}"

        self.report(
            {report_state},
            report_str,
        )
        return {"FINISHED"}


class KITSU_OT_sqe_clear_update_indicators(bpy.types.Operator):
    bl_idname = "kitsu.sqe_clear_update_indicators"
    bl_label = "Clear Update Indicators"
    bl_description = "Removes the media update indicators from all strips"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        return bool(sqe.strips_all)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        reset: List[bpy.types.Strip] = []

        strips = context.selected_strips
        if not strips:
            strips = context.scene.sequence_editor.strips_all

        for strip in strips:
            if strip.kitsu.media_outdated:
                strip.kitsu.media_outdated = False
                reset.append(strip)
        if not reset:
            self.report({"INFO"}, "Already reset")
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Cleared indicator of {len(reset)} {'strip' if len(reset) == 1 else 'strips'}",
        )

        util.ui_redraw()

        return {"FINISHED"}


class KITSU_OT_sqe_change_strip_source(bpy.types.Operator):
    bl_idname = "kitsu.sqe_change_strip_source"
    bl_label = "Change Strip Media Source"
    bl_description = (
        "Changes the media source of the active strip by "
        "cycling through the different versions on disk"
    )
    bl_options = {"REGISTER", "UNDO"}

    direction: bpy.props.EnumProperty(items=[("UP", "UP", ""), ("DOWN", "DOWN", "")])
    go_latest: bpy.props.BoolProperty(name="Got to latest", default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sqe = context.scene.sequence_editor
        if not sqe:
            return False
        return bool(sqe.active_strip)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        strip = context.scene.sequence_editor.active_strip

        # Check if it has valid filepath key.
        if not strip.filepath:
            self.report({"ERROR"}, f"{strip.name} has invalid filepath")
            return {"CANCELLED"}

        media_path_old = Path(os.path.abspath(bpy.path.abspath(strip.filepath)))
        current_version = util.get_version(media_path_old.name)

        # Check if source media path contains version string.
        if not current_version:
            self.report(
                {"ERROR"},
                f"{strip.name} source media contains no version string: {strip.filepath}",
            )
            return {"CANCELLED"}

        # Gather valid files to compare source media to.
        media_folder = media_path_old.parent
        media_all: List[Path] = [
            f for f in media_folder.iterdir() if f.is_file() and util.get_version(f.name)
        ]
        # List of files that are named as source except for version str.
        valid_files: List[Path] = []

        for file in media_all:
            # Version should exists here, we already check for that in list comprehension.
            version = util.get_version(file.name)

            # We only want to consider files that have the same name except for version string.
            if file.name.replace(version, "") != media_path_old.name.replace(current_version, ""):
                continue

            valid_files.append(file)

        valid_files.sort(reverse=True)

        # No valid files found, should not happen source file should be at least here.
        if not valid_files:
            self.report({"WARNING"}, f"{strip.name} no other files available")

        current_idx = valid_files.index(media_path_old)

        if self.go_latest:
            latest_index = 0
            # Check if already on latest version.
            if current_idx == latest_index:
                self.report(
                    {"INFO"},
                    f"Already at latest version: {util.get_version(valid_files[0].name)}",
                )
            else:
                self.report(
                    {"INFO"},
                    f"Reached latest version: {util.get_version(valid_files[0].name)}",
                )
                strip.filepath = bpy.path.relpath(valid_files[latest_index].as_posix())

            strip.kitsu.media_outdated = False
            # Needs to be reset otherwise other operator instances also do go_latest.
            self.go_latest = False

        elif self.direction == "UP":
            new_index = current_idx - 1

            if new_index <= 0:
                self.report(
                    {"INFO"},
                    f"Reached latest version: {util.get_version(valid_files[0].name)}",
                )
                strip.kitsu.media_outdated = False

            if current_idx == 0:
                return {"FINISHED"}

            if new_index >= 0:
                strip.filepath = bpy.path.relpath(valid_files[new_index].as_posix())

        elif self.direction == "DOWN":
            new_index = current_idx + 1

            if new_index >= len(valid_files) - 1:
                self.report(
                    {"INFO"},
                    f"Reached oldest version: {util.get_version(valid_files[-1].name)}",
                )

            if current_idx == len(valid_files) - 1:
                return {"FINISHED"}

            if new_index <= len(valid_files) - 1:
                strip.filepath = bpy.path.relpath(valid_files[new_index].as_posix())
                strip.kitsu.media_outdated = True

        # Load latest media.
        logger.info(
            "%s changed source media version: %s > %s",
            strip.name,
            current_version,
            util.get_version(Path(strip.filepath).name),
        )

        util.ui_redraw()
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
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
    KITSU_OT_sqe_push_shot,
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
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
