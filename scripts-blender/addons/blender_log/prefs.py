import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty
from .ui import change_ui_category
from .util import get_addon_prefs


class BlenLog_Prefs(AddonPreferences):
    bl_idname = __package__

    def update_sidebar_panel(self, context):
        change_ui_category(self.sidebar_panel)

    sidebar_panel: StringProperty(
        name="Sidebar Panel",
        description="Define which sidebar panel the Blender Log should appear in",
        default="Blender Log",
        update=update_sidebar_panel,
    )
    purge_on_save: BoolProperty(
        name="Purge On Save",
        description="Run a recursive purge on file save, rather than simply not saving unused datablocks, which is Blender's default behaviour. This ensures your file is never saved with any garbage orphan data",
        default=True,
    )

    display_stack_trace: BoolProperty(
        name="Display Stack Trace",
        description="Whether to display the Python Stack Trace of a log entry. Only useful for Python developers",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout = layout.column(align=True)
        layout.prop(self, 'sidebar_panel')
        layout.prop(self, 'purge_on_save')

        layout.separator()
        layout.prop(self, 'display_stack_trace')


registry = [BlenLog_Prefs]


@bpy.app.handlers.persistent
def delayed_register(_):
    prefs = get_addon_prefs(bpy.context)
    prefs.sidebar_panel = prefs.sidebar_panel


def register():
    bpy.app.handlers.load_post.append(delayed_register)


def unregister():
    bpy.app.handlers.load_post.remove(delayed_register)
