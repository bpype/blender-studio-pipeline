from pathlib import Path

import bpy
import pytest

from .install_addons import disable_addon, install_addon


@pytest.fixture(scope='session')
def context_ap():
    context = bpy.context
    install_addon(context, addon_name='asset_pipeline')
    context.preferences.filepaths.save_version = 0
    yield context
    disable_addon('asset_pipeline')


#############################


def load_blend(rel_blend_path: str):
    abs_path = Path(__file__).parent / Path(f"{rel_blend_path}")
    bpy.ops.wm.open_mainfile(filepath=abs_path.as_posix())


def select_obj(context, obj_name=None):
    if obj_name:
        obj = bpy.data.objects[obj_name]
        context.view_layer.objects.active = obj
        obj.hide_set(False)
        obj.select_set(True)
