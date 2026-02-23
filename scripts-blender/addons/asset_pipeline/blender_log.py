import addon_utils

# Integration with the Blender Log add-on.


def clear_log_category(context, category: str):
    """Clear a category of issues, to avoid duplicating issues when checking for them multiple times."""
    log_enabled = addon_utils.check(context, 'blender_log')[1]
    if log_enabled:
        context.scene.blender_log.clear_category(category)


def report_issue(
    context,
    name: str,
    description="",
    icon="",
    category="Uncategorized",
    operator="",
    op_kwargs={},
    op_text="",
    op_icon="",
):
    """The parameters of this function should mirror `BlenderLog_Manager.add()`.
    This function is just a wrapper around that,
    to avoid errors in case Blender Log is not installed.
    """
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
        raise Exception(name + " " + description)
