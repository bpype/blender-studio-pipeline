# Remap Tools

This directory contains scripts that are useful for re-organizing production directories. The tools are intended to be used when some directories need to be changed, and references to these directories need to be updated in .blend files.

## Usage
1. Set the variable `json_file_path` to match in all script files. Set `folder_path` in both has_map script files.
2. Run `hash_map_make.py` to create a JSON file listing every file in directory via hash, plus a list directories leading to that file (duplicate files included).
3. Re-organize/rename items in the directory you have made a map for.
4. Run `hash_map_update.py` to find the new locations of these files using the Hash to match them up. This will add a `new` directory for each hash.
5. Using [`bbatch`](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts/bbatch/README.md) run the script `remap_blender_paths.py` to update references in .blend files from the old path to the new path.