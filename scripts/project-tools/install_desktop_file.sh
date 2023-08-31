#!/bin/bash

# Make sure we are in this files directory
cd "$(dirname "$0")"

PROJECT_NAME="Pets"
DESKTOP_FILE_DST="$HOME/.local/share/applications/blender_$PROJECT_NAME.desktop"
BLENDER_BIN_PATH=$(realpath ./run_blender.py)

cp ../../local/blender/linux/blender.desktop $DESKTOP_FILE_DST

# Update the .desktop file data
sed -i -e "s:Exec=blender:Exec=$BLENDER_BIN_PATH:" -e "s:Blender:Blender $PROJECT_NAME:" "$DESKTOP_FILE_DST"
