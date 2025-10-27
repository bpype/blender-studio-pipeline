# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty

from .weight_cleaner import start_cleaner, stop_cleaner
from .prefs_to_disk import PrefsFileSaveLoadMixin, update_prefs_on_file

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

    def update_auto_clean(self, context):
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

    def update_front_faces(self, context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.use_frontface = self.global_front_faces_only

    def update_accumulate(self, context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.use_accumulate = self.global_accumulate

    def update_falloff_shape(self, context):
        update_prefs_on_file()
        for brush in get_available_wp_brushes():
            brush.falloff_shape = 'SPHERE' if self.global_falloff_shape_sphere else 'PROJECTED'
            for i, val in enumerate(brush.cursor_color_add):
                if val > 0:
                    brush.cursor_color_add[i] = 0.5 if self.global_falloff_shape_sphere else 2.0

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

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(self, 'auto_clean_weights')
        if bpy.app.version < (5, 0, 0):
            col.prop(self, 'always_show_zero_weights')
        col.prop(self, 'always_auto_normalize')
        col.prop(self, 'always_multipaint')
        col.prop(self, 'always_xray')

        main_col = layout.column(align=True)
        hotkey_header, hotkey_panel = main_col.panel("EasyWeight Hotkeys", default_closed=False)
        hotkey_header.label(text="Hotkeys")
        if hotkey_panel:
            type(self).draw_hotkey_list(hotkey_panel, context)

    @classmethod
    def draw_hotkey_list(cls, layout, context):
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
                if user_kmi.idname == 'wm.call_menu_pie' and user_kmi.properties.name != addon_kmi.properties.name:
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
    def draw_kmi(km, kmi, layout):
        """A simplified version of draw_kmi from rna_keymap_ui.py."""
        col = layout.column()

        split = col.split(factor=0.7)

        # header bar
        row = split.row(align=True)
        row.prop(kmi, "active", text="", emboss=False)
        row.label(text=f'{kmi.name} ({km.name})')

        row = split.row(align=True)
        sub = row.row(align=True)
        sub.enabled = kmi.active
        sub.prop(kmi, "type", text="", full_event=True)

        if kmi.is_user_modified:
            row.operator("preferences.keyitem_restore", text="", icon='BACK').item_id = kmi.id

    # NOTE: This function is copied from CloudRig's cloudrig.py.
    @staticmethod
    def find_kmi_in_km_by_hash(keymap, kmi_hash):
        """There's no solid way to match modified user keymap items to their
        add-on equivalent, which is necessary to draw them in the UI reliably.

        To remedy this, we store a hash in the KeyMapItem's properties.

        This function lets us find a KeyMapItem with a stored hash in a KeyMap.
        Eg., we can pass a User KeyMap and an Addon KeyMapItem's hash, to find the
        corresponding user keymap, even if it was modified.

        The hash value is unfortunately exposed to the users, so we just hope they don't touch that.
        """

        for kmi in keymap.keymap_items:
            if not kmi.properties:
                continue
            if 'hash' not in kmi.properties:
                continue

            if kmi.properties['hash'] == kmi_hash:
                return kmi

EASYWEIGHT_KEYMAPS = []



def register_hotkey(
    bl_idname, hotkey_kwargs, *, key_cat='Window', space_type='EMPTY', op_kwargs={}
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
        'wm.call_menu_pie',
        hotkey_kwargs={'type': "W", 'value': "PRESS"},
        key_cat='Weight Paint',
        op_kwargs={'name': 'EASYWEIGHT_MT_PIE_easy_weight'},
    )
    EASYWEIGHT_addon_preferences.register_autoload_from_file()


def unregister_hotkeys():
    for km, kmi in EASYWEIGHT_KEYMAPS:
        km.keymap_items.remove(kmi)


def unregister():
    unregister_hotkeys()
