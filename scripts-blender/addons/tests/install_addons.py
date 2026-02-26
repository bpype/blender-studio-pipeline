from pathlib import Path

import bpy


def install_addon(context, addon_name=""):
    """Install this add-on by adding its parent folder as a local repository (requires Blender >=4.2)
    Expected folder hierarchy:
    Root
        Addon Source
            blender_manifest.toml
        Tests
            this_file.py
    """
    repos = context.preferences.extensions.repos

    # Disable all other repos.
    for repo in repos:
        repo.enabled = False

    # Add add-on repo.
    repo_dir, addon_name, module_name = get_filepath_info(addon_name)
    _addon_repo = repos.new(name=addon_name,
                            module=module_name,
                            custom_directory=repo_dir)

    print("Extension repo added: ", repo_dir)

    # Enable the add-on.
    if addon_name:
        assert bpy.ops.preferences.addon_enable(
            module=f"bl_ext.{module_name}.{addon_name}") == {
                'FINISHED'
            }, f"Failed to install {addon_name}."

        print(f"Installed {addon_name}.")


def disable_addon(addon_name: str):
    _repo_dir, addon_name, module_name = get_filepath_info(
        addon_name=addon_name)
    assert bpy.ops.preferences.addon_disable(
        module=f"bl_ext.{module_name}.{addon_name}") == {
            'FINISHED'
        }, f"Failed to unregister {addon_name}."


def enable_this(addon_name):
    _repo_dir, addon_name, module_name = get_filepath_info(
        addon_name=addon_name)
    assert bpy.ops.preferences.addon_enable(
        module=f"bl_ext.{module_name}.{addon_name}") == {
            'FINISHED'
        }, f"Failed to register {addon_name}."


def get_filepath_info(addon_name="") -> tuple[str, str, str]:
    filepath = Path(__file__)
    dirpath = filepath.parent.parent
    addon_name = addon_name or dirpath.name
    module_name = addon_name.lower()
    return dirpath.as_posix(), addon_name, module_name
