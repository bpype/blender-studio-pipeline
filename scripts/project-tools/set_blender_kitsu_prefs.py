import bpy
from bl_ext.system.blender_kitsu import cache, prefs
from pathlib import Path
import json
import getpass

def print_header(text: str, level: int = 1):
    """
    Prints a header surrounded by asterisks.
    The higher the level, the more rows of asterisks above and below.
    """
    print()
    print()
    stars = '*' * max(20, len(text) + 4)
    for _ in range(level):
        print(stars)
    print(f"* {text.center(len(stars) - 4)} *")
    for _ in range(level):
        print(stars)


def set_blender_kitsu_login(login_data, addon_prefs):
    addon_prefs.host = login_data["host"]
    addon_prefs.email = input("Email: ").strip()
    addon_prefs.passwd = getpass.getpass("Password: ").strip()

    try:
        bpy.ops.kitsu.session_start()
    except RuntimeError:
        # Exception will already print on it's own
        return set_blender_kitsu_login(login_data, addon_prefs)

    if not prefs.session_get(bpy.context).is_auth():
        set_blender_kitsu_login(login_data, addon_prefs)

    cache.project_active_set_by_id(bpy.context, login_data["project_id"])


def set_blender_kitsu_paths(project_config, addon_prefs):
    base_path = Path(__file__).parents[2].as_posix()
    project_paths = project_config["project_paths"]
    setattr(addon_prefs, "project_root_dir", base_path)
    print("project root dir: ", base_path)

    for key, value in project_paths.items():
        setattr(addon_prefs, key, Path(base_path).joinpath(value).as_posix())
        print(key,": ", Path(base_path).joinpath(value).as_posix())


def set_blender_kitsu_generic_prefs(generic_prefs, addon_prefs):
    for key, value in generic_prefs.items():
        if hasattr(addon_prefs, key):
            setattr(addon_prefs, key, value)
        else:
            print(f"Warning: {key} is not a valid preference in Blender Kitsu Addon.")


def get_project_config():
    config_file = Path(__file__).parent.joinpath("project_config.json")
    with config_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def enable_blender_kitsu_addon():
    bpy.ops.preferences.addon_enable(module="bl_ext.system.blender_kitsu")


def set_asset_library(asset_lib_name):
    asset_libs = bpy.context.preferences.filepaths.asset_libraries
    asset_lib_path = Path(__file__).parents[2].joinpath("svn/pro/assets").as_posix()

    if asset_libs.get(asset_lib_name) is None:
        asset_lib = asset_libs.new(name=asset_lib_name, directory=asset_lib_path)
        asset_lib.import_method = 'LINK'
        asset_lib.use_relative_path = True
        print(f"Added new asset library: {asset_lib_name} at {asset_lib_path}")


def main():
    project_config = get_project_config()

    enable_blender_kitsu_addon()

    addon_prefs = prefs.addon_prefs_get(bpy.context)
    print_header("Artist Kitsu Login", 1)
    set_blender_kitsu_login(project_config["login_data"], addon_prefs)
    print_header("Kitsu Project Paths", 1)
    set_blender_kitsu_paths(project_config, addon_prefs)
    set_blender_kitsu_generic_prefs(project_config["generic_prefs"], addon_prefs)
    set_asset_library(project_config["login_data"]["project_name"])
    print_header("Writing Preferences", 1)
    bpy.ops.wm.save_userpref()
    bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    main()
