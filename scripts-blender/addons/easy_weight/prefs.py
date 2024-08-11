# SPDX-License-Identifier: GPL-2.0-or-later

import bpy, json
from bpy.props import BoolProperty
from . import __package__ as base_package
from bpy.app.handlers import persistent

def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    if base_package.startswith('bl_ext'):
        # 4.2
        return context.preferences.addons[base_package].preferences
    else:
        return context.preferences.addons[base_package.split(".")[0]].preferences


class EASYWEIGHT_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    easyweight_keymap_items = {}

    always_show_zero_weights: BoolProperty(
        name="Always Show Zero Weights",
        description="A lack of weights will always be indicated with black color to differentiate it from a weight of 0.0 being assigned",
        default=True,
    )
    always_auto_normalize: BoolProperty(
        name="Always Auto Normalize",
        description="Weight auto-normalization will always be turned on, so the sum of all deforming weights on a vertex always add up to 1",
        default=True,
    )
    always_multipaint: BoolProperty(
        name="Always Multi-Paint",
        description="Multi-paint will always be turned on, allowing you to select more than one deforming bone while weight painting",
        default=True,
    )
    auto_clean_weights: BoolProperty(
        name="Always Auto Clean",
        description="While this is enabled, zero-weights will be removed automatically after every brush stroke",
        default=True,
    )

    def update_front_faces(self, context):
        for brush in bpy.data.brushes:
            if not brush.use_paint_weight:
                continue
            brush.use_frontface = self.global_front_faces_only

    def update_accumulate(self, context):
        for brush in bpy.data.brushes:
            if not brush.use_paint_weight:
                continue
            brush.use_accumulate = self.global_accumulate

    def update_falloff_shape(self, context):
        for brush in bpy.data.brushes:
            if not brush.use_paint_weight:
                continue
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

        main_col = layout.column(align=True)
        hotkey_col = self.draw_fake_dropdown(main_col, self, 'show_hotkeys', "Hotkeys")
        if self.show_hotkeys:
            type(self).draw_hotkey_list(hotkey_col, context)

    # NOTE: This function is copied from CloudRig's prefs.py.
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

    # NOTE: This function is copied from CloudRig's prefs.py.
    @classmethod
    def draw_hotkey_list(cls, layout, context):
        hotkey_class = cls
        user_kc = context.window_manager.keyconfigs.user

        keymap_data = list(hotkey_class.easyweight_keymap_items.items())
        keymap_data = sorted(keymap_data, key=lambda tup: tup[1][2].name)

        prev_kmi = None
        for kmi_hash, kmi_tup in keymap_data:
            addon_kc, addon_km, addon_kmi = kmi_tup

            user_km = user_kc.keymaps.get(addon_km.name)
            if not user_km:
                # This really shouldn't happen.
                continue
            user_kmi = hotkey_class.find_kmi_in_km_by_hash(user_km, kmi_hash)

            col = layout.column()
            col.context_pointer_set("keymap", user_km)
            if user_kmi and prev_kmi and prev_kmi.name != user_kmi.name:
                col.separator()
            user_row = col.row()

            if False:
                # Debug code: Draw add-on and user KeyMapItems side-by-side.
                split = user_row.split(factor=0.5)
                addon_row = split.row()
                user_row = split.row()
                hotkey_class.draw_kmi(addon_km, addon_kmi, addon_row)
            if not user_kmi:
                # This should only happen for one frame during Reload Scripts.
                print(
                    "EasyWeight: Can't find this hotkey to draw: ",
                    addon_kmi.name,
                    addon_kmi.to_string(),
                    kmi_hash,
                )
                continue

            hotkey_class.draw_kmi(user_km, user_kmi, user_row)
            prev_kmi = user_kmi

    # NOTE: This function is copied from CloudRig's cloudrig.py.
    @staticmethod
    def draw_kmi(km, kmi, layout):
        """A simplified version of draw_kmi from rna_keymap_ui.py."""

        map_type = kmi.map_type

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

