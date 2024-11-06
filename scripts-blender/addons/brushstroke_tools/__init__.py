from . import utils, icons, settings, preferences, ui, draw_tool, ops
import tomllib as toml
import bpy

modules = [utils, icons, settings, preferences, ui, draw_tool, ops]

def register():
	# register modules
	for m in modules:
		m.register()
	
	# read addon meta-data
	with open(f"{utils.get_addon_directory()}/blender_manifest.toml", 'rb') as f:
		manifest = toml.load(f)
	utils.addon_version = tuple([int(i) for i in manifest['version'].split('.')])
	
	# Add addon asset library
	utils.register_asset_lib()

	# Get available brush styles
	#utils.refresh_brushstroke_styles()

def unregister():
	# un-register modules
	for m in reversed(modules):
		m.unregister()

	# Remove addon asset library
	utils.unregister_asset_lib()