# SPDX-FileCopyrightText: 2021 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import bpy

PATTERN_FRAME_COUNTER = r"\d+$"

REVIEW_OUTPUT_DIR = Path.home().joinpath("blender-media-viewer")

BLENDER_EXEC = Path(bpy.app.binary_path)

TO_MOVIE_SCRIPT_PATH = Path(__file__).parent.joinpath("convert_to_movie.py")

EXT_MOVIE = [
    ".avi",
    ".flc",
    ".mov",
    ".movie",
    ".mp4",
    ".m4v",
    ".m2v",
    ".m2t",
    ".m2ts",
    ".mts",
    ".ts",
    ".mv",
    ".avs",
    ".wmv",
    ".ogv",
    ".ogg",
    ".r3d",
    ".dv",
    ".mpeg",
    ".mpg",
    ".mpg2",
    ".vob",
    ".mkv",
    ".flv",
    ".divx",
    ".xvid",
    ".mxf",
    ".webm",
]

EXT_IMG = [
    ".jpg",
    ".png",
    ".exr",
    ".tga",
    ".bmp",
    ".jpeg",
    ".sgi",
    ".rgb",
    ".rgba",
    ".tif",
    ".tiff",
    ".tx",
    ".hdr",
    ".dpx",
    ".cin",
    ".psd",
    ".pdd",
    ".psb",
    ".webp",
]

EXT_TEXT = [
    ".txt",
    ".glsl",
    ".osl",
    ".data",
    ".pov",
    ".ini",
    ".mcr",
    ".inc",
    ".fountain",
    ".rst",
    ".ass",
]

EXT_SCRIPT = [".py"]


def get_config_file() -> Path:
    path = bpy.utils.user_resource("CONFIG", path="media_viewer", create=True)
    return Path(path) / "config.json"


FOLDER_HISTORY_STEPS: int = 10
PAN_VIEW_DELTA: int = 50
