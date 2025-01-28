# Remap Tools

This directory contains a script that resyncs any files older than one day and saves the file. The script requires two arguments:
1. The path to the project
2. the argument `--exec` followed by the path to the blender executable 
3. Optionally provide `--filter` argument followed by a string to filter for specific file

## Usage
1. Enter remap directory `cd blender-studio-tools/scripts/resync_blends`
2. Run `./run_resync_blends.py /data/your_project_name/ --exec /home/user/blender/bin/blender --filter anim.blend` 
