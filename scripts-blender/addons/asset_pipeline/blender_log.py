import sys

import addon_utils
import bpy

from .logging import get_logger

# Integration with the Blender Log add-on.


def __get_blenlog_module_name() -> str:
    return next((m for m in sys.modules if m.endswith('.blender_log')), None)


def clear_log_category(context, category: str):
    """Clear a category of issues, to avoid duplicating issues when checking for them multiple times."""
    blenlog_module_name = __get_blenlog_module_name()
    log_enabled = addon_utils.check(blenlog_module_name)[1]
    if log_enabled:
        context.scene.blender_log.clear_category(category)


def add_log(
    name: str,
    *,
    context=None,
    description="",
    icon="",
    category="Uncategorized",
    operator="",
    op_kwargs={},
    op_text="",
    op_icon="",
    log_level="DEBUG",
):
    """The parameters of this function should mirror `BlenderLog_Manager.add()`.
    This function is just a wrapper around that,
    to avoid errors in case Blender Log is not installed.
    """
    if not context:
        context = bpy.context
    log_enabled = addon_utils.check(context, 'blender_log')[1]
    if log_enabled:
        context.scene.blender_log.add(
            name=name,
            description=description,
            icon=icon,
            category=category,
            operator=operator,
            op_kwargs=op_kwargs,
            op_text=op_text,
            op_icon=op_icon,
        )
    else:
        # This is what happens when Blender Log is not installed by your user.
        # You can implement a fallback error handling here!
        logger = get_logger()
        msg = name + ": " + description
        {
            'DEBUG': logger.debug,
            'ERROR': logger.error,
            'WARNING': logger.warning,
            'INFO': logger.info,
            'CRITICAL': logger.critical,
            'FATAL': logger.fatal,
        }[log_level](msg)
