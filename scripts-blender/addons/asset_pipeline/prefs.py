import bpy
from . import constants


def get_addon_prefs():
    return bpy.context.preferences.addons[constants.ADDON_NAME].preferences


class ASSET_PIPELINE_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    custom_task_layers_dir: bpy.props.StringProperty(  # type: ignore
        name="Custom Task Layers",
        description="Specify directory to add additonal Task Layer Presets to use as templates when cerating new assets",
        default="",
        subtype="DIR_PATH",
    )

    save_images_path: bpy.props.StringProperty(  # type: ignore
        name="Save Images Path",
        description="Path to save un-saved images to, if left blank images will save in a called 'images' folder relative to the asset",
        default="",
        subtype="DIR_PATH",
    )

    is_advanced_mode: bpy.props.BoolProperty(
        name="Advanced Mode",
        description="Show Advanced Options in Asset Pipeline Panels",
        default=False,
    )

    def draw(self, context):
        self.layout.prop(self, "custom_task_layers_dir")
        self.layout.prop(self, "save_images_path")
        self.layout.prop(self, "is_advanced_mode")


classes = (ASSET_PIPELINE_addon_preferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
