# Convention Checker
Before each publish, you can run a series of convention checks: Python functions that return `True` or `False`. The `convention_required` [project setting](configuration.md#project-settings) controls whether checks must pass before publishing; the `conventions_file` [shared path](configuration.md#shared-paths) identifies the project's checks.


![Convention Panel](/media/addons/expo_manager/conventions_panel.jpg)

### Refresh Convention
Each convention has a refresh icon next to it. If a convention fails a check, it will appear red in your conventions list. Click the "error" icon to show the error message for each convention in the info panel.

### Fix Convention
If a convention check fails and a fix is available, use the wrench icon to run the fix for that convention. The operator then runs the check again; if it passes, the convention returns to its default color.

### Check All
To check all conventions, use this operator. It provides the option to automatically run fixes for any conventions that failed.

![Check All Operator](/media/addons/expo_manager/conventions_operator.jpg)

The operator runs all checks, then runs fixes (if enabled), and re-runs the checks afterward to ensure all of them pass.

![Convention Checker Error Message](/media/addons/expo_manager/conventions_error.jpg)

If any checks still fail after the `Check All` operator runs, the Info panel displays a summary.

## Writing Custom Conventions

Each convention is defined by a function with an `@convention` decorator. If a fix is available, define it with the `@fix_for` decorator.

Each check returns a boolean indicating whether the check passed or failed, as well as a message to show to the user.

See the example below:

```python
import bpy
from bpy_extras import anim_utils

# The import paths here are relative to the "expo_manager/conventions/hooks.py" file.
from .. import pipe_manager
from ..output_col.core import get_asset_collections_from_scene
from .hooks import convention, fix_for

@convention(entity_type="Shot", task_type="Animation", label="Scene FPS Matches Project")
def check_scene_fps(context):
    project = pipe_manager.get_project()

    scene_fps = context.scene.render.fps
    if scene_fps == project.fps:
        return True, f"Scene FPS is {scene_fps}"

    return False, f"Scene FPS is {scene_fps}, expected {project.fps}"


@fix_for(check_scene_fps)
def fix_scene_fps(context):
    project = pipe_manager.get_project()
    context.scene.render.fps = project.fps


@convention(entity_type="Shot", task_type="Animation", label="Action Names Follow Convention")
def check_action_names(context):
    wrong, error = _collect_wrong_action_names(context)
    if error:
        return False, error
    if wrong:
        summary = ", ".join(f"'{a.name}' → '{n}'" for a, n in wrong)
        return False, f"{len(wrong)} action(s) mis-named: {summary}"
    return True, "All action names follow the convention"


@convention(entity_type="Asset", label="Scene Has Camera")
def check_scene_has_camera(context):
    has_camera = any(obj.type == "CAMERA" for obj in context.scene.objects)
    if has_camera:
        return True, "At least one camera exists"
    return False, "No camera object found in this file"

```
