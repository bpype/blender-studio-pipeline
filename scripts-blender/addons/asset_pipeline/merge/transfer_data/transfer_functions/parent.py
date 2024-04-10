import bpy
from ..transfer_util import check_transfer_data_entry
from ...task_layer import get_transfer_data_owner
from ...naming import merge_get_basename
from .... import constants, logging


def parent_clean(obj):
    logger = logging.get_logger()
    matches = check_transfer_data_entry(
        obj.transfer_data_ownership,
        merge_get_basename(constants.PARENT_TRANSFER_DATA_ITEM_NAME),
        constants.PARENT_KEY,
    )

    if len(matches) != 0:
        return

    obj.parent = None
    logger.debug("Cleaning Parent Relationship")


def parent_is_missing(transfer_data_item):
    if (
        transfer_data_item.type == constants.PARENT_KEY
        and transfer_data_item.id_data.parent == None
    ):
        return True


def init_parent(scene, obj):
    asset_pipe = scene.asset_pipeline
    td_type_key = constants.PARENT_KEY
    name = constants.PARENT_TRANSFER_DATA_ITEM_NAME
    transfer_data = obj.transfer_data_ownership

    if obj.parent not in list(asset_pipe.asset_collection.all_objects) and obj.parent is not None:
        raise Exception(f"Object parent {obj.parent.name} cannot be outside of asset collection")
    matches = check_transfer_data_entry(transfer_data, name, td_type_key)
    # Only add new ownership transfer_data_item if vertex group doesn't have an owner
    if len(matches) == 0:
        task_layer_owner, auto_surrender = get_transfer_data_owner(
            asset_pipe,
            td_type_key,
        )
        asset_pipe.add_temp_transfer_data(
            name=name,
            owner=task_layer_owner,
            type=td_type_key,
            obj_name=obj.name,
            surrender=auto_surrender,
        )


def transfer_parent(target_obj, source_obj):
    target_obj.parent = source_obj.parent

    target_obj.location = source_obj.location
    if source_obj.rotation_mode == 'QUATERNION':
        target_obj.rotation_quaternion = source_obj.rotation_quaternion
    else:
        target_obj.rotation_euler = source_obj.rotation_euler
    target_obj.scale = source_obj.scale
    target_obj.matrix_parent_inverse = source_obj.matrix_parent_inverse.copy()
