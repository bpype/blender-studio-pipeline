# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import (
    categories, 
	props,
    templates, 
    json_io, 
    execution, 
    ui, 
    override_picker,
)


bl_info = {
	"name": "Lighting Overrider",
	"author": "Simon Thommes",
    "version": (0, 1, 3),
	"blender": (3, 0, 0),
	"location": "3D Viewport > Sidebar > Overrides",
	"description": "Tool for the Blender Studio to create, manage and store local python overrides of linked data on a shot and sequence level.",
	"category": "Workflow",
}

modules = [
	ui,
	templates,
	categories,
	props,
	json_io,
	execution,
	override_picker,
]

def register():
	for m in modules:
	    m.register()
    
def unregister():
	for m in modules:
	    m.unregister()