import bpy
from typing import Optional
from .util import *
from . import props

from .ops import (
    BZ_OT_SessionStart,
    BZ_OT_SessionEnd,
    BZ_OT_ProductionsLoad,
    BZ_OT_SequencesLoad,
    BZ_OT_ShotsLoad,
    BZ_OT_AssetsLoad,
    BZ_OT_AssetTypesLoad,
    BZ_OT_SQE_PushThumbnail,
    BZ_OT_SQE_InitShot,
    BZ_OT_SQE_InitShotBulk,
    BZ_OT_SQE_DelShotMeta,
    BZ_OT_SQE_LinkShot,
    BZ_OT_SQE_LinkSequence,
    BZ_OT_SQE_PushNewShot,
    BZ_OT_SQE_PushDeleteShot,
    BZ_OT_SQE_PushShotMeta,
    BZ_OT_SQE_PullShotMeta,
    BZ_OT_SQE_DebugDuplicates,
    BZ_OT_SQE_DebugNotLinked,
    BZ_OT_SQE_DebugMultiProjects,
)


def get_selshots_noun(context: bpy.types.Context, prefix: str = "Active") -> str:
    selshots = context.selected_sequences
    if not selshots:
        noun = "All"
    elif len(selshots) == 1:
        noun = f"{prefix} Shot"
    else:
        noun = "%i Shots" % len(selshots)

    return noun


class BZ_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        zsession = zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {prefs.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionStart.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionEnd.bl_idname, text="Logout", icon="PANEL_CLOSE")


class BZ_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        layout = self.layout
        category = prefs.category  # can be either 'SHOTS' or 'ASSETS'
        zproject_active = zproject_active_get()
        item_group_data = {
            "name": "Sequence",
            "zobject": zsequence_active_get(),
            "operator": BZ_OT_SequencesLoad.bl_idname,
        }
        item_data = {
            "name": "Shot",
            "zobject": zshot_active_get(),
            "operator": BZ_OT_ShotsLoad.bl_idname,
        }
        # Production
        layout.row().label(text=f"Production: {zproject_active.name}")

        # Category
        box = layout.box()
        row = box.row(align=True)
        row.prop(prefs, "category", expand=True)

        if not zsession_auth(context) or not zproject_active:
            row.enabled = False

        # Sequence / AssetType
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["zobject"] = zasset_type_active_get()
            item_group_data["operator"] = BZ_OT_AssetTypesLoad.bl_idname

        row = box.row(align=True)
        item_group_text = f"Select {item_group_data['name']}"

        if not zproject_active:
            row.enabled = False

        elif item_group_data["zobject"]:
            item_group_text = item_group_data["zobject"].name
        row.operator(
            item_group_data["operator"], text=item_group_text, icon="DOWNARROW_HLT"
        )

        # Shot / Asset
        if category == "ASSETS":
            item_data["name"] = "Asset"
            item_data["zobject"] = zasset_active_get()
            item_data["operator"] = BZ_OT_AssetsLoad.bl_idname

        row = box.row(align=True)
        item_text = f"Select {item_data['name']}"

        if not zproject_active and item_group_data["zobject"]:
            row.enabled = False

        elif item_data["zobject"]:
            item_text = item_data["zobject"].name

        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")


