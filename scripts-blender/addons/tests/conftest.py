from pathlib import Path

import bpy
import pytest

from .install_addons import disable_addon, install_addon


@pytest.fixture(scope='session')
def context_ap():
    context = bpy.context
    install_addon(context, addon_name='asset_pipeline')
    yield context
    disable_addon('asset_pipeline')


#############################


def load_blend(blend_name: str):
    blend_path = Path(__file__).parent / Path(f"{blend_name}")
    bpy.ops.wm.open_mainfile(filepath=blend_path.as_posix())


def select_obj(context, obj_name=None):
    if obj_name:
        obj = bpy.data.objects[obj_name]
        context.view_layer.objects.active = obj
        obj.hide_set(False)
        obj.select_set(True)
