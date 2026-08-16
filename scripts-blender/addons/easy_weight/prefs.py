# SPDX-FileCopyrightText: 2024-2026 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty
from bpy.types import Context, KeyMap, KeyMapItem, UILayout

from .prefs_to_disk import PrefsFileSaveLoadMixin, update_prefs_on_file
from .weight_cleaner import start_cleaner, stop_cleaner


def get_available_wp_brushes():
    for brush in bpy.data.brushes:
        if brush.use_paint_weight:
            yield brush


class EASYWEIGHT_addon_preferences(PrefsFileSaveLoadMixin, bpy.types.AddonPreferences):
    bl_idname = __package__

    always_show_zero_weights: BoolProperty(
        name="Always Show Zero Weights",
        description="A lack of weights will always be indicated with black color to differentiate it from a weight of 0.0 being assigned",
        default=True,
        update=update_prefs_on_file,
    )
    always_auto_normalize: BoolProperty(
        name="Always Auto Normalize",
        description="Weight auto-normalization will always be turned on, so the sum of all deforming weights on a vertex always add up to 1",
        default=True,
        update=update_prefs_on_file,
    )
    always_multipaint: BoolProperty(
        name="Always Multi-Paint",
        description="Multi-paint will always be turned on, allowing you to select more than one deforming bone while weight painting",
        default=True,
        update=update_prefs_on_file,
    )
    always_xray: BoolProperty(
        name="Always X-Ray",
        description="Always enable bone x-ray when entering weight paint mode",
        default=True,
        update=update_prefs_on_file,
    )
    always_reveal_armature: BoolProperty(
        name="Always Reveal Armature",
        description="Automatically make the deforming armature visible (unhide it, take it out of local view, or link it to the scene if needed) when entering Weight Paint mode, and restore its previous visibility when leaving",
        default=True,
        update=update_prefs_on_file,
    )
    always_unify_brush_settings: BoolProperty(
        name="Always Apply Brush Settings",
        description="Apply global brush settings when entering Weight Paint mode",
        default=True,
        update=update_prefs_on_file,
    )

    def update_auto_clean(self, _context: Context):
        update_prefs_on_file()
        if self.auto_clean_weights:
            start_cleaner()
        else:
            stop_cleaner()

    auto_clean_weights: BoolProperty(
        name="Always Auto Clean",
        description="While this is enabled, zero-weights will be removed automatically after every brush stroke",
        default=True,
    )

    def update_front_faces(self, _context: Context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.use_frontface = self.global_front_faces_only

    def update_accumulate(self, _context: Context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.use_accumulate = self.global_accumulate

    def update_falloff_shape(self, _context: Context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.falloff_shape = (
                "SPHERE" if self.global_falloff_shape_sphere else "PROJECTED"
            )
            for i, val in enumerate(brush.cursor_color_add):
                if val > 0:
                    brush.cursor_color_add[i] = (
                        0.5 if self.global_falloff_shape_sphere else 1.0
                    )

    def update_unified_strength(self, context: Context):
        update_prefs_on_file()
        if hasattr(context.tool_settings, 'unified_paint_settings'):
            # Blender 4.x
            owner = context.tool_settings
        else:
            # Blender 5.x
            owner = context.tool_settings.weight_paint
        owner.unified_paint_settings.use_unified_strength = self.global_unified_strength

    global_front_faces_only: BoolProperty(
        name="Front Faces Only",
        description="All weight brushes are able to paint on geometry that is facing away from the viewport",
        update=update_front_faces,
    )
    global_accumulate: BoolProperty(
        name="Accumulate",
        description="All weight paint brushes will accumulate their effect within a single stroke as you move the mouse",
        update=update_accumulate,
    )
    global_falloff_shape_sphere: BoolProperty(
        name="Falloff Shape",
        description="All weight paint brushes switch between a 3D spherical or a 2D projected circular falloff shape",
        update=update_falloff_shape,
    )
    global_unified_strength: BoolProperty(
        name="Unified Strength",
        description="All weight paint brushes share the same Strength value, instead of each brush having its own",
        update=update_unified_strength,
    )

    set_add_blend_mode: BoolProperty(
        name="Additive Paint",
        description="Set the Blend Mode of the `Paint` brush to `Add`",
        default=True,
    )

    def draw(self, context: Context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(self, "auto_clean_weights")
        if bpy.app.version < (5, 0, 0):
            col.prop(self, "always_show_zero_weights")
        col.prop(self, "always_auto_normalize")
        col.prop(self, "always_multipaint")
        col.prop(self, "always_xray")
        col.prop(self, "always_reveal_armature")

        brush_col = layout.column(align=True)
        brush_header, brush_panel = brush_col.panel(
            "EasyWeight Unified Brush Settings", default_closed=True
        )
        header_row = brush_header.row()
        header_row.label(text="Unified Brush Settings")
        if brush_panel:
            col = brush_panel.column(align=True)
            col.prop(self, "always_unify_brush_settings")
            col.prop(self, "global_front_faces_only")
            col.prop(self, "global_accumulate")
            col.prop(self, "global_unified_strength")
            if bpy.app.version < (5, 3, 0):
                col.prop(self, "set_add_blend_mode")
            text, icon = ("Sphere", "SPHERE") if self.global_falloff_shape_sphere else ("Circle", "MESH_CIRCLE")
            split = col.row().split(factor=0.4)
            split.use_property_split = False
            row = split.row()
            row.alignment = 'RIGHT'
            row.label(text="Falloff Shape: ")
            split.prop(
                self,
                "global_falloff_shape_sphere",
                text=text,
                icon=icon,
                invert_checkbox=self.global_falloff_shape_sphere,
                toggle=True,
            )

        main_col = layout.column(align=True)
        hotkey_header, hotkey_panel = main_col.panel(
            "EasyWeight Hotkeys", default_closed=False
        )
        hotkey_header.label(text="Hotkeys")
        if hotkey_panel:
            type(self).draw_hotkey_list(context, hotkey_panel)

    @classmethod
    def draw_hotkey_list(cls, context: Context, layout: UILayout):
        hotkey_class = cls
        user_kc = context.window_manager.keyconfigs.user

        global EASYWEIGHT_KEYMAPS

        prev_kmi = None
        for addon_km, addon_kmi in EASYWEIGHT_KEYMAPS:
            user_km = user_kc.keymaps.get(addon_km.name)
            if not user_km:
                # This really shouldn't happen.
                continue
            for user_kmi in user_km.keymap_items:
                if user_kmi.idname != addon_kmi.idname:
                    continue
                if (
                    user_kmi.idname == "wm.call_menu_pie"
                    and user_kmi.properties.name != addon_kmi.properties.name
                ):
                    continue
                col = layout.column()
                col.context_pointer_set("keymap", user_km)
                if user_kmi and prev_kmi and prev_kmi.name != user_kmi.name:
                    col.separator()
                user_row = col.row()

                hotkey_class.draw_kmi(user_km, user_kmi, user_row)
                break

    # NOTE: This function is copied from CloudRig's cloudrig.py.
    @staticmethod
    def draw_kmi(km: KeyMap, kmi: KeyMapItem, layout: UILayout):
        """A simplified version of draw_kmi from rna_keymap_ui.py."""
        col = layout.column()

        split = col.split(factor=0.7)

        # header bar
        row = split.row(align=True)
        row.prop(kmi, "active", text="", emboss=False)
        row.label(text=f"{kmi.name} ({km.name})")

        row = split.row(align=True)
        sub = row.row(align=True)
        sub.enabled = kmi.active
        sub.prop(kmi, "type", text="", full_event=True)

        if kmi.is_user_modified:
            row.operator(
                "preferences.keyitem_restore", text="", icon="BACK"
            ).item_id = kmi.id


EASYWEIGHT_KEYMAPS = []


def register_hotkey(
    bl_idname, hotkey_kwargs, *, key_cat="Window", space_type="EMPTY", op_kwargs={}
):
    """This function inserts a 'hash' into the created KeyMapItems' properties,
    so they can be compared to each other, and duplicates can be avoided."""

    wm = bpy.context.window_manager
    addon_keyconfig = wm.keyconfigs.addon
    if not addon_keyconfig:
        # This happens when running Blender in background mode.
        return

    addon_keymaps = addon_keyconfig.keymaps
    addon_km = addon_keymaps.get(key_cat)
    if not addon_km:
        addon_km = addon_keymaps.new(name=key_cat, space_type=space_type)

    addon_kmi = addon_km.keymap_items.new(bl_idname, **hotkey_kwargs)
    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(addon_kmi.properties, key, value)

    global EASYWEIGHT_KEYMAPS
    EASYWEIGHT_KEYMAPS.append((addon_km, addon_kmi))


registry = [EASYWEIGHT_addon_preferences]


def register():
    register_hotkey(
        "wm.call_menu_pie",
        hotkey_kwargs={"type": "W", "value": "PRESS"},
        key_cat="Weight Paint",
        op_kwargs={"name": "EASYWEIGHT_MT_PIE_easy_weight"},
    )
    EASYWEIGHT_addon_preferences.register_autoload_from_file()


def unregister_hotkeys():
    for km, kmi in EASYWEIGHT_KEYMAPS:
        km.keymap_items.remove(kmi)


def unregister():
    unregister_hotkeys()
