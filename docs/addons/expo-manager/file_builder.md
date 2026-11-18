# File Builder

![Top Menu Bar](/media/addons/expo_manager/expo_topmenu_bar.jpg)

To create a new file for a Shot, Asset, Sequence, or Edit, use the `Expo > New {Entity}` menu in Blender's top bar.

Each entity's [file patterns](configuration.md#file-patterns) determine its working file's `dir` and `file`. The `[naming]` settings `delimiter` and `space_replacer` control the corresponding pattern tokens and how spaces in entity names are replaced; see [Naming](configuration.md#naming).

## Shot Building

For a step-by-step guide to building and using Shots in your production, see [Project Workflow](/pipeline/workflow.md).
- **Templates:** To define a custom template for each Shot Task Type, place a `.blend` file in the `templates_dir` defined in the [project configuration](configuration.md). File names must match the full Task Type name on Kitsu (not its short name or code), e.g. `Animation.blend`.
- **Hooks:** Add production-specific behavior to new Shot files. The hook file path is defined by `hooks_file` in your [project configuration](configuration.md).
- **Casting:** Casting associates a Kitsu Asset entity with a Shot so the Shot Builder knows which Assets to link. See the [Kitsu Breakdown](https://kitsu.cg-wire.com/guides/production/breakdown-casting/) guide for how to cast Assets to Shots.
- **Editorial import:** When enabled for a Task Type, the latest [editorial Publish](edit.md#export--publish) is loaded into the sequence editor and synchronized to the current Shot. You can later update it using the [`Import Latest Edit Export`](shot.md#editorial-reference) operator.

Expo opens the matching template as a Blender home file before building the new file, rather than loading only its workspaces. Expo Manager also includes some basic templates. If no matching template is found, Blender's standard home file is used.

Create a Python file at the `hooks_file` path in your project configuration. Hooks run during shot building and can customize the scene using the shot task, project root, and destination file path. For example, a production could use a hook to adjust settings for animation shots.

Hooks can apply to one Task Type, a list of Task Types, or every Shot Task. They match the Kitsu Task Type's **short name** when one is set, falling back to the full name otherwise. Matching is case-sensitive, so the example below only applies to the Animation Task when its matching name is `Animation`.

The [Shot Builder settings](configuration.md#shot-builder) also control camera setup with `link_camera_rig_task_types` and `camera_name`, action naming with `action_name`, and overrides for cast assets with `asset_type_to_override`. The `hooks_file` and `templates_dir` settings are described under [Shared Paths](configuration.md#shared-paths).

The following settings can be left empty to change optional shot assembly behavior:

- `link_camera_rig_task_types`: An empty list skips camera setup for all Shot Task Types.
- `output_col_create`: An empty mapping skips creating Task output collections; cast Assets are linked to the scene collection instead.
- `output_col_link_mapping`: An empty mapping skips linking output collections from other Task Types.
- `load_editorial_ref`: An empty mapping skips loading editorial references automatically.
- `asset_type_to_override`: An empty mapping links cast Assets without creating library overrides; it does not skip linking the Assets.

```python
import bpy

# The import paths here are relative to the "expo_manager/shot_builder/hooks.py" file.
from .hooks import hook
from ..pipe_manager import Shot


import logging

'''
Arguments to use in hooks
    scene: bpy.types.Scene # current scene
    shot: Shot entity class from pipe_manager
    prod_path: str # path to production root dir (your_project/project_files/)
    shot_path: str # path to shot file (your_project/project_files/pro/shots/{sequence_name}/{shot_name}/{shot_task_name}.blend})

Notes
     matching_task_type = ['anim', 'lighting', 'fx', 'comp'] # either use list or just one string
     output_col_name = shot.get_output_collection_name(task_type_short_name="anim")
'''

logger = logging.getLogger(__name__)


@hook()
def set_eevee_render_engine(scene: bpy.types.Scene, **kwargs):
    """
    By default, we set EEVEE as the renderer.
    """
    scene.render.engine = 'BLENDER_EEVEE'
    print("HOOK SET RENDER ENGINE")


@hook(match_task_type='Animation')
def test_args(
    scene: bpy.types.Scene, shot: Shot, prod_path: str, shot_path: str, **kwargs
):
    """
    Set output parameters for animation rendering
    """
    print(f"Scene = {scene.name}")
    print(f"Shot = {shot.name}")
    print(f"Prod Path = {prod_path}")
    print(f"Shot Path = {shot_path}")
```

## Asset Building
- **Mapping:** Asset files map to the Asset entity on Kitsu, not to a Task Type. Task Types are used only for [publishing](asset.md#publish).
- **Template:** To define one template for all Asset files, place a `.blend` file named `Asset.blend` in the `templates_dir` defined in the [project configuration](configuration.md).
- **Asset collection:** When an Asset file is built, an asset collection is automatically created and [marked as an asset](https://docs.blender.org/manual/en/latest/files/asset_libraries/introduction.html#bpy-ops-asset-mark) in Blender's Asset Browser.

:::info Blender's Asset Library
Manually set the Asset Library path in Blender's preferences to point to your project's assets directory.
:::

## Edit Building
- **Mapping:** Edit files map to an Edit entity on Kitsu, not to a Task Type. Task Types are selected when [publishing](edit.md#export-publish).
- **Template:** To define a template for Edit files, place a file named `Edit.blend` in the `templates_dir` defined in the [project configuration](configuration.md).

## Sequence Building
- **Mapping:** Each sequence file maps to a Sequence and Task Type on Kitsu.
- **Templates:** To define a custom template for each Sequence Task Type, place a `.blend` file in the `templates_dir` defined in the [project configuration](configuration.md). File names must match the full Task Type name on Kitsu (not its short name or code), e.g. `Storyboard.blend`.

The `patterns.Sequence` section determines the sequence file's location; see [Pattern Tokens](configuration.md#pattern-tokens).
