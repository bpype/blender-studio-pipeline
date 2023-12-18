from ..builder.build_step import BuildStep, BuildContext
from ..asset import *
from ..project import *
from ..shot import *
import pathlib

import bpy

import logging

logger = logging.getLogger(__name__)


def save_shot_builder_file(file_path: str):
    """Save Shot File within Folder of matching name.
    Set Shot File to relative Paths."""
    dir_path = pathlib.Path(file_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_mainfile(filepath=file_path, relative_remap=True)


class SaveFileStep(BuildStep):
    def __str__(self) -> str:
        return "save file"

    def execute(self, build_context: BuildContext) -> None:
        shot = build_context.shot
        file_path = pathlib.Path(shot.file_path)
        save_shot_builder_file(file_path)
        logger.info(f"save file {shot.file_path}")
