from pathlib import Path
import bpy

MOVIE_EXT = [
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

IMG_EXT = [".png", ".tga", ".bmp", ".jpg", ".jpeg", ".sgi", ".rgb", ".rgba"]


def get_config_file() -> Path:
    path = bpy.utils.user_resource("CONFIG", path="video_player", create=False)
    return Path(path) / "config.json"
