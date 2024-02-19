import bpy
from .. import prefs, ui
from ..context import core as context_core
from pathlib import Path
from .ops import (
    KITSU_OT_edit_render_set_version,
    KITSU_OT_edit_render_increment_version,
    KITSU_OT_edit_render_publish,
    KITSU_OT_edit_render_import_latest,
)
from ..generic.ops import KITSU_OT_open_path


class KITSU_PT_edit_render_publish(bpy.types.Panel):
    """
    Panel in sequence editor that exposes a set of tools that are used to render latest edit
    """

    bl_category = "Kitsu"
    bl_label = "Render & Publish"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(prefs.session_auth(context) and context_core.is_edit_context())

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        split_factor_small = 0.95

        # # ERROR.
        if not addon_prefs.is_edit_render_root_valid:
            box = ui.draw_error_box(layout)
            ui.draw_error_invalid_edit_render_root_dir(box)

        # Edit Render version op.
        row = layout.row(align=True)
        row.operator(
            KITSU_OT_edit_render_set_version.bl_idname,
            text=context.scene.kitsu.edit_render_version,
            icon="DOWNARROW_HLT",
        )
        # Edit Render increment version op.
        row.operator(
            KITSU_OT_edit_render_increment_version.bl_idname,
            text="",
            icon="ADD",
        )

        # Edit Render op.
        row = layout.row(align=True)
        row.operator(KITSU_OT_edit_render_publish.bl_idname, icon="RENDER_ANIMATION")

        # Edit Render path label.
        if Path(context.scene.kitsu.edit_render_file).exists():
            split = layout.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.edit_render_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.edit_render_file
        else:
            row = layout.row(align=True)
            row.label(text=context.scene.kitsu.edit_render_file)
            row.operator(KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text="").filepath = (
                context.scene.kitsu.edit_render_file
            )


class KITSU_PT_edit_render_tools(bpy.types.Panel):
    """
    Panel in sequence editor that exposes a set of tools that are used to load the latest edit
    """

    bl_category = "Kitsu"
    bl_label = "General Tools"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not prefs.session_auth(context):
            return False

        if not (context_core.is_sequence_context() or context_core.is_shot_context()):
            return False
        return True

    def draw(self, context: bpy.types.Context) -> None:
        box = self.layout.box()
        box.label(text="General", icon="MODIFIER")
        box.operator(KITSU_OT_edit_render_import_latest.bl_idname)


classes = [KITSU_PT_edit_render_publish, KITSU_PT_edit_render_tools]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
