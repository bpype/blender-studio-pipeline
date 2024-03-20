import bpy
from . import constants
from .logging import get_logger

def get_addon_prefs():
    return bpy.context.preferences.addons[constants.ADDON_NAME].preferences


def project_root_dir_get():
    prefs = get_addon_prefs()
    return prefs.project_root_dir


class ASSET_PIPELINE_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    project_root_dir: bpy.props.StringProperty(  # type: ignore
        name="Project Root Directory",
        description="Root Directory of the Project, this should be the root directory `your_project_name/ that contains the SVN, Shared and Local folders`",
        default="/data/gold/",
        subtype="DIR_PATH",
    )

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

    def update_logger_level(self, context):
        logger = get_logger()
        logger.handlers.clear()

    logger_level: bpy.props.EnumProperty(  # type: ignore
        name="Logging Level",
        description="Changes the level of detail of print statements in blender's console",
        default=1,
        items=constants.LOGGER_LEVEL_ITEMS,
        update=update_logger_level,
    )

    is_advanced_mode: bpy.props.BoolProperty(  # type: ignore
        name="Advanced Mode",
        description="Show Advanced Options in Asset Pipeline Panels",
        default=False,
    )

    preserve_action: bpy.props.BoolProperty(  # type: ignore
        name="Preserve Actions in Workfiles",
        description="Preserve Action Data-Blocks on Armatures in working files during Pull (this data will not be pushed to Sync Target)",
        default=False,
    )

    preserve_indexes: bpy.props.BoolProperty(  # type: ignore
        name="Preserve Active Indexes in Workfiles",
        description=(
            "Preserve Active Indexes (Vertex Groups, Shape Keys, UV Maps, Color Attributes, Attributes) "
            "in working files during Pull (this data will not be pushed to Sync Target)"
        ),
        default=False,
    )

    def draw(self, context):
        self.layout.prop(self, "project_root_dir")
        self.layout.prop(self, "custom_task_layers_dir")
        self.layout.prop(self, "save_images_path")
        self.layout.prop(self, "logger_level")
        self.layout.prop(self, "preserve_action")
        self.layout.prop(self, "preserve_indexes")
        self.layout.prop(self, "is_advanced_mode")


classes = (ASSET_PIPELINE_addon_preferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
