import bpy
from pathlib import Path


def is_edit_file():
    return bpy.context.scene.kitsu.category == "EDIT"


# Category values are defined in enum props.py KITSU_property_group_scene under category
def is_sequence_context():
    return bpy.context.scene.kitsu.category == "SEQ"


def is_asset_context():
    return bpy.context.scene.kitsu.category == "ASSET"


def is_shot_context():
    return bpy.context.scene.kitsu.category == "SHOT"
