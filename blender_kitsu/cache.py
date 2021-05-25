from typing import Any

import bpy

from bpy.app.handlers import persistent

from . import bkglobals
from .types import Project, Sequence, Shot, Asset, AssetType, TaskType
from .logger import ZLoggerFactory
from .gazu.exception import RouteNotFoundException

logger = ZLoggerFactory.getLogger(name=__name__)

# CACHE VARIABLES
# used to cache active entitys to prevent a new api request when read only
_project_active: Project = Project()
_sequence_active: Sequence = Sequence()
_shot_active: Shot = Shot()
_asset_active: Asset = Asset()
_asset_type_active: AssetType = AssetType()
_task_type_active: TaskType = TaskType()

_cache_initialized: bool = False


def _addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def project_active_get() -> Project:
    global _project_active

    return _project_active


def project_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _project_active

    _project_active = Project.by_id(entity_id)
    _addon_prefs_get(context).project_active_id = entity_id
    logger.info("Set active project to %s", _project_active.name)


def project_active_reset(context: bpy.types.Context) -> None:
    global _project_active
    _project_active = Project()
    _addon_prefs_get(context).project_active_id = ""
    logger.info("Reset active project")


def sequence_active_get() -> Sequence:
    return _sequence_active


def sequence_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _sequence_active

    _sequence_active = Sequence.by_id(entity_id)
    context.scene.kitsu.sequence_active_id = entity_id
    logger.info("Set active sequence to %s", _sequence_active.name)


def sequence_active_reset(context: bpy.types.Context) -> None:
    global _sequence_active

    _sequence_active = Sequence()
    context.scene.kitsu.sequence_active_id = ""
    logger.info("Reset active sequence")


def shot_active_get() -> Shot:
    global _shot_active

    return _shot_active


def shot_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _shot_active

    _shot_active = Shot.by_id(entity_id)
    context.scene.kitsu.shot_active_id = entity_id
    logger.info("Set active shot to %s", _shot_active.name)


def shot_active_reset(context: bpy.types.Context) -> None:
    global _shot_active

    _shot_active = Shot()
    context.scene.kitsu.shot_active_id = ""
    logger.info("Reset active shot")


def asset_active_get() -> Asset:
    global _asset_active

    return _asset_active


def asset_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_active

    _asset_active = Asset.by_id(entity_id)
    context.scene.kitsu.asset_active_id = entity_id
    logger.info("Set active asset to %s", _asset_active.name)


def asset_active_reset(context: bpy.types.Context) -> None:
    global _asset_active

    _asset_active = Asset()
    context.scene.kitsu.asset_active_id = ""
    logger.info("Reset active asset")


def asset_type_active_get() -> AssetType:
    global _asset_type_active

    return _asset_type_active


def asset_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _asset_type_active

    _asset_type_active = AssetType.by_id(entity_id)
    context.scene.kitsu.asset_type_active_id = entity_id
    logger.info("Set active asset type to %s", _asset_type_active.name)


def asset_type_active_reset(context: bpy.types.Context) -> None:
    global _asset_type_active

    _asset_type_active = AssetType()
    context.scene.kitsu.asset_type_active_id = ""
    logger.info("Reset active asset type")


def task_type_active_get() -> TaskType:
    global _task_type_active

    return _task_type_active


def task_type_active_set_by_id(context: bpy.types.Context, entity_id: str) -> None:
    global _task_type_active

    _task_type_active = TaskType.by_id(entity_id)
    context.scene.kitsu.task_type_active_id = entity_id
    logger.info("Set active task type to %s", _task_type_active.name)


def task_type_active_reset(context: bpy.types.Context) -> None:
    global _task_type_active

    _task_type_active = TaskType()
    context.scene.kitsu.task_type_active_id = ""
    logger.info("Reset active task type")


def _init_cache_entity(
    entity_id: str, entity_type: Any, cache_variable_name: Any, cache_name: str
) -> None:

    if entity_id:
        try:
            globals()[cache_variable_name] = entity_type.by_id(entity_id)
            logger.info(
                "Initiated active %s cache to: %s",
                cache_name,
                globals()[cache_variable_name].name,
            )
        except RouteNotFoundException:
            logger.error(
                "Failed to initialize active %s cache. ID not found on server: %s",
                cache_name,
                entity_id,
            )


def init_cache_variables() -> None:
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _task_type_active
    global _cache_initialized
    addon_prefs = _addon_prefs_get(bpy.context)

    if not addon_prefs.session.is_auth():
        logger.info("Skip initiating cache. Session not authorized.")
        return

    if _cache_initialized:
        logger.info("Cache already initiated.")
        return

    project_active_id = addon_prefs.project_active_id
    sequence_active_id = bpy.context.scene.kitsu.sequence_active_id
    shot_active_id = bpy.context.scene.kitsu.shot_active_id
    asset_active_id = bpy.context.scene.kitsu.asset_active_id
    asset_type_active_id = bpy.context.scene.kitsu.asset_type_active_id
    task_type_active_id = bpy.context.scene.kitsu.task_type_active_id

    _init_cache_entity(project_active_id, Project, "_project_active", "project")
    _init_cache_entity(sequence_active_id, Sequence, "_sequence_active", "sequence")
    _init_cache_entity(
        asset_type_active_id, AssetType, "_asset_type_active", "asset type"
    )
    _init_cache_entity(shot_active_id, Shot, "_shot_active", "shot")
    _init_cache_entity(asset_active_id, Asset, "_asset_active", "asset")
    _init_cache_entity(task_type_active_id, TaskType, "_task_type_active", "task type")

    _cache_initialized = True


def clear_cache_variables():
    global _project_active
    global _sequence_active
    global _shot_active
    global _asset_active
    global _asset_type_active
    global _task_type_active
    global _cache_initialized

    _shot_active = Shot()
    logger.info("Cleared active shot cache")

    _asset_active = Asset()
    logger.info("Cleared active asset cache")

    _sequence_active = Sequence()
    logger.info("Cleared active aequence cache")

    _asset_type_active = AssetType()
    logger.info("Cleared active asset type cache")

    _project_active = Project()
    logger.info("Cleared Active Project Cache")

    _task_type_active = TaskType()
    logger.info("Cleared Active Task Type Cache")

    _cache_initialized = False


@persistent
def load_post_handler_update_cache(dummy: Any) -> None:
    clear_cache_variables()
    init_cache_variables()


# ---------REGISTER ----------


def register():
    # handlers
    bpy.app.handlers.load_post.append(load_post_handler_update_cache)


def unregister():
    # clear handlers
    bpy.app.handlers.load_post.remove(load_post_handler_update_cache)
