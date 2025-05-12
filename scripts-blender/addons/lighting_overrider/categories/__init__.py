from . import (
    variable_settings,
    motion_blur_settings,
    shader_settings,
    rig_settings,
    rna_overrides,
)

modules = [
    variable_settings,
    motion_blur_settings,
    shader_settings,
    rig_settings,
    rna_overrides,
]

def register():
    for m in modules:
        m.register()

def unregister():
    for m in modules:
        m.unregister()