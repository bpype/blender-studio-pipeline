ADDON_NAME = "asset_pipeline"

# Delimiter used for naming data within Blender
NAME_DELIMITER = "-"


###################
# MERGE
###################

# Delimiter used by suffixes in the merge process
MERGE_DELIMITER = "."

# Suffixes used when naming items to merge
LOCAL_SUFFIX = "LOCAL"
EXTERNAL_SUFFIX = "EXTERNAL"


###################
# Task Layers
###################

# Name of directory containing task layer prefixes internal to add-on
TASK_LAYER_CONFIG_DIR_NAME = "task_layer_configs"

# Name of task layer file found a the root of an asset
TASK_LAYER_CONFIG_NAME = "task_layers.json"


###################
# Transferable Data
###################

# Keys for transferable data
NONE_KEY = "NONE"
VERTEX_GROUP_KEY = "GROUP_VERTEX"
MODIFIER_KEY = "MODIFIER"
CONSTRAINT_KEY = "CONSTRAINT"
MATERIAL_SLOT_KEY = "MATERIAL"
SHAPE_KEY_KEY = "SHAPE_KEY"
ATTRIBUTE_KEY = "ATTRIBUTE"
PARENT_KEY = "PARENT"

# Information about supported transferable data.
# UI Bools are defined in props.py file
# {Key string : ("UI Name", 'ICON', "UI_BOOL_KEY")}
TRANSFER_DATA_TYPES = {
    NONE_KEY: ("None", "BLANK1", 'none'),
    VERTEX_GROUP_KEY: ("Vertex Groups", 'GROUP_VERTEX', 'group_vertex_ui_bool'),
    MODIFIER_KEY: ("Modifiers", 'MODIFIER', 'modifier_ui_bool'),
    CONSTRAINT_KEY: ("Constraints", 'CONSTRAINT', 'constraint_ui_bool'),
    MATERIAL_SLOT_KEY: ("Materials", 'MATERIAL', 'material_ui_bool'),
    SHAPE_KEY_KEY: ("Shape Keys", 'SHAPEKEY_DATA', 'shapekey_ui_bool'),
    ATTRIBUTE_KEY: ("Attributes", 'EVENT_A', 'attribute_ui_bool'),
    PARENT_KEY: ("Parent", 'FILE_PARENT', 'file_parent_ui_bool'),
}

# Convert it to the format that EnumProperty.items wants:
# List of 5-tuples; Re-use name as description at 3rd element, add index at 5th.
TRANSFER_DATA_TYPES_ENUM_ITEMS = [
    (tup[0], tup[1][0], tup[1][0], tup[1][1], i)
    for i, tup in enumerate(TRANSFER_DATA_TYPES.items())
]


# Name used in all material transferable data
MATERIAL_TRANSFER_DATA_ITEM_NAME = "All Materials"

# Name used in parent transferable data
PARENT_TRANSFER_DATA_ITEM_NAME = "Parent Relationship"

MATERIAL_ATTRIBUTE_NAME = "material_index"


###################
# SHARED IDs
###################

# SHARED ID Icons
GEO_NODE = "GEOMETRY_NODES"
IMAGE = "IMAGE_DATA"
BLANK = "BLANK1"


###################
# Publish
###################

# List of different states used when Publishing a Final Asset
PUBLISH_TYPES = [
    (
        "publish",
        "Active",
        "Publish a new active version that will become the latest published version",
    ),
    (
        "staged",
        "Staged",
        """Publish a staged version that will replace the last active version as the Push/Pull target.
        Used for internal asset pipeline use only""",
    ),
    (
        "review",
        "Review",
        "Test the results that will be published in the review area, will not be used as Push/Pull target",
    ),
]
PUBLISH_KEYS = [pub_type[0] for pub_type in PUBLISH_TYPES]
ACTIVE_PUBLISH_KEY = PUBLISH_KEYS[0]
STAGED_PUBLISH_KEY = PUBLISH_KEYS[1]
