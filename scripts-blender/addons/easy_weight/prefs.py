# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, os
from bpy.props import BoolProperty
from bpy.app.handlers import persistent

from .weight_cleaner import start_cleaner, stop_cleaner
from .utils import get_addon_prefs
from .prefs_to_disk import PrefsFileSaveLoadMixin, update_prefs_on_file
from pathlib import Path

def ensure_brush_assets():
    # Since the Brush Assets in Blender 4.3, brushes are not local to the .blend file 
    # until they are first accessed, so let's do that when needed. We also can't check 
    # whether these brushes exist without looping over all of them.
    for brush_name in ('Blur', 'Paint'):
        brush = next((brush for brush in bpy.data.brushes if brush.use_paint_weight and brush.name==brush_name), None)
        if not brush:
            # Append the brush from the `datafiles` folder.
            blend_path = os.path.abspath((Path(bpy.utils.resource_path('LOCAL')) / "datafiles/assets/brushes/essentials_brushes-mesh_weight.blend").as_posix())
            with bpy.data.libraries.load(blend_path, link=True) as (data_from, data_to):
                data_to.brushes = [brush_name]
            brush = bpy.data.brushes.get((brush_name, blend_path))
            if not brush:
                brush = bpy.data.brushes.get(brush_name)
        if brush_name == 'Paint' and brush:
            brush.blend = 'ADD'

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

    show_hotkeys: BoolProperty(
        name="Show Hotkeys",
        description="Reveal the hotkey list. You may customize or disable these hotkeys",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(self, 'auto_clean_weights')
        col.prop(self, 'always_show_zero_weights')
        col.prop(self, 'always_auto_normalize')
        col.prop(self, 'always_multipaint')
        col.prop(self, 'always_xray')

        main_col = layout.column(align=True)
        hotkey_col = self.draw_fake_dropdown(main_col, self, 'show_hotkeys', "Hotkeys")
        if self.show_hotkeys:
            type(self).draw_hotkey_list(hotkey_col, context)

    # NOTE: This function is copied from CloudRig's prefs.py. TODO: No longer needed since like 4.2 or so, could just use layout.panel(), but then bump the minimum blender version.
    def draw_fake_dropdown(self, layout, prop_owner, prop_name, dropdown_text):
        row = layout.row()
        split = row.split(factor=0.20)
        split.use_property_split = False
        prop_value = prop_owner.path_resolve(prop_name)
        icon = 'TRIA_DOWN' if prop_value else 'TRIA_RIGHT'
        split.prop(prop_owner, prop_name, icon=icon, emboss=False, text=dropdown_text)
        split.prop(prop_owner, prop_name, icon='BLANK1', emboss=False, text="")
        split = layout.split(factor=0.012)
        split.row()
        dropdown_row = split.row()
        dropdown_col = dropdown_row.column()
        row = dropdown_col.row()
        row.use_property_split = False

        return dropdown_col

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

@persistent
def set_brush_prefs_on_file_load(scene):
    if bpy.app.version >= (4, 3, 0):
        ensure_brush_assets()
    prefs = get_addon_prefs()
    prefs.global_front_faces_only = prefs.global_front_faces_only
    prefs.global_accumulate = prefs.global_accumulate
    prefs.global_falloff_shape_sphere = prefs.global_falloff_shape_sphere


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
    bpy.app.handlers.load_post.append(set_brush_prefs_on_file_load)
    EASYWEIGHT_addon_preferences.register_autoload_from_file()


def unregister_hotkeys():
    for km, kmi in EASYWEIGHT_KEYMAPS:
        km.keymap_items.remove(kmi)


def unregister():
    unregister_hotkeys()
    bpy.app.handlers.load_post.remove(set_brush_prefs_on_file_load)
