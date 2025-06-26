import bpy

# The import paths here are relative to the "blender_kitsu/shot_builder/hooks.py" file.
# The example imports here imports the "blender_kitsu/shot_builder/hooks.py" and "blender_kistsu/types.py" file.
from .hooks import hook
from ..types import Shot, Asset

import logging

'''
Arguments to use in hooks
    scene: bpy.types.Scene # current scene
    shot: Shot class from blender_kitsu.types.py
    prod_path: str # path to production root dir (your_project/svn/)
    shot_path: str # path to shot file (your_project/svn/pro/shots/{sequence_name}/{shot_name}/{shot_task_name}.blend})
    
Notes
     matching_task_type = ['anim', 'lighting', 'fx', 'comp'] # either use list or just one string
     output_col_name = shot.get_output_collection_name(task_type_short_name="anim")
     



'''

logger = logging.getLogger(__name__)

# ---------- Global Hook ----------


@hook()
def set_eevee_render_engine(scene: bpy.types.Scene, **kwargs):
    """
    By default, we set EEVEE as the renderer.
    """
    scene.render.engine = 'BLENDER_EEVEE'
    print("HOOK SET RENDER ENGINE")


# ---------- Overrides for animation files ----------


@hook(match_task_type='anim')
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
