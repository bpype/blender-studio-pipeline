ADDON_NAME = "asset_pipeline"

# Delimiter used for naming data within Blender
NAME_DELIMITER = "-"

# Delimiter used for naming .blend files
FILE_DELIMITER = NAME_DELIMITER

###################
# MERGE
###################

# Delimiter used by suffixes in the merge process
MERGE_DELIMITER = "."

# Suffixes used when naming items to merge. Max 3 chars!
LOCAL_SUFFIX = "LOC"
EXTERNAL_SUFFIX = "EXT"


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
CUSTOM_PROP_KEY = "CUSTOM_PROP"

# Information about supported transferable data.
# UI Bools are defined in props.py file
# {Key string : ("UI Name", 'ICON')}
TRANSFER_DATA_TYPES = {
    NONE_KEY: ("None", "BLANK1"),
    VERTEX_GROUP_KEY: ("Vertex Groups", 'GROUP_VERTEX'),
    MODIFIER_KEY: ("Modifiers", 'MODIFIER'),
    CONSTRAINT_KEY: ("Constraints", 'CONSTRAINT'),
    MATERIAL_SLOT_KEY: ("Materials", 'MATERIAL'),
    SHAPE_KEY_KEY: ("Shape Keys", 'SHAPEKEY_DATA'),
    ATTRIBUTE_KEY: ("Attributes", 'MOD_DATA_TRANSFER'),
    PARENT_KEY: ("Parent", 'FILE_PARENT'),
    CUSTOM_PROP_KEY: ("Custom Properties", 'PROPERTIES'),
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

ADDON_OWN_PROPERTIES = ['asset_id_owner', 'asset_id_surrender', 'transfer_data_ownership']

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
        "Active version that will become the latest published version, used in production files",
    ),
    (
        "staged",
        "Staged",
        """Staged version that will replace the last active version as the Push/Pull/Sync target. Not used in production files""",
    ),
    (
        "sandbox",
        "Sandbox",
        "Test the results that will be published in the sandbox area, will not be used as Push/Pull target",
    ),
]
PUBLISH_KEYS = [pub_type[0] for pub_type in PUBLISH_TYPES]
ACTIVE_PUBLISH_KEY = PUBLISH_KEYS[0]
STAGED_PUBLISH_KEY = PUBLISH_KEYS[1]
SANDBOX_PUBLISH_KEY = PUBLISH_KEYS[2]


#############
# Logging
#############

LOGGER_LEVEL_ITEMS = (
    ('10', 'Debug', ''),
    ('20', 'Info', ''),
    ('30', 'Warning', ''),
    ('40', 'Error', ''),
    ('50', 'Critical', ''),
)