class BZ_PT_SQE_auth(bpy.types.Panel):
    """
    Panel in sequence editor that displays email, password and login operator.
    """

    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = addon_prefs_get(context)
        zsession = zsession_get(context)

        layout = self.layout

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.label(text=f"Email: {prefs.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionStart.bl_idname, text="Login", icon="PLAY")
        else:
            row.label(text=f"Logged in: {zsession.email}")
            row = layout.row(align=True)
            row.operator(BZ_OT_SessionEnd.bl_idname, text="Logout", icon="PANEL_CLOSE")


class BZ_PT_SQE_tools(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_idname = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "SEQ Editor Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        selshots = context.selected_sequences
        nr_of_shots = len(selshots)
        noun = get_selshots_noun(context)
        zproject_active = zproject_active_get()

        layout = self.layout

        # Production
        layout.row().label(text=f"Production: {zproject_active.name}")

        if nr_of_shots == 0:
            row = layout.row(align=True)
            # init all
            row.operator(
                BZ_OT_SQE_InitShotBulk.bl_idname, text=f"Bulk Init {noun}", icon="ADD"
            )

        elif nr_of_shots == 1:
            row = layout.row(align=True)

            if not strip.blezou.initialized:
                # init active
                row.operator(
                    BZ_OT_SQE_InitShot.bl_idname, text=f"Init {noun}", icon="ADD"
                )
                # link active
                row.operator(
                    BZ_OT_SQE_LinkShot.bl_idname,
                    text=f"Link {noun}",
                    icon="LINKED",
                )

            else:
                # relink active
                row.operator(
                    BZ_OT_SQE_LinkShot.bl_idname,
                    text=f"Relink {noun}",
                    icon="LINKED",
                )
                row = layout.row(align=True)
                # unlink active
                row.operator(
                    BZ_OT_SQE_DelShotMeta.bl_idname,
                    text=f"Unlink {noun}",
                    icon="CANCEL",
                )

        else:
            row = layout.row(align=True)

            # bul init
            row.operator(
                BZ_OT_SQE_InitShotBulk.bl_idname, text=f"Bulk Init {noun}", icon="ADD"
            )
            # unlink all
            row = layout.row(align=True)
            row.operator(
                BZ_OT_SQE_DelShotMeta.bl_idname,
                text=f"Unlink {noun}",
                icon="CANCEL",
            )


class BZ_PT_SQE_shot_meta(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Metadata"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.initialized
        return False

    def draw(self, context: bpy.types.Context) -> None:

        strip = context.scene.sequence_editor.active_strip
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        # sequence
        sub_row = col.row(align=True)
        sub_row.prop(strip.blezou, "sequence_name")
        sub_row.operator(BZ_OT_SQE_LinkSequence.bl_idname, text="", icon="LINKED")

        # shot
        col.prop(strip.blezou, "shot_name")

        # description
        col.prop(strip.blezou, "shot_description")
        col.enabled = False if not strip.blezou.initialized else True

        # not editable
        col = box.column(align=True)
        col.enabled = False


class BZ_PT_SQE_push(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Push"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.initialized

        return True

    def draw(self, context: bpy.types.Context) -> None:
        nr_of_shots = len(context.selected_sequences)
        layout = self.layout
        strip = context.scene.sequence_editor.active_strip
        noun_active = get_selshots_noun(context, prefix="Active")
        noun_new = get_selshots_noun(context, prefix="New")

        # special case if one shot is selected and it is init but not linked
        # shows the operator but it is not enabled until user types in required metadata
        if nr_of_shots == 1 and not strip.blezou.linked:
            # new operator
            row = layout.row()
            col = row.column(align=True)
            col.operator(
                BZ_OT_SQE_PushNewShot.bl_idname,
                text=f"Submit {noun_new}",
                icon="ADD",
            )
            return

        # either way no selection one selection but linked or multiple

        # metadata operator
        row = layout.row()
        col = row.column(align=True)
        col.operator(
            BZ_OT_SQE_PushShotMeta.bl_idname,
            text=f"Metadata {noun_active}",
            icon="SEQ_STRIP_META",
        )

        # thumbnail operator
        col.operator(
            BZ_OT_SQE_PushThumbnail.bl_idname,
            text=f"Thumbnail {noun_active}",
            icon="IMAGE_DATA",
        )

        # delete and new operator
        if nr_of_shots > 0:

            row = layout.row()
            col = row.column(align=True)
            col.operator(
                BZ_OT_SQE_PushNewShot.bl_idname,
                text=f"Submit {noun_new}",
                icon="ADD",
            )

            col.operator(
                BZ_OT_SQE_PushDeleteShot.bl_idname,
                text=f"Delete {noun_active}",
                icon="KEYTYPE_EXTREME_VEC",
            )


class BZ_PT_SQE_pull(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Pull"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # if only one strip is selected and it is not init then hide panel
        nr_of_shots = len(context.selected_sequences)
        strip = context.scene.sequence_editor.active_strip
        if nr_of_shots == 1:
            return strip.blezou.linked
        return True

    def draw(self, context: bpy.types.Context) -> None:
        noun = get_selshots_noun(context)

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_PullShotMeta.bl_idname,
            text=f"Metadata {noun}",
            icon="SEQ_STRIP_META",
        )


class BZ_PT_SQE_debug(bpy.types.Panel):
    """
    Panel that shows operator to open a debug ui
    """

    bl_parent_id = "BZ_PT_SQE_tools"
    bl_category = "Blezou"
    bl_label = "Debug"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 40
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        noun = get_selshots_noun(context)

        layout = self.layout
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugDuplicates.bl_idname,
            text=f"Duplicates {noun}",
            icon="MODIFIER_ON",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugNotLinked.bl_idname,
            text=f"Not Linked {noun}",
            icon="MODIFIER_ON",
        )
        row = layout.row()
        row.operator(
            BZ_OT_SQE_DebugMultiProjects.bl_idname,
            text=f"Multi Projects {noun}",
            icon="MODIFIER_ON",
        )


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_SQE_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_tools,
    BZ_PT_SQE_shot_meta,
    BZ_PT_SQE_push,
    BZ_PT_SQE_pull,
    BZ_PT_SQE_debug,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
