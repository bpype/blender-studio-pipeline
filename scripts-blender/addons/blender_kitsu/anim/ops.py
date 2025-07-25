# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Set, Tuple

import bpy

from .. import cache, util
from ..logger import LoggerFactory

from . import opsdata

logger = LoggerFactory.getLogger()


class KITSU_OT_anim_quick_duplicate(bpy.types.Operator):
    bl_idname = "kitsu.anim_quick_duplicate"
    bl_label = "Quick Duplicate"
    bl_description = (
        "Duplicate the active collection and add it to the "
        "output collection of the current scene"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        act_coll = context.view_layer.active_layer_collection.collection

        return bool(
            cache.shot_active_get()
            and context.view_layer.active_layer_collection.collection
            and not opsdata.is_item_local(act_coll)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        act_coll = context.view_layer.active_layer_collection.collection
        amount = context.window_manager.kitsu.quick_duplicate_amount

        if not act_coll:
            self.report({"ERROR"}, f"No collection selected")
            return {"CANCELLED"}

        # Check if output colletion exists in scene.
        output_coll_name = cache.output_collection_name_get()
        try:
            output_coll = bpy.data.collections[output_coll_name]

        except KeyError:
            self.report(
                {"ERROR"},
                f"Missing output collection: {output_coll_name}",
            )
            return {"CANCELLED"}

        # Get ref coll.
        ref_coll = opsdata.get_ref_coll(act_coll)

        for i in range(amount):
            # Create library override.
            coll = ref_coll.override_hierarchy_create(
                context.scene, context.view_layer, reference=act_coll
            )

            # Set color tag to be the same.
            coll.color_tag = act_coll.color_tag

            # Link coll in output collection.
            if coll not in list(output_coll.children):
                output_coll.children.link(coll)

        # Report.
        self.report(
            {"INFO"},
            f"Created {amount} Duplicates of: {act_coll.name} and added to {output_coll.name}",
        )

        util.ui_redraw()
        return {"FINISHED"}


class KITSU_OT_anim_check_action_names(bpy.types.Operator):
    bl_idname = "kitsu.anim_check_action_names"
    bl_label = "Check Action Names "
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Inspect all action names of .blend file and check "
        "if they follow the Blender Studio naming convention"
    )
    wrong: List[Tuple[bpy.types.Action, str]] = []
    created: List[bpy.types.Action] = []
    empty_actions: List[bpy.types.Action] = []
    cleanup_empty_actions: bpy.props.BoolProperty(
        name="Delete Empty Action Data-Blocks",
        default=False,
        description="Remove any empty action data-blocks, actions that have 0 Fcurves/Keyframes. Even if the action has a fake user assigned to it",
    )

    # List of tuples that contains the action on index 0 with the wrong name
    # and the name it should have on index 1.

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not cache.shot_active_get():
            cls.poll_message_set("No Shot selected")
            return False
        if not cache.task_type_active_get():
            cls.poll_message_set("No Task Type selected")
            return False
        return True

    def get_action(self, action_name: str):
        if bpy.data.actions.get(action_name):
            return bpy.data.actions.get(action_name)
        else:
            new_action = bpy.data.actions.new(action_name)
            self.created.append(new_action)
            return new_action

    def execute(self, context: bpy.types.Context) -> Set[str]:
        existing_action_names = [a.name for a in bpy.data.actions]
        failed = []
        succeeded = []
        removed = []

        # Clean-up Empty Actions
        if self.cleanup_empty_actions:
            for action in self.empty_actions:
                removed.append(action.name)
                action.use_fake_user = False
                bpy.data.actions.remove(action)

        # Rename actions.
        for action, name in self.wrong:
            if name in existing_action_names:
                logger.warning(
                    "Failed to rename action %s to %s. Action with that name already exists",
                    action.name,
                    name,
                )
                failed.append(action)
                continue

            old_name = action.name
            action.name = name
            action.use_fake_user = True
            existing_action_names.append(action.name)
            succeeded.append(action)
            logger.info("Renamed action %s to %s", old_name, action.name)

        # Report.
        report_str = f"Renamed actions: {len(succeeded)}"
        report_state = "INFO"

        if self.cleanup_empty_actions:
            report_str += f" | Removed Empty Actions: {len(removed)}"
        if failed:
            report_state = "WARNING"
            report_str += f" | Rename Failed: {len(failed)}"
        if len(self.created) != 0:
            report_str += f" | Created Actions: {len(self.created)}"

        self.report(
            {report_state},
            report_str,
        )

        # Clear action names cache.
        opsdata.action_names_cache.clear()

        return {"FINISHED"}

    def invoke(self, context, event):
        shot_active = cache.shot_active_get()
        self.wrong.clear()
        self.created.clear()
        no_action = []
        correct = []

        # Clear action names cache.
        opsdata.action_names_cache.clear()
        opsdata.action_names_cache.extend([a.name for a in bpy.data.actions])

        output_col_name = cache.output_collection_name_get()
        output_col = context.scene.collection.children.get(output_col_name)

        if not output_col:
            self.report(
                {"ERROR"},
                f"Missing output collection: {output_col_name}",
            )
            return {"CANCELLED"}

        # Find all asset collections in .blend.
        asset_colls = opsdata.find_asset_collections(output_col)

        if not asset_colls:
            self.report(
                {"WARNING"},
                f"Failed to find any asset collections",
            )
            return {"CANCELLED"}

        # Collect Empty Actions
        self.empty_actions = []
        for action in bpy.data.actions:
            if len(action.fcurves) == 0:
                self.empty_actions.append(action)

        # Find rig of each asset collection.
        asset_rigs: List[Tuple[bpy.types.Collection, bpy.types.Armature]] = []
        for coll in asset_colls:
            rigs = opsdata.find_rig(coll, log=False)
            if rigs:
                for rig in rigs:
                    asset_rigs.append((coll, rig))

        if not asset_rigs:
            self.report(
                {"WARNING"},
                f"Failed to find any valid rigs",
            )
            return {"CANCELLED"}

        # For each rig check the current action name if it matches the convention.
        for coll, rig in asset_rigs:
            if not rig.animation_data or not rig.animation_data.action:
                logger.info("%s has no animation data", rig.name)
                no_action.append(rig)
                continue

            if rig.animation_data.action in self.empty_actions:
                continue

            action_name_should = opsdata.gen_action_name(rig, coll, shot_active)
            action_name_is = rig.animation_data.action.name

            # If action name does not follow convention append it to wrong list.
            if action_name_is != action_name_should:
                logger.warning(
                    "Action %s should be named %s", action_name_is, action_name_should
                )
                self.wrong.append((rig.animation_data.action, action_name_should))

                # Extend action_names_cache list so any follow up items in loop can
                # access that information and adjust postfix accordingly.
                opsdata.action_names_cache.append(action_name_should)
                continue

            # Action name of rig is correct.
            correct.append(rig)

        if not self.wrong and self.empty_actions == []:
            self.report({"INFO"}, "All actions names are correct, no empty actions found")
            return {"FINISHED"}

        self.report(
            {"INFO"},
            f"Checked Rigs: {len(asset_rigs)} | Wrong Actions {len(correct)} | Correct Actions: {len(correct)} | No Actions: {len(no_action)}",
        )
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        for action, name in self.wrong:
            row = layout.row()
            row.label(text=action.name)
            row.label(text="", icon="FORWARD")
            row.label(text=name)
        layout.prop(
            self,
            "cleanup_empty_actions",
            text=f"Delete {len(self.empty_actions)} Empty Action Data-Blocks",
        )


class KITSU_OT_anim_enforce_naming_convention(bpy.types.Operator):
    bl_idname = "kitsu.anim_enforce_naming_convention"
    bl_label = "Set Name Conventions"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Fix Naming of Scene, Output Collection, Actions, and optionally Find and remove a given string"

    remove_str: bpy.props.StringProperty(
        name="Find and Replace",
        default="",
    )
    rename_scene: bpy.props.BoolProperty(name="Rename Scene", default=True)
    rename_output_col: bpy.props.BoolProperty(
        name="Rename Output Collection", default=True
    )
    find_replace: bpy.props.BoolProperty(
        name="Find and Remove",
        default=False,
        description="Remove this string from Collection, Object and Object Data names. Used to remove suffixes from file names such as '.001'",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "rename_scene")
        layout.prop(self, "rename_actions")
        layout.prop(self, "rename_output_col")
        layout.prop(self, "find_replace")
        if self.find_replace:
            layout.prop(self, "remove_str")

    def rename_datablock(self, data_block, replace: str):
        # Return Early if data_block is linked but not overriden
        if data_block is None or data_block.library is not None:
            return
        if replace in data_block.name:
            data_block.name = data_block.name.replace(replace, "")
            return data_block.name

    def execute(self, context: bpy.types.Context):
        shot_base_name = bpy.path.basename(bpy.data.filepath).replace(".anim.blend", "")
        scene_col = context.scene.collection
        anim_suffix = "anim.output"

        if self.find_replace:
            for col in scene_col.children_recursive:
                self.rename_datablock(col, self.remove_str)
                for obj in col.objects:
                    self.rename_datablock(obj, self.remove_str)
                    self.rename_datablock(obj.data, self.remove_str)

        if self.rename_output_col:
            output_cols = [
                col
                for col in context.scene.collection.children_recursive
                if anim_suffix in col.name
            ]
            if len(output_cols) != 1:
                self.report(
                    {"INFO"},
                    f"Animation Output Collection could not be found",
                )

                return {"CANCELLED"}
            output_col = output_cols[0]
            output_col.name = f"{shot_base_name}.{anim_suffix}"

        # Rename Scene
        if self.rename_scene:
            context.scene.name = f"{shot_base_name}.anim"

        self.report(
            {"INFO"},
            f"Naming Conventions Enforced",
        )
        return {"FINISHED"}


class KITSU_OT_unlink_collection_with_string(bpy.types.Operator):
    bl_idname = "kitsu.unlink_collection_with_string"
    bl_label = "Find and Unlink Collections"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Unlink any Collection with a given name. By default name is 'OVERRIDE_HIDDEN'"
    )

    remove_collection_string: bpy.props.StringProperty(
        name="Find in Name",
        default='OVERRIDE_HIDDEN',
        description="Search for this string withing current scene's collections. Collection will be unlinked if it matches given string'",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "remove_collection_string")

    def execute(self, context):
        scene_cols = context.scene.collection.children
        cols = [col for col in scene_cols if self.remove_collection_string in col.name]
        cleaned = False
        for col in cols:
            cleaned = True
            scene_cols.unlink(col)
            self.report(
                {"INFO"},
                f"Removed Collection '{col.name}'",
            )
        if not cleaned:
            self.report(
                {"INFO"},
                f"No Collections found containing name '{self.remove_collection_string}'",
            )
        return {"FINISHED"}


