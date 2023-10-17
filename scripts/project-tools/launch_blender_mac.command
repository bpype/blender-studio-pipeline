#!/bin/bash

die(){ echo "$@" 1>&2; install_python=true; }

command -v python3 >/dev/null 2>&1 || die "This requires python3 to be installed, installing via homebrew"

if [[ ${install_python} ]]; then
  # Python3 comes as a dependecy of brew.
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
fi

# Make sure we are in this files directory
cd "$(dirname "$0")"

./run_blender.py
