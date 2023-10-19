from blender_kitsu.shot_builder.connectors.kitsu import KitsuConnector

PRODUCTION_NAME = KitsuConnector
SHOTS = KitsuConnector
ASSETS = KitsuConnector
RENDER_SETTINGS = KitsuConnector

# Formatting rules
# ----------------

# The name of the scene in blender where the shot is build in.
SCENE_NAME_FORMAT = "{shot.name}.{task_type}"
SHOT_NAME_FORMAT = "{shot.name}"
