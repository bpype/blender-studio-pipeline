from bpy.types import Panel, UIList, Operator, Menu
import bpy, json
from .util import draw_label_with_linebreak, get_addon_prefs

# TODO: Button to copy log name, or ability to provide an object name and a button to select that object.

class BLENLOG_PT_log_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Log'
    bl_label = "Blender Log"

    def draw(self, context):
        blenlog = context.scene.blender_log
        layout = self.layout

        layout.label(text="Log Categories")
        row = layout.row()
        row.template_list(
            'BLENLOG_UL_cat_list',
            '',
            blenlog,
            'categories',
            blenlog,
            'active_cat_index',
        )
        ops_col = row.column()

        ops_col.menu(BLENLOG_MT_log_checks.bl_idname, text="", icon='VIEWZOOM')

        cat = blenlog.active_category
        if not cat:
            return

        ops_col.operator(BLENLOG_OT_remove_category.bl_idname, text="", icon='REMOVE')

        layout.operator(BLENLOG_OT_quick_fix_category.bl_idname, icon='AUTO')

        layout.separator()

        layout.label(text="Entries of Category: " + cat.name)
        row = layout.row()
        row.template_list(
            'BLENLOG_UL_log_list',
            '',
            cat,
            'logs',
            cat,
            'active_log_index',
        )

        log = cat.active_log
        if not log:
            return

        layout.use_property_split = False

        draw_label_with_linebreak(context, layout, log.description)

        if log.operator != '':
            row = layout.row()
            split = row.split(factor=0.2)
            split.label(text="Quick Fix:")
            kwargs = {}
            if log.op_text:
                kwargs['text'] = log.op_text
            if log.op_icon:
                kwargs['icon'] = log.op_icon
            op = split.operator(log.operator, **kwargs)
            if op:
                kwargs = json.loads(log.op_kwargs)
                for key in kwargs.keys():
                    setattr(op, key, kwargs[key])
            else:
                row = split.row()
                row.alert = True
                row.label(text="Missing operator: " + log.operator)


class BLENLOG_PT_stack_trace(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = 'BLENLOG_PT_log_panel'
    bl_label = "Python Stack Trace"
    bl_options = {'DEFAULT_CLOSED'}

    # @classmethod
    # def poll(cls, context):
    #     prefs = get_addon_prefs(context)
    #     generator = context.object.cloudrig.generator
    #     if not generator.active_log:
    #         return False
    #     display_mode = generator.active_log.display_stack_trace
    #     return display_mode == 'ALWAYS' or (
    #         display_mode == 'ADVANCED' and is_advanced_mode(context)
    #     )

    def draw(self, context):
        generator = context.object.cloudrig.generator
        draw_label_with_linebreak(
            context, self.layout, generator.active_log.pretty_stack, alert=True
        )


class BLENLOG_UL_log_list(UIList):
    """UI code for list of BlenderLog_Entries."""

    def draw_item(self, _context, layout, _data, item, _icon_value, _active_data, _active_propname):
        log = item
        row = layout.row()
        if log.icon:
            row.label(text=log.name, icon=log.icon)
        else:
            row.label(text=log.name)


class BLENLOG_UL_cat_list(UIList):
    """UI code for list of BlenderLog_Categories."""

    def draw_item(self, _context, layout, _data, item, _icon_value, _active_data, _active_propname):
        cat = item
        row = layout.row()
        row.label(text=f"{cat.name} ({len(cat.logs)})", icon=cat.icon)


class BLENLOG_MT_log_checks(Menu):
    bl_label = "Global Checks"
    bl_idname = 'BLENLOG_MT_log_checks'

    def draw(self, context):
        layout = self.layout
        layout.operator(
            'blenlog.report_fake_user_collections',
            text="Report Fake User Collections",
            icon='FAKE_USER_ON',
        )
        layout.operator(
            'blenlog.report_obdata_name_mismatch',
            text="Report Mis-Named Object Data",
            icon='FILE_TEXT',
        )
        layout.operator(
            'blenlog.report_leftover_drivers',
            text="Report Leftover Drivers",
            icon='DRIVER_TRANSFORM',
        )
        layout.operator(
            'blenlog.report_library_overrides',
            text="Report Library Override Issues",
            icon='LIBRARY_DATA_OVERRIDE',
        )


class BLENLOG_OT_quick_fix_category(Operator):
    """Run the automatic fixing operator for each entry in this category that has one"""

    bl_idname = "blenlog.fix_category"
    bl_label = "Quick-Fix Issues"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active_cat = context.scene.blender_log.active_category
        return any([log.operator for log in active_cat.logs])

    def execute(self, context):
        active_cat = context.scene.blender_log.active_category

        for i, log in reversed(list(enumerate(active_cat.logs))):
            active_cat.active_log_index = i
            op_idname = log.operator
            if not op_idname:
                continue
            op_kwargs = json.loads(log.op_kwargs)
            op_category, op_name = op_idname.split(".")
            op_callable = getattr(getattr(bpy.ops, op_category), op_name)
            op_callable(**op_kwargs)

        return {'FINISHED'}


class BLENLOG_OT_remove_category(Operator):
    """Remove active log category"""

    bl_idname = "blenlog.remove_category"
    bl_label = "Remove Category"
    bl_options = {'INTERNAL', 'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.blender_log.active_category

    def execute(self, context):
        context.scene.blender_log.remove_category(context.scene.blender_log.active_category)
        return {'FINISHED'}


registry = [
    BLENLOG_UL_log_list,
    BLENLOG_UL_cat_list,
    BLENLOG_MT_log_checks,
    BLENLOG_PT_log_panel,
    BLENLOG_OT_quick_fix_category,
    BLENLOG_OT_remove_category,
]


@bpy.app.handlers.persistent
def update_ui_category(_):
    prefs = get_addon_prefs(bpy.context)
    change_ui_category(prefs.sidebar_panel)


def change_ui_category(category):
    if BLENLOG_PT_log_panel.bl_category != category:
        bpy.utils.unregister_class(BLENLOG_PT_log_panel)
        BLENLOG_PT_log_panel.bl_category = category
        bpy.utils.register_class(BLENLOG_PT_log_panel)


def register():
    bpy.app.handlers.depsgraph_update_post.append(update_ui_category)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(update_ui_category)
