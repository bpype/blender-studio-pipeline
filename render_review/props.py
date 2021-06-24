from pathlib import Path

import bpy

from render_review.log import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)


class RR_property_group_scene(bpy.types.PropertyGroup):
    """"""

    def _get_shot_name_from_render_dir(self):
        if not self.is_render_dir_valid:
            return ""
        return self.render_dir_path.stem  # 060_0010_A.lighting > 060_0010_A

    render_dir: bpy.props.StringProperty(name="Render Directory", subtype="DIR_PATH")
    shot_name: bpy.props.StringProperty(
        name="Shot Name", get=_get_shot_name_from_render_dir
    )

    @property
    def render_dir_path(self):
        if not self.is_render_dir_valid:
            return None
        return Path(bpy.path.abspath(self.render_dir)).absolute()

    @property
    def is_render_dir_valid(self) -> bool:
        if not self.render_dir:
            return False

        if not bpy.data.filepath and self.render_dir.startswith("//"):
            return False

        return True


# ----------------REGISTER--------------

classes = [
    RR_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties
    bpy.types.Scene.rr = bpy.props.PointerProperty(
        name="Render Review",
        type=RR_property_group_scene,
        description="Metadata that is required for render_review",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
