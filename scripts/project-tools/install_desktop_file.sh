#!/bin/bash

# Make sure we are in this files directory
cd "$(dirname "$0")"

PROJECT_NAME="Pets"
DESKTOP_FILE_DST="$HOME/.local/share/applications/blender_$PROJECT_NAME.desktop"
BLENDER_BIN_PATH=$(realpath ./run_blender.py)

cp ../../local/blender/linux/blender.desktop $DESKTOP_FILE_DST

# Update the .desktop file data
# 1. Replace the executable path with the path to "run_blender.py"
# 2. Replace the desktop entry text with "Blender <PROJECT_NAME>"
# 3. Make it so that you can right click on other blender binaries and "open with" the run_blender.py for this project
# 4. Make sure we start Blender in a terminal window
sed -i \
  -e "s:Exec=blender:Exec=$BLENDER_BIN_PATH:" \
  -e "s:Blender:Blender $PROJECT_NAME:" \
  -e "s:application/x-blender:application/x-executable" \
  -e "s:Terminal=false:Terminal=true" \
  "$DESKTOP_FILE_DST"
