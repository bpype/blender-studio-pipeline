# Blender Log

This add-on lets other add-ons report issues to the user in a persistent location in Blender's UI. 
Add-ons can add issues to a list of lists, providing detailed information about the issue, or even a button to fix it outright.
No add-on should vitally rely on this one! Implement fallbacks for error reporting in case this add-on is not installed by the user.

This add-on also aims to be an inspiration for this kind of functionality being built into Blender itself; For example, to report dependency cycles, modifier errors, driver errors, without spamming the terminal window. The Info Editor seems like the perfect place for this sort of functionality.

## Installation
Find installation instructions [here](https://studio.blender.org/tools/addons/overview).

# Example use cases:

### 1. Mesh Editing add-on wants to warn you about non-manifold geometry:
- An operation in a mesh editing add-on reports a warning about your mesh having non-manifold geometry
- It creates an entry in the Blender Log UI, explaining what non-manifold geometry is and why it could be a problem.
- It provides you with a button that will select that concerning geometry for you, so you can fix it.
- If you think you've fixed the issue, you can remove the report.
- If the report comes back the next time you use the operator, your fix didn't work.
- If you use the same operator multiple times, the report should not be duplicated. (Subject to the reporting add-on's implementation)

### 2. Convention checker:
- In your pipeline add-on, you can implement a button that checks if object names adhere to your desired naming conventions.
- If not, you can create an entry in the Blender Log UI for each offending object name, rather than just printing to the terminal.
- You can even provide the user with a Rename button so they don't have to find each object by hand.
- You can also choose to throw an error and interrupt your operation if you think it's a severe enough issue.


# How to use as a Python Developer
In order to develop an add-on that can make use of this add-on when it is present, without erroring otherwise, and without cluttering your code too much, I suggest adding the following code to your add-on:

```python

import addon_utils

# These are the only two functions where you need to check if the Blender Log add-on is present.

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
            op_icon=op_icon
        )
    else:
        # This is what happens when Blender Log is not installed by your user. 
        # You can implement a fallback error handling here!
        raise Exception(name + " " + description)
```

Then, let's say your add-on is an importer for an imaginary .b3d file format. You can report issues you detect during your import process like this:

```python
def check_imported_objects(context, my_objects: List[bpy.types.Object]):
    issue_category = 'B3D Import Issues'

    # Clear any previous issues of this type from the log, to avoid duplicate reports.
    clear_log_category(context, issue_category)

    for obj in my_objects:
        if obj.type == 'MESH' and len(obj.data.vertices) == 0:
            report_issue(context,
                name = obj.name,                # Everything beside this is optional.
                description = "Mesh object imported with no geometry. Might as well delete it.",
                icon = 'MESH_CIRCLE',
                category = issue_category,      # If not provided, will default to "Uncategorized".
                category_icon = 'MESH_DATA'     # Only first entry of a category will set the category's icon.
                operator = 'object.my_delete_operator',
                op_kwargs = {'ob_name' : obj.name},
                op_text = "Delete " + obj.name,
                op_icon = 'TRASH'
            )
```

Here I also implied that you might've implemented your own object deletion operator, since Blender doesn't provide one that you can pass an object name to; It always uses the active object, which isn't suitable for this scenario. Besides, your operator should probably also get rid of the corresponding issue entry, which you can do as easily as `context.scene.blender_log.remove_active()`.
