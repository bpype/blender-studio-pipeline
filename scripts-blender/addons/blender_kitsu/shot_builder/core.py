# SPDX-FileCopyrightText: 2023 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from pathlib import Path

from .. import bkglobals
from ..types import (
    Sequence,
    Shot,
    TaskType,
)

from ..cache import Project
from . import config
from .. import prefs
from ..anim import opsdata as anim_opsdata

#################
# Constants
#################
CAMERA_NAME = 'CAM-camera'


def get_shot_builder_config_dir(context: bpy.types.Context) -> Path:
    """Returns directory Shot Builder Hooks are stored in

    Args:
        context (bpy.types.Context): Blender Context

    Returns:
        Path: Path object to Shot Builder Hooks Directory
    """
    root_dir = prefs.project_root_dir_get(context)
    return root_dir.joinpath("pro/config/shot_builder")


def get_file_dir(seq: Sequence, shot: Shot, task_type: TaskType) -> Path:
    """Returns Path to Directory for Current Shot, will ensure that
    file path exists if it does not.

    Args:
        seq (Sequence): Sequence Class from blender_kitsu.types
        shot (Shot): Shot Class from blender_kitsu.types
        task_type TaskType Class from blender_kitsu.types

    Returns:
        Path: Returns Path for Shot Directory
    """
    project_root_dir = prefs.project_root_dir_get(bpy.context)
    all_shots_dir = project_root_dir.joinpath('pro').joinpath('shots')
    shot_dir = all_shots_dir.joinpath(seq.name).joinpath(shot.name)
    if not shot_dir.exists():
        shot_dir.mkdir(parents=True)
    return shot_dir


def set_render_engine(scene: bpy.types.Scene, engine='CYCLES'):
    scene.render.engine = engine


def remove_all_data():
    for lib in bpy.data.libraries:
        bpy.data.libraries.remove(lib)

    for col in bpy.data.collections:
        bpy.data.collections.remove(col)

    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

    for action in bpy.data.actions:
        bpy.data.actions.remove(action)

    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def set_shot_scene(context: bpy.types.Context, scene_name: str) -> bpy.types.Scene:
    print(f"create scene with name {scene_name}")
    for scene in bpy.data.scenes:
        scene.name = 'REMOVE-' + scene.name

    keep_scene = bpy.data.scenes.new(name=scene_name)
    for scene in bpy.data.scenes:
        if scene.name == scene_name:
            continue
        print(f"remove scene {scene.name}")
        bpy.data.scenes.remove(scene)

    context.window.scene = keep_scene
    return keep_scene


def set_resolution_and_fps(project: Project, scene: bpy.types.Scene):
    scene.render.fps = int(project.fps)  # set fps
    resolution = project.resolution.split('x')
    scene.render.resolution_x = int(resolution[0])
    scene.render.resolution_y = int(resolution[1])
    scene.render.resolution_percentage = 100


def set_frame_range(shot: Shot, scene: bpy.types.Scene):
    kitsu_start_3d = shot.get_3d_start()
    scene.frame_start = kitsu_start_3d
    if not shot.nb_frames:
        raise Exception(f"{shot.name} has missing frame duration information")
    scene.frame_end = kitsu_start_3d + shot.nb_frames - 1
    scene.frame_current = kitsu_start_3d


def link_data_block(file_path: str, data_block_name: str, data_block_type: str):
    bpy.ops.wm.link(
        filepath=file_path,
        directory=file_path + "/" + data_block_type,
        filename=data_block_name,
        instance_collections=False,
    )
    # TODO This doesn't return anything but collections
    return bpy.data.collections.get(data_block_name)


def link_and_override_collection(
    file_path: str, collection_name: str, scene: bpy.types.Scene
) -> bpy.types.Collection:
    """_summary_

    Args:
        file_path (str): File Path to .blend file to link from
        collection_name (str): Name of collection to link from given filepath
        scene (bpy.types.Scene): Current Scene to link collection to

    Returns:
        bpy.types.Collection: Overriden Collection linked to Scene Collection
    """
    collection = link_data_block(file_path, collection_name, "Collection")
    override_collection = collection.override_hierarchy_create(
        scene, bpy.context.view_layer, do_fully_editable=True
    )
    scene.collection.children.unlink(collection)
    # Make library override.
    return override_collection


def link_camera_rig(
    scene: bpy.types.Scene,
    output_collection: bpy.types.Collection,
):
    """
    Function to load the camera rig. The rig will be added to the output collection
    of the shot and the camera will be set as active camera.
    """
    # Load camera rig.
    project_path = prefs.project_root_dir_get(bpy.context)
    path = f"{project_path}/pro/assets/cam/camera_rig.blend"

    if not Path(path).exists():
        camera_data = bpy.data.cameras.new(name=CAMERA_NAME)
        camera_object = bpy.data.objects.new(name=CAMERA_NAME, object_data=camera_data)
        scene.collection.objects.link(camera_object)
        output_collection.objects.link(camera_object)
        return

    collection_name = "CA-camera_rig"  # TODO Rename the asset itself, this breaks convention

    override_camera_col = link_and_override_collection(
        file_path=path, collection_name=collection_name, scene=scene
    )
    output_collection.children.link(override_camera_col)

    # Set the camera of the camera rig as active scene camera.
    camera = override_camera_col.objects.get(CAMERA_NAME)
    scene.camera = camera


def create_task_type_output_collection(
    scene: bpy.types.Scene, shot: Shot, task_type: TaskType
) -> bpy.types.Collection:
    collections = bpy.data.collections
    output_col_name = shot.get_output_collection_name(task_type.get_short_name())

    if not collections.get(output_col_name):
        bpy.data.collections.new(name=output_col_name)
    output_collection = collections.get(output_col_name)

    output_collection.use_fake_user = True
    if not scene.collection.children.get(output_col_name):
        scene.collection.children.link(output_collection)

    for view_layer in scene.view_layers:
        view_layer_output_collection = view_layer.layer_collection.children.get(output_col_name)
        view_layer_output_collection.exclude = True
    return output_collection


def link_task_type_output_collections(shot: Shot, task_type: TaskType):
    task_type_short_name = task_type.get_short_name()
    if config.OUTPUT_COL_LINK_MAPPING.get(task_type_short_name) == None:
        return
    for short_name in config.OUTPUT_COL_LINK_MAPPING.get(task_type_short_name):
        external_filepath = shot.get_filepath(bpy.context, short_name)
        if not Path(external_filepath).exists():
            print(f"Unable to link output collection for {Path(external_filepath).name}")
            continue
        file_path = external_filepath.__str__()
        colection_name = shot.get_output_collection_name(short_name)
        link_data_block(file_path, colection_name, 'Collection')


def add_action_to_armature(collection: bpy.types.Collection, shot_active: Shot):
    for obj in collection.all_objects:
        # Skip Armatures that are hidden from viewport because they aren't intended to be animated
        if obj.type == 'ARMATURE' and not obj.hide_viewport:
            if not obj.animation_data:
                obj.animation_data_create()
            name = anim_opsdata.gen_action_name(obj, collection, shot_active)
            if obj.animation_data.action and obj.animation_data.action.name == name:
                continue
            obj.animation_data.action = bpy.data.actions.new(name=name)
