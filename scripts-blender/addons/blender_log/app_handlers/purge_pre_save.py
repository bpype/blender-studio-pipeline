import bpy
from bpy.app.handlers import persistent
from ..util import get_addon_prefs


@persistent
def purge_before_save(scene):
    prefs = get_addon_prefs()
    if prefs.purge_on_save:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)


def register():
    bpy.app.handlers.save_pre.append(purge_before_save)


def unregister():
    bpy.app.handlers.save_pre.remove(purge_before_save)
