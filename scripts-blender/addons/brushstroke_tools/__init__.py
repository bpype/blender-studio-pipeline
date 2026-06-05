# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from . import geomod, utils, icons, settings, preferences, ui, draw_tool, ops
import tomllib as toml

modules = [geomod, utils, icons, settings, preferences, ui, draw_tool, ops]

def register():
	# register modules
	for m in modules:
		importlib.reload(m)
		if hasattr(m, 'register'):
			m.register()
	
	# read addon meta-data
	with open(f"{utils.get_addon_directory()}/blender_manifest.toml", 'rb') as f:
		manifest = toml.load(f)
	utils.addon_version = tuple([int(i) for i in manifest['version'].split('.')])
	
	# Add addon asset library
	utils.register_asset_lib()

	# Copy resource files to config directory
	utils.unpack_resources()

def unregister():
	# un-register modules
	for m in reversed(modules):
		if hasattr(m, 'unregister'):
			m.unregister()

	# Remove addon asset library
	utils.unregister_asset_lib()