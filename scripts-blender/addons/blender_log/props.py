from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)

import bpy, json

from .util import get_pretty_stack


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


registry = [
    BlenderLog_Entry,
    BlenderLog_Category,
    BlenderLog_Manager,
]


def register():
    bpy.types.Scene.blender_log = PointerProperty(type=BlenderLog_Manager)


def unregister():
    del bpy.types.Scene.blender_log
