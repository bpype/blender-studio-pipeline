# Remap Tools

This directory contains scripts that are useful for re-organizing production directories. The tools are intended to be used when some directories need to be changed, and references to these directories need to be updated in .blend files.

## Usage
1. Enter remap directory `cd blender-studio-tools/scripts/remap`
2. Run the remap tool via `python -m remap`. You will be prompted for a directory to map, and a location to store the map (outside of your remap directory).
3. Now you are ready to re-organize your mapped directory, move files into different folders, rename files and remove duplicates.
4. Re-run the remap tool via `python -m remap` to update your map with the new file locations. The tool will print a bbatch, copy this for use in step 6.
5. Enter bbatch directory `cd blender-studio-tools/scripts/bbatch`
6. Run provided bbatch command, similar to `python -m bbatch {my_files}/ --nosave --recursive --script {path_to_script}/remap_blender_paths.py --args "{path_to_json}/dir_map.json"` to update all references to the remapped directory contents in your .blend files.
