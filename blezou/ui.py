import bpy
from typing import Optional
from .util import prefs_get, zsession_get, zsession_auth


class BZ_PT_vi3d_auth(bpy.types.Panel):
    """
    Panel in 3dview that displays email, password and login operator.
    """

    bl_idname = "panel.bz_auth"
    bl_category = "Blezou"
    bl_label = "Kitsu Login"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 10

    def draw(self, context: bpy.types.Context) -> None:
        prefs = context.preferences.addons["blezou"].preferences
        zsession = prefs.session

        layout = self.layout

        box = layout.box()
        # box.row().prop(prefs, 'host')
        box.row().prop(prefs, "email")
        box.row().prop(prefs, "passwd")

        row = layout.row(align=True)
        if not zsession.is_auth():
            row.operator("blezou.session_start", text="Login")
        else:
            row.operator("blezou.session_end", text="Logout")


class BZ_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_idname = "panel.bz_vi3d_context"
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
        prefs = prefs_get(context)
        layout = self.layout

        # Production
        if not prefs["project_active"]:
            prod_load_text = "Select Production"
        else:
            prod_load_text = prefs["project_active"]["name"]

        box = layout.box()
        row = box.row(align=True)
        row.operator(
            "blezou.productions_load", text=prod_load_text, icon="DOWNARROW_HLT"
        )

        # Category
        row = box.row(align=True)
        if not prefs["project_active"]:
            row.enabled = False
        row.prop(prefs, "category", expand=True)

        # Sequence
        row = box.row(align=True)
        seq_load_text = "Select Sequence"
        if not prefs["project_active"]:
            row.enabled = False
        elif prefs["sequence_active"]:
            seq_load_text = prefs["sequence_active"]["name"]
            # seq_load_text = 'Select Sequence'
        row.operator("blezou.sequences_load", text=seq_load_text, icon="DOWNARROW_HLT")

        # Shot
        row = box.row(align=True)
        shot_load_text = "Select Shot"
        if not prefs["project_active"] and prefs["sequence_active"]:
            row.enabled = False
        elif prefs["shot_active"]:
            shot_load_text = prefs["shot_active"]["name"]
            # seq_load_text = 'Select Sequence'
        row.operator("blezou.shots_load", text=shot_load_text, icon="DOWNARROW_HLT")


class BZ_PT_SQE_context(bpy.types.Panel):
    """
    Panel in sequence editor that only shows active production browser operator.
    """

    bl_idname = "panel.bz_sqe_context"
    bl_category = "Blezou"
    bl_label = "Context"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 10

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)
        layout = self.layout

        # Production
        if not prefs["project_active"]:
            prod_load_text = "Select Production"
        else:
            prod_load_text = prefs["project_active"]["name"]

        box = layout.box()
        row = box.row(align=True)
        row.operator(
            "blezou.productions_load", text=prod_load_text, icon="DOWNARROW_HLT"
        )


class BZ_PT_SQE_strip_props(bpy.types.Panel):
    """
    Panel in sequence editor that shows .blezou properties of active strip. (shot, sequence)
    """

    bl_idname = "panel.bz_sqe_strip_props"
    bl_category = "Blezou"
    bl_label = "Strip Properties"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> Optional[bpy.types.Sequence]:
        return context.scene.sequence_editor.active_strip

    def draw(self, context: bpy.types.Context) -> None:
        active_strip_prop = context.scene.sequence_editor.active_strip.blezou

        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.prop(active_strip_prop, "sequence")
        row = box.row(align=True)
        row.prop(active_strip_prop, "shot")


class BZ_PT_SQE_sync(bpy.types.Panel):
    """
    Panel that shows operator to sync sequence editor metadata with backend.
    """

    bl_idname = "panel.bz_sqe_sync"
    bl_category = "Blezou"
    bl_label = "Sync"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_order = 30

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return zsession_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = prefs_get(context)

        layout = self.layout
        row = layout.row(align=True)
        row.operator("blezou.sqe_scan_track_properties", text="Scan Sequence Editor")

        """
        box = layout.box()
        row = box.row(align=True)
        row.prop(prefs, 'sqe_track_props') #TODO: Dosn"t work blender complaints it does not exist, manualli in script editr i can retrieve it
        """
        row = layout.row(align=True)
        row.operator("blezou.sqe_sync_track_properties", text=f"Push to: {prefs.host}")


# ---------REGISTER ----------

classes = [
    BZ_PT_vi3d_auth,
    BZ_PT_vi3d_context,
    BZ_PT_SQE_context,
    BZ_PT_SQE_strip_props,
    BZ_PT_SQE_sync,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)