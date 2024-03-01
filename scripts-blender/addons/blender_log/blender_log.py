from bpy.types import PropertyGroup, Panel, UIList, Operator, Object
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
)

import bpy, json

from .util import draw_label_with_linebreak, get_pretty_stack, get_addon_prefs


class BlenderLog_Entry(PropertyGroup):
    """Container for storing information about a single metarig warning/error.

    A CollectionProperty of CloudRigLogEntries are added to the armature datablock
    in cloud_generator.register().

    This CollectionProperty is then populated by a BlenderLog_Manager instance created by
    CloudRig_Generator, which is created by the Generate operator.
    """

    name: StringProperty(name="Name", description="Name of issue", default="")
    category: StringProperty(
        name="Category", description="For internal categorization of log entries", default=""
    )

    icon: StringProperty(name="Icon", description="Icon for this log entry", default='ERROR')
    description: StringProperty(name="Description", description="Description of issue", default="")

    pretty_stack: StringProperty(
        name="Pretty Stack",
        description="Stack trace in the code of where this log entry was added. For internal use only",
    )

    operator: StringProperty(
        name="Operator", description="Operator that can fix the issue", default=''
    )
    op_kwargs: StringProperty(
        name="Operator Arguments",
        description="Keyword arguments that will be passed to the operator. This should be a string that can be eval()'d into a python dict",
        default='',
    )
    op_text: StringProperty(
        name="Operator Text",
        description="Text to display on the operator button",
        default='',
    )
    op_icon: StringProperty(
        name="Operator Icon",
        description="Icon to display on the operator button",
        default='',
    )


class BlenderLog_Category(PropertyGroup):
    name: StringProperty()
    icon: StringProperty()
    active_log_index: IntProperty()
    logs: CollectionProperty(type=BlenderLog_Entry)

    @property
    def active_log(self):
        if self.active_log_index > len(self.logs) - 1:
            return
        return self.logs[self.active_log_index]

    def get_index(self, log):
        for i, l in enumerate(self.logs):
            if l == log:
                return i

    def clear(self):
        self.logs.clear()
        self.active_log_index = 0


class BlenderLog_Manager(PropertyGroup):
    """Class to manage BlenderLog_Entry CollectionProperty on metarigs.

    This class is instanced once per rig generation, by the CloudRig_Generator class.
    """

    categories: CollectionProperty(type=BlenderLog_Category)
    active_cat_index: IntProperty()

    @property
    def active_category(self):
        if self.active_cat_index > len(self.categories) - 1:
            return
        return self.categories[self.active_cat_index]

    @property
    def active_log(self):
        return self.active_category.active_log

    @property
    def all_logs(self):
        for cat in self.categories:
            for log in cat.logs:
                yield log

    def add(
        self,
        name: str,
        *,
        description="No description.",
        icon='ERROR',
        category="Uncategorized",
        category_icon="",
        operator='',
        op_kwargs={},
        op_text="",
        op_icon="",
    ):
        """Low-level function to add a log entry to the metarig object's data."""
        cat_entry = self.categories.get(category)
        if not cat_entry:
            cat_entry = self.categories.add()
            cat_entry.name = category
            cat_entry.icon = category_icon or icon

        entry = cat_entry.logs.add()
        entry.pretty_stack = get_pretty_stack()

        entry.name = name
        entry.description = description
        entry.category = category
        entry.icon = icon

        entry.operator = operator
        entry.op_kwargs = json.dumps(op_kwargs)
        entry.op_text = op_text
        entry.op_icon = op_icon

        return entry

    def remove(self, log):
        removed = False
        for cat in self.categories:
            for other_log in cat.logs:
                if log == other_log:
                    cat.logs.remove(cat.get_index(log))
                    removed = True
                    break
            if removed:
                break
        if removed and len(cat.logs) == 0:
            self.clear_category(cat.name)

    def remove_active(self):
        self.remove(self.active_log)

    def remove_category(self, cat):
        self.categories.remove(self.get_index(cat))

    def get_category(self, cat_name: str):
        for cat in self.categories:
            if cat.name == cat_name:
                return cat

    def get_index(self, cat):
        for i, c in enumerate(self.categories):
            if c == cat:
                return i

    def clear_category(self, cat_name: str):
        cat = self.get_category(cat_name)
        if cat:
            cat.clear()
            self.categories.remove(self.get_index(cat))


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


class BLENLOG_MT_log_checks(bpy.types.Menu):
    bl_label = "Global Checks"
    bl_idname = 'BLENLOG_MT_log_checks'

    def draw(self, context):
        layout = self.layout
        layout.operator(
            'scene.report_collections_with_fake_user',
            text="Report Fake User Collections",
            icon='FAKE_USER_ON',
        )
        layout.operator(
            'scene.report_obdata_name_mismatch',
            text="Report Mis-Named Object Data",
            icon='FILE_TEXT',
        )
        layout.operator(
            'scene.report_leftover_drivers',
            text="Report Leftover Drivers",
            icon='DRIVER_TRANSFORM',
        )


class BLENLOG_OT_quick_fix_category(bpy.types.Operator):
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


class BLENLOG_OT_remove_category(bpy.types.Operator):
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


class BLENLOG_PT_log_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender Log'
    bl_label = "Blender Log"

    def draw(self, context):
        metarig = context.object
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

        def get_sidebar_size(context):
            for region in context.area.regions:
                if region.type == 'UI':
                    return region.width

        draw_label_with_linebreak(layout, log.description, area_width=get_sidebar_size(context))

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
            kwargs = json.loads(log.op_kwargs)
            for key in kwargs.keys():
                setattr(op, key, kwargs[key])


def change_ui_category(category):
    if BLENLOG_PT_log_panel.bl_category != category:
        bpy.utils.unregister_class(BLENLOG_PT_log_panel)
        BLENLOG_PT_log_panel.bl_category = category
        bpy.utils.register_class(BLENLOG_PT_log_panel)


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
        draw_label_with_linebreak(self.layout, generator.active_log.pretty_stack, alert=True)


registry = [
    BlenderLog_Entry,
    BlenderLog_Category,
    BlenderLog_Manager,
    BLENLOG_UL_log_list,
    BLENLOG_UL_cat_list,
    BLENLOG_MT_log_checks,
    BLENLOG_PT_log_panel,
    BLENLOG_OT_quick_fix_category,
    BLENLOG_OT_remove_category,
    # BLENLOG_PT_stack_trace,
]


@bpy.app.handlers.persistent
def update_ui_category(_):
    prefs = get_addon_prefs(bpy.context)
    change_ui_category(prefs.sidebar_panel)


def register():
    bpy.types.Scene.blender_log = PointerProperty(type=BlenderLog_Manager)
    bpy.app.handlers.depsgraph_update_post.append(update_ui_category)


def unregister():
    del bpy.types.Scene.blender_log
    bpy.app.handlers.depsgraph_update_post.remove(update_ui_category)
