import bpy
from pathlib import Path


def is_edit_file():
    return Path(bpy.data.filepath).parents[0].name == 'edit'


# Category values are defined in enum props.py KITSU_property_group_scene under category
def is_sequence_context():
    return bpy.context.scene.kitsu.category == "SEQS"


def is_asset_context():
    return bpy.context.scene.kitsu.category == "ASSETS"


def is_shot_context():
    return bpy.context.scene.kitsu.category == "SHOTS"
