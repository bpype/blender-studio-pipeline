import bpy

from . import types
from . import checkstrip
from . import pull
from . import push
from . import props
from . import prefs
from . import opsdata
from . import ops
from . import ui
from . import util
from .logger import ZLoggerFactory, ZLoggerLevelManager

logger = ZLoggerFactory.getLogger(__name__)

bl_info = {
    "name": "Blezou",
    "author": "Paul Golter",
    "description": "Blender addon to interact with gazou data base",
    "blender": (2, 93, 0),
    "version": (0, 1, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Generic",
}

_need_reload = "ops" in locals()

if _need_reload:
    import importlib

    logger.info("-START- Reloading Blezou")
    types = importlib.reload(types)
    checkstrip = importlib.reload(checkstrip)
    pull = importlib.reload(pull)
    push = importlib.reload(push)
    props = importlib.reload(props)
    prefs = importlib.reload(prefs)
    opsdata = importlib.reload(opsdata)
    ops = importlib.reload(ops)
    ui = importlib.reload(ui)
    util = importlib.reload(util)
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Reloading Blezou")


def register():
    logger.info("-START- Registering Blezou")
    props.register()
    prefs.register()
    ops.register()
    ui.register()
    ZLoggerLevelManager.configure_levels()
    logger.info("-END- Registering Blezou")


def unregister():
    logger.info("-START- Unregistering Blezou")
    ui.unregister()
    ops.unregister()
    prefs.unregister()
    props.unregister()
    ZLoggerLevelManager.restore_levels()
    logger.info("-END- Unregistering Blezou")


if __name__ == "__main__":
    register()
