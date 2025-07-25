# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ImportHelper
from . import utils
import os

@persistent
def load_handler(dummy):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if not addon_prefs.resource_path:
        utils.unpack_resources()
    utils.refresh_brushstroke_styles()

def update_resource_path(self, context):
    if utils.get_resource_directory() == utils.get_default_resource_directory():
        utils.unpack_resources()
    utils.update_asset_lib_path()

class BSBST_OT_install_brush_style_pack(bpy.types.Operator, ImportHelper):
    bl_idname = "brushstroke_tools.install_brush_style_pack"
    bl_label = "Install Brush Style Pack"

    filter_glob: bpy.props.StringProperty(
        default='*.zip;*.blend',
        options={'HIDDEN'}
        )
    
    def execute(self, context):
        """ Install selected brush style pack at resource location and refresh available brush styles.
        """
        
        install_state = utils.install_brush_style_pack(self.filepath, ot=self)
        if not install_state:
            return {'CANCELLED'}
        
        utils.refresh_brushstroke_styles()
        
        return {'FINISHED'}

class BSBST_OT_refresh_brushstroke_styles(bpy.types.Operator):
    """
    """
    bl_idname = "brushstroke_tools.refresh_styles"
    bl_label = "Refresh Brushstroke Styles"
    bl_description = "Refresh available brushstroke styles from library."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        utils.refresh_brushstroke_styles()
        return {"FINISHED"}
class BSBST_OT_copy_resources_to_path(bpy.types.Operator):
    """
    Copy Resources to Directory.
    """
    bl_idname = "brushstroke_tools.copy_resources"
    bl_label = "Copy Resources"
    bl_description = "Copy addon resources to local directory"
    bl_options = {"REGISTER", "UNDO"}

    update: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        addon_prefs = context.preferences.addons[__package__].preferences
        return os.path.isdir(addon_prefs.resource_path)

    def execute(self, context):
        utils.copy_resources_to_dir()
        return {"FINISHED"}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text='This will overwrite the resource files in the target directory! Additional data, like brush styles, will be kept.', icon='ERROR')
        layout.label(text=str(utils.get_resource_directory()))
class BSBST_OT_open_resource_directory(bpy.types.Operator):
    """
    Open resource directory in system's default file manager.
    """
    bl_idname = "brushstroke_tools.open_resource_directory"
    bl_label = "Open Resource Directory"
    bl_description = "Open directory in system's default file manager"
    bl_options = {"REGISTER"}

    path: bpy.props.StringProperty(default='', subtype='DIR_PATH')

    def execute(self, context):
        utils.open_in_file_manager(utils.get_resource_directory())
        return {"FINISHED"}

class BSBST_UL_brush_styles(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        resource_dir = utils.get_resource_directory()
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            main_split = layout.split(factor=0.5)

            row = main_split.row()
            split = row.split()
            if not item.filepath:
                split.label(text=item.name, icon='FILE_BLEND')
            else:
                split.label(text=item.name, icon='BRUSHES_ALL')

            split = split.split()
            split.label(text=item.category)
            split.label(text=item.type)

            row = main_split.row()
            row.active = False
            row.label(text=item.filepath.replace(str(resource_dir), '{LIB}'), icon='FILE_FOLDER')
        elif self.layout_type == 'GRID':
            layout.label(text=item.name)

    def draw_filter(self, context, layout):
        return

class BSBST_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    resource_path: bpy.props.StringProperty(name='Resource Directory', subtype='DIR_PATH', update=update_resource_path)
    import_relative_path: bpy.props.BoolProperty(name='Relative Path', default=True)
    import_method: bpy.props.EnumProperty(name='Import Method', default='APPEND',
                                       items= [('APPEND', 'Append', 'Append data-blocks and pack image data as local to this file.', 'APPEND_BLEND', 0),\
                                               ('LINK', 'Link', 'Link data-blocks from resource directory.', 'LINK_BLEND', 1),
                                               ])
    brush_styles: bpy.props.CollectionProperty(type=utils.BSBST_brush_style)
    active_brush_style_index: bpy.props.IntProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text='Brushstrokes Library', icon='ASSET_MANAGER')
        layout.prop(self, 'import_method')
        if self.import_method == 'LINK':
            layout.prop(self, 'import_relative_path')
        row = layout.row()
        col = row.column()
        dir_exists = os.path.isdir(utils.get_resource_directory())
        resources_available = utils.check_resources_valid()
        if not dir_exists or not resources_available:
            col.alert = True
        col.prop(self, 'resource_path', placeholder=str(utils.get_resource_directory()))
        op = col.operator('brushstroke_tools.open_resource_directory', icon='ASSET_MANAGER')
        
        split = layout.split(factor=0.25)
        split.column()
        col = split.column()
        if not dir_exists:
            col.alert = True
            row = col.row()
            row.label(text='The selected directory does not exist.', icon='ERROR')
        elif not resources_available:
            col.alert = True
            split = col.split(factor=0.75)
            split.label(text='The required resources were not found at the specified directory.', icon='ERROR')
            op = split.operator('brushstroke_tools.copy_resources', icon='IMPORT')
            op.update = False
        elif self.resource_path:
            lib_version = utils.read_lib_version()
            version_comp = utils.compare_versions(lib_version, utils.addon_version)
            if bool(version_comp):
                col.label(text=f"Version mismatch: Local Data ({'.'.join([str(i) for i in lib_version])}) {'>' if version_comp>0 else '<'} Addon ({'.'.join([str(i) for i in utils.addon_version])})", icon='ERROR')
                if abs(version_comp) in [1, 2, 3]:
                    split = col.split(factor=0.75)
                    if version_comp>0:
                        split.label(text="Consider upgrading the addon and re-copying the data.")
                    else:
                        split.label(text="Consider re-copying the data.")
                    op = split.operator('brushstroke_tools.copy_resources', icon='IMPORT')
                    op.update = False

        if self.import_method == 'LINK' and not self.resource_path:
            col.label(text='Linking the resources from the default addon directory is not recommended.', icon='ERROR')
        
        style_box = layout.box()
        style_box_header = style_box.row(align=True)
        count_local = len([bs for bs in self.brush_styles if not  bs.filepath])
        if count_local:
            count_info = f'Brush Styles ({len(self.brush_styles)-count_local} loaded, {count_local} local)'
        else:
            count_info = f'Brush Styles ({len(self.brush_styles)} loaded)'
        style_box_header.label(text=count_info, icon='BRUSHES_ALL')
        style_box_header.operator('brushstroke_tools.install_brush_style_pack')
        style_box_header.operator('brushstroke_tools.refresh_styles', text='', icon='FILE_REFRESH')
        if not self.brush_styles:
            style_box.label(text='No Brush styles found in library directory', icon='ERROR')
        else:
            row = style_box.row(align=True)
            row.active = False
            main_split = style_box.split()
            row = main_split.row()
            split = row.split()
            split.label(text='Name')
            split = split.split()
            split.label(text='Category')
            split.label(text='Type')
            main_split.label(text='Filepath')
            style_box.template_list('BSBST_UL_brush_styles', "", self, "brush_styles",
                             self, "active_brush_style_index", rows=3, maxrows=5, sort_lock=True)



classes = [
    BSBST_UL_brush_styles,
    BSBST_preferences,
    BSBST_OT_copy_resources_to_path,
    BSBST_OT_refresh_brushstroke_styles,
    BSBST_OT_install_brush_style_pack,
    BSBST_OT_open_resource_directory,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.app.handlers.load_post.remove(load_handler)