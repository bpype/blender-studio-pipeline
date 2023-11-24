import bpy
import contextlib

from typing import Optional


def get_visibility_driver(obj) -> Optional[bpy.types.FCurve]:
    obj = bpy.data.objects.get(obj.name)
    assert obj, "Object was renamed while its visibility was being ensured?"
    if hasattr(obj, "animation_data") and obj.animation_data:
        return obj.animation_data.drivers.find("hide_viewport")


@contextlib.contextmanager
def override_obj_visability(obj: bpy.types.Object, scene: bpy.types.Scene):
    """Temporarily Change the Visability of an Object so an bpy.ops or other
    function that requires the object to be visable can be called.

    Args:
        obj (bpy.types.Object): Object to un-hide
        scene (bpy.types.Scene): Scene Object is in
    """
    hide = obj.hide_get()  # eye icon
    hide_viewport = obj.hide_viewport  # hide viewport
    select = obj.hide_select  # selectable

    driver = get_visibility_driver(obj)
    if driver:
        driver_mute = driver.mute

    try:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_select = False
        if driver:
            driver.mute = True

        assigned_to_scene_root = False
        if obj.name not in scene.collection.objects:
            assigned_to_scene_root = True
            scene.collection.objects.link(obj)

        yield

    finally:
        obj.hide_set(hide)
        obj.hide_viewport = hide_viewport
        obj.hide_select = select
        if driver:
            driver.mute = driver_mute

        if assigned_to_scene_root and obj.name in scene.collection.objects:
            scene.collection.objects.unlink(obj)
