import importlib

from . import ui, ops, props, prefs

bl_info = {
    "name": "Asset Pipeline",
    "author": "Nick Alberelli",
    "description": "Blender Studio Asset Pipeline Add-on",
    "blender": (4, 0, 0),
    "version": (0, 2, 1),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}


def reload() -> None:
    global ui
    global ops
    global props
    global prefs
    importlib.reload(ui)
    importlib.reload(ops)
    importlib.reload(props)
    importlib.reload(prefs)


_need_reload = "ui" in locals()
if _need_reload:
    reload()

# ----------------REGISTER--------------.


def register() -> None:
    ui.register()
    ops.register()
    props.register()
    prefs.register()


def unregister() -> None:
    ui.unregister()
    ops.unregister()
    props.unregister()
    prefs.unregister()
