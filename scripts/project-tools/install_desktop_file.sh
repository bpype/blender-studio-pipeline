#!/bin/bash

# Make sure we are in this files directory
cd "$(dirname "$0")"

PROJECT_NAME="$(basename $(realpath ../../))"
DESKTOP_FILE_DST="$HOME/.local/share/applications/blender_$PROJECT_NAME.desktop"
BLENDER_BIN_PATH=$(realpath ./run_blender.py)
BLENDER_ICON_NAME="blender-bin"

echo "
[Desktop Entry]
Name=Blender $PROJECT_NAME
GenericName=3D modeler
Keywords=3d;cg;modeling;animation;painting;sculpting;texturing;video editing;video tracking;rendering;render engine;cycles;game engine;python;
Exec=sh -c '$BLENDER_BIN_PATH %f || read -p \"Press any key to close this window\"'
Icon=$BLENDER_ICON_NAME
Terminal=true
Type=Application
PrefersNonDefaultGPU=true
Categories=Graphics;3DGraphics;
MimeType=application/x-executable;
" > $DESKTOP_FILE_DST
