import bpy
from pathlib import Path
import json
import hashlib
import time
import contextlib

file_updated = False

json_file_path = ""  # File Path to read/write JSON File to

gold_file_map_json = Path(json_file_path)
gold_file_map_data = open(gold_file_map_json)
gold_file_map_dict = json.load(gold_file_map_data)


@contextlib.contextmanager
def override_save_version():
    """Overrides the save version settings"""
    save_version = bpy.context.preferences.filepaths.save_version

    try:
        bpy.context.preferences.filepaths.save_version = 0
        yield

    finally:
        bpy.context.preferences.filepaths.save_version = save_version


def paths_for_vse_strip(strip):
    if hasattr(strip, "filepath"):
        return [strip.filepath]
    if hasattr(strip, "directory"):
        return [strip.directory + elt.filename for elt in strip.elements]
    if hasattr(strip, "sound"):
        return [strip.sound.filepath]
    return []


def generate_checksum(filepath: str) -> str:
    """
    Generate a checksum for a zip file
    Arguments:
        archive_path: String of the archive's file path
    Returns:
        sha256 checksum for the provided archive as string
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as file:
        # Read the file in chunks to handle large files efficiently
        chunk = file.read(4096)
        while len(chunk) > 0:
            sha256.update(chunk)
            chunk = file.read(4096)
    return sha256.hexdigest()


def find_new_from_old(old_path):
    for _, value in gold_file_map_dict.items():
        for old_json_path in value['old']:
            if old_json_path.endswith(old_path.split("/..")[-1]):
                if value['new'] != old_json_path:
                    return value['new']
    for _, value in gold_file_map_dict.items():
        for old_json_path in value['old']:
            if old_json_path.endswith(old_path.split("/")[-1]):
                if value['new'] != old_json_path:
                    return value['new']


def update_vse_references():
    global file_updated
    for scn in bpy.data.scenes:
        if not scn.sequence_editor:
            continue
        for strip in scn.sequence_editor.sequences_all:
            for path in paths_for_vse_strip(strip):
                if path == "":
                    continue
                new_path = find_new_from_old(path)
                if not new_path:
                    print(f"No new path for '{strip.name}' at '{path}' ")
                    continue
                if strip.type == "IMAGE":
                    old_filename = Path(path).name.__str__()
                    for elm in strip.elements:
                        if elm.filename == old_filename:
                            elm.filename = Path(new_path).name.__str__()
                    print(f"Remapping Image Strip {strip.name} {path} to {new_path}")
                    strip.directory = Path(new_path).parent.__str__()
                    file_updated = True

                if strip.type == "MOVIE":
                    if Path(new_path).is_file():
                        print(
                            f"Remapping Movie Strip {strip.name} {path} to {new_path}"
                        )
                        strip.filepath = Path(new_path).__str__()  # new_path
                        file_updated = True
                if strip.type == "SOUND":
                    if Path(new_path).is_file():
                        print(
                            f"Remapping Sound Strip {strip.name} {path} to {new_path}"
                        )
                        strip.sound.filepath = Path(new_path).__str__()  # new_path
                        file_updated = True


def update_referenced_images():
    global file_updated
    for img in bpy.data.images:
        if img.filepath is not None and img.filepath != "":
            new_path = find_new_from_old(img.filepath)
            if new_path:
                print(f"Remapping Image Datablock {img.filepath }")
                img.filepath = new_path
                file_updated = True


def update_libs():
    global file_updated
    for lib in bpy.data.libraries:
        new_path = find_new_from_old(lib.filepath)
        if new_path:
            lib.filepath = new_path
            print(f"Remapping {lib.filepath}")
            file_updated = True


def remap_all_blender_paths():
    start = time.time()
    update_vse_references()
    update_referenced_images()
    update_libs()
    bpy.ops.file.make_paths_relative()
    end = time.time()

    if file_updated == True:
        with override_save_version():
            bpy.ops.wm.save_mainfile()
            print(f"Saved file: '{bpy.data.filepath}'")

    print("File Path Updater time elapsed in minutes")
    print((end - start) / 60)


remap_all_blender_paths()
