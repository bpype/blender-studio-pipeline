
import bpy
from .categories import rig_settings, shader_settings, rna_overrides
from .categories import variable_settings as var_settings


class LOR_SettingsGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    text_datablock: bpy.props.PointerProperty(
        type = bpy.types.Text,
        name = "Settings JSON",
        description = "Text datablock that contains the full settings information"
    )
    is_dirty: bpy.props.BoolProperty(default=False)

    variable_settings: bpy.props.CollectionProperty(type=var_settings.LOR_variable_setting)
    variable_settings_index: bpy.props.IntProperty()
    motion_blur_settings: bpy.props.CollectionProperty(type=var_settings.LOR_variable_setting)
    motion_blur_settings_index: bpy.props.IntProperty()
    shader_settings: bpy.props.CollectionProperty(type=shader_settings.LOR_shader_setting)
    shader_settings_index: bpy.props.IntProperty()
    rig_settings: bpy.props.CollectionProperty(type=rig_settings.LOR_rig_setting)
    rig_settings_index: bpy.props.IntProperty()
    rna_overrides: bpy.props.CollectionProperty(type=rna_overrides.LOR_rna_override)
    rna_overrides_index: bpy.props.IntProperty()

class LOR_MetaSettings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(default=False)
    shot_settings: bpy.props.PointerProperty(type=LOR_SettingsGroup)
    sequence_settings: bpy.props.PointerProperty(type=LOR_SettingsGroup)
    settings_toggle: bpy.props.EnumProperty(default='SHOT',
        items= [('SEQUENCE', 'Sequence Settings', 'Manage override settings for the current sequence', '', 0),
                ('SHOT', 'Shot Settings', 'Manage override settings for the current shot', '', 1),]
    )
    execution_script: bpy.props.PointerProperty(
        type = bpy.types.Text,
        name = "Execution Script",
        description = "Text datablock with script that automatically applies the saved settings on file-load"
    )
    execution_script_source: bpy.props.StringProperty(default='//../../../lib/scripts/load_settings.blend')#TODO expose in addon settings


classes = [
    LOR_SettingsGroup,
    LOR_MetaSettings,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.LOR_Settings = bpy.props.PointerProperty(type=LOR_MetaSettings)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.LOR_Settings
