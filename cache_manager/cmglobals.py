from typing import List

MODIFIER_NAME = "cm_cache"

CONSTRAINT_NAME = "cm_cache"

VALID_OBJECT_TYPES = {"MESH", "CAMERA"}

_VERSION_PATTERN = "v\d\d\d"

MODIFIERS_KEEP: List[str] = [
    "SUBSURF",
    "PARTICLE_SYSTEM",
    "MESH_SEQUENCE_CACHE",
    "DATA_TRANSFER",
    "NORMAL_EDIT",
]

DRIVER_VIS_DATA_PATHS: List[str] = [
    "hide_viewport",
    "hide_render",
    "show_viewport",
    "show_render",
]

CAM_DATA_PATHS: List[str] = [
    "angle",
    "angle_x",
    "angle_y",
    "clip_end",
    "clip_start",
    "display_size",
    "dof.aperture_blades",
    "dof.aperture_fstop",
    "dof.aperture_ratio",
    "dof.aperture_rotation",
    "lens",
    "lens_unit",
    "ortho_scale",
    "sensor_fit",
    "sensor_height",
    "sensor_width",
    "shift_x",
    "shift_y",
]