@persistent
def set_brush_prefs_on_file_load(scene):
    prefs = get_addon_prefs()
    prefs.global_front_faces_only = prefs.global_front_faces_only
    prefs.global_accumulate = prefs.global_accumulate
    prefs.global_falloff_shape_sphere = prefs.global_falloff_shape_sphere


# NOTE: This function is copied from CloudRig's cloudrig.py.
def register_hotkey(
    bl_idname, hotkey_kwargs, *, key_cat='Window', space_type='EMPTY', op_kwargs={}
):
    """This function inserts a 'hash' into the created KeyMapItems' properties,
    so they can be compared to each other, and duplicates can be avoided."""

    wm = bpy.context.window_manager
    prefs_class = bpy.types.AddonPreferences.bl_rna_get_subclass_py('EASYWEIGHT_addon_preferences')

    addon_keyconfig = wm.keyconfigs.addon
    if not addon_keyconfig:
        # This happens when running Blender in background mode.
        return

    # We limit the hash to a few digits, otherwise it errors when trying to store it.
    kmi_hash = (
        hash(json.dumps([bl_idname, hotkey_kwargs, key_cat, space_type, op_kwargs])) % 1000000
    )

    # If it already exists, don't create it again.
    for (
        existing_kmi_hash,
        existing_kmi_tup,
    ) in prefs_class.easyweight_keymap_items.items():
        existing_addon_kc, existing_addon_km, existing_kmi = existing_kmi_tup
        if kmi_hash == existing_kmi_hash:
            # The hash we just calculated matches one that is in storage.
            user_kc = wm.keyconfigs.user
            user_km = user_kc.keymaps.get(existing_addon_km.name)
            # NOTE: It's possible on Reload Scripts that some KeyMapItems remain in storage,
            # but are unregistered by Blender for no reason.
            # I noticed this particularly in the Weight Paint keymap.
            # So it's not enough to check if a KMI with a hash is in storage, we also need to check if a corresponding user KMI exists.
            user_kmi = prefs_class.find_kmi_in_km_by_hash(user_km, kmi_hash)
            if user_kmi:
                # print("Hotkey already exists, skipping: ", existing_kmi.name, existing_kmi.to_string(), kmi_hash)
                return

    addon_keymaps = addon_keyconfig.keymaps
    addon_km = addon_keymaps.get(key_cat)
    if not addon_km:
        addon_km = addon_keymaps.new(name=key_cat, space_type=space_type)

    addon_kmi = addon_km.keymap_items.new(bl_idname, **hotkey_kwargs)
    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(addon_kmi.properties, key, value)

    addon_kmi.properties['hash'] = kmi_hash

    prefs_class.easyweight_keymap_items[kmi_hash] = (
        addon_keyconfig,
        addon_km,
        addon_kmi,
    )


registry = [EASYWEIGHT_addon_preferences]


def register():
    register_hotkey(
        'wm.call_menu_pie',
        hotkey_kwargs={'type': "W", 'value': "PRESS"},
        key_cat='Weight Paint',
        op_kwargs={'name': 'EASYWEIGHT_MT_PIE_easy_weight'},
    )
    register_hotkey(
        bl_idname='object.weight_paint_toggle',
        hotkey_kwargs={'type': 'TAB', 'value': 'PRESS', 'ctrl': True},
        key_cat='3D View',
    )

    bpy.app.handlers.load_post.append(set_brush_prefs_on_file_load)


def unregister_hotkeys():
    prefs_class = bpy.types.AddonPreferences.bl_rna_get_subclass_py('EASYWEIGHT_addon_preferences')
    if not prefs_class:
        return
    for kmi_hash, kmi_tup in prefs_class.easyweight_keymap_items.items():
        kc, km, kmi = kmi_tup
        km.keymap_items.remove(kmi)
    prefs_class.easyweight_keymap_items = {}


def unregister():
    unregister_hotkeys()

    bpy.app.handlers.load_post.remove(set_brush_prefs_on_file_load)
