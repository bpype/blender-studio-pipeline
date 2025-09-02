import bpy
from .hooks import hook

'''
Rules:
    merge_mode: ['pull', 'push'] # Run hook only during pull or push (both if left blank)
    merge_status: ['pre', 'post'] # Run hook either before or after push/pull (both if left blank)

Keyword Arguments:
    asset_col: bpy.types.Collection # Get the top level collection for the current asset
    
Notes:
    Function Naming: Must be unique between production hooks and asset hooks files
    Production Hook Path: 'your_project_name/svn/pro/assets/scripts/asset_pipeline/hooks.py'
    Asset Hook Path: 'your_project_name/svn/pro/assets/{asset_type}/{asset_name}/hooks.py'
'''


@hook(merge_mode='pull', merge_status="pre")
def asset_pre_pull(asset_col: bpy.types.Collection, **kwargs):
    # Only runs before pull
    print(f"Asset Collection Name '{asset_col.name}'")
    print("PRE PULL asset hook running!")


@hook(merge_mode='pull', merge_status="post")
def asset_post_pull(**kwargs):
    # Only runs after pull
    print("POST PULL asset hook running!")


@hook(merge_mode='push', merge_status="pre")
def asset_pre_push(**kwargs):
    # Only runs before push
    print("PRE PUSH asset hook running!")


@hook(merge_mode='push', merge_status="post")
def asset_post_push(**kwargs):
    # Only runs after push
    print("POST PUSH asset hook running!")
