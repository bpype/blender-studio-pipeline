import bpy, os, sys, traceback, addon_utils
from bpy import types
from bpy.types import Object
from typing import Dict, List, Tuple

# NOTE: This file should not import anything from this add-on!


def get_pretty_stack() -> str:
    """Make a pretty looking string out of the current execution stack,
    or the exception stack if this is called from a stack which is handling an exception.
    (Python is cool in that way - We can tell when this function is being called by
    a stack which originated in a try/except block!)
    """
    ret = ""

    exc_type, exc_value, tb = sys.exc_info()
    if exc_value:
        # If the stack we're currently on is handling an exception,
        # use the stack of that exception instead of our stack
        stack = traceback.extract_tb(exc_value.__traceback__)
    else:
        stack = traceback.extract_stack()

    lines = []
    after_generator = False
    for i, frame in enumerate(stack):
        if 'generator' in frame.filename:
            after_generator = True
        if not after_generator:
            continue
        if frame.name in (
            "log",
            "add_log",
            "log_fatal_error",
            "raise_generation_error",
        ):
            break

        # Shorten the file name; All files are in blender's "scripts" folder, so
        # that part of the path contains no useful information, just clutter.
        short_file = frame.filename
        if 'scripts' in short_file:
            short_file = frame.filename.split("scripts")[1]

        if i > 0 and frame.filename == stack[i - 1].filename:
            short_file = " " * int(len(frame.filename) / 2)

        lines.append(f"{short_file} -> {frame.name} -> line {frame.lineno}")

    ret += f" {chr(8629)}\n".join(lines)
    ret += f":\n          {frame.line}\n"
    if exc_value:
        ret += f"{exc_type.__name__}: {exc_value}"
    return ret


def get_datablock_type_icon(datablock):
    """Return the icon string representing a datablock type"""
    # It's beautiful.
    # There's no proper way to get the icon of a datablock, so we use the
    # RNA definition of the id_type property of the DriverTarget class,
    # which is an enum with a mapping of each datablock type to its icon.
    # TODO: It would unfortunately be nicer to just make my own mapping.
    if not hasattr(datablock, "type"):
        # shape keys...
        return 'NONE'
    typ = datablock.type
    if datablock.type == 'SHADER':
        typ = 'NODETREE'
    return bpy.types.DriverTarget.bl_rna.properties['id_type'].enum_items[typ].icon


def get_sidebar_size(context):
    for region in context.area.regions:
        if region.type == 'UI':
            return region.width


def draw_label_with_linebreak(context, layout, text, alert=False):
    """Attempt to simulate a proper textbox by only displaying as many
    characters in a single label as fits in the UI.
    This only works well on specific UI zoom levels.
    """

    if text == "":
        return
    col = layout.column(align=True)
    col.alert = alert
    paragraphs = text.split("\n")

    # Try to determine maximum allowed characters per line, based on pixel width of the area.
    # Not a great metric, but I couldn't find anything better.

    max_line_length = get_sidebar_size(context) / 8
    for p in paragraphs:
        lines = [""]
        for word in p.split(" "):
            if len(lines[-1]) + len(word) + 1 > max_line_length:
                lines.append("")
            lines[-1] += word + " "

        for line in lines:
            col.label(text=line)
    return col


def get_object_hierarchy_recursive(obj: Object, all_objects=[]):
    if obj not in all_objects:
        all_objects.append(obj)

    for c in obj.children:
        get_object_hierarchy_recursive(c, all_objects)

    return all_objects


def check_addon(context, addon_name: str) -> bool:
    """Same as addon_utils.check() but account for workspace-specific disabling.
    Return whether an addon is enabled in this context.
    """
    addon_enabled_in_userprefs = addon_utils.check(addon_name)[1]
    if addon_enabled_in_userprefs and context.workspace.use_filter_by_owner:
        # Not sure why it's called owner_ids, but it contains a list of enabled addons in this workspace.
        addon_enabled_in_workspace = addon_name in context.workspace.owner_ids
        return addon_enabled_in_workspace

    return addon_enabled_in_userprefs


def get_addon_prefs(context=None):
    if not context:
        context = bpy.context
    return context.preferences.addons[__package__.split(".")[0]].preferences