class KITSU_PG_anim_exclude_coll(bpy.types.PropertyGroup):
    exclude: bpy.props.BoolProperty(
        name="Exclude",
        description="",
        default=False,
        override={"LIBRARY_OVERRIDABLE"},
    )


class KITSU_OT_anim_update_output_coll(bpy.types.Operator):
    bl_idname = "kitsu.anim_update_output_coll"
    bl_label = "Update Output Collection"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Scans scene for any collections that are not yet in the output collection"
    )
    output_coll = None
    asset_colls = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        output_coll_name = cache.output_collection_name_get()
        try:
            output_coll = bpy.data.collections[output_coll_name]
        except KeyError:
            output_coll = None

        return bool(output_coll)

    def invoke(self, context, event):
        output_coll_name = cache.output_collection_name_get()
        self.output_coll = bpy.data.collections[output_coll_name]
        return context.window_manager.invoke_props_dialog(self, width=500)

    def get_collections(self, context):
        self.asset_colls = opsdata.find_asset_collections_in_scene(context.scene)
        # Only take parent colls.
        childs = []
        for i in range(len(self.asset_colls)):
            coll = self.asset_colls[i]
            coll_childs = list(opsdata.traverse_collection_tree(coll))
            for j in range(i + 1, len(self.asset_colls)):
                coll_comp = self.asset_colls[j]
                if coll_comp in coll_childs:
                    childs.append(coll_comp)

        return [coll for coll in self.asset_colls if coll not in childs]

    def draw(self, context):
        parents = self.get_collections(context)
        # Must display collections that already exist in output collection so user can exclude them
        for col in self.output_coll.children:
            parents.append(col)
        layout = self.layout
        box = layout.box()
        box.label(text="Select Collection to Exclude", icon="OUTLINER_COLLECTION")
        column = box.column(align=True)
        for col in parents:
            column.prop(col.anim_output, "exclude", text=col.name)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        # Clear Out Output Collection before Starting
        for collection in self.output_coll.children:
            self.output_coll.children.unlink(collection)
        bpy.context.view_layer.update()
        parents = self.get_collections(context)
        parents = [col for col in parents if not col.anim_output.exclude]
        for coll in parents:
            self.output_coll.children.link(coll)
            logger.info("%s linked in %s", coll.name, self.output_coll.name)

        # Ensure Camera Rig is Linked
        for coll in [col for col in bpy.data.collections]:
            if coll.override_library:
                if (
                    coll.override_library.hierarchy_root.name == "CA-camera_rig"
                ):  # TODO Fix this hack to be generic
                    self.output_coll.children.link(coll)

        self.report(
            {"INFO"},
            f"Found Asset Collections: {len(self.asset_colls)} | Added to output collection: {len(parents)}",
        )
        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [
    KITSU_OT_anim_quick_duplicate,
    KITSU_OT_anim_check_action_names,
    KITSU_OT_anim_update_output_coll,
    KITSU_OT_anim_enforce_naming_convention,
    KITSU_OT_unlink_collection_with_string,
    KITSU_PG_anim_exclude_coll,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Collection.anim_output = bpy.props.PointerProperty(
        type=KITSU_PG_anim_exclude_coll
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Collection.anim_output
