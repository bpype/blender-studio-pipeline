# GeoNode Shape Keys
GeoNode Shape Keys is a Blender Add-on that lets you deform [linked and overridden](https://docs.blender.org/manual/en/latest/files/linked_libraries/library_overrides.html#make-an-override) meshes using sculpt mode in a roundabout way using a geometry node set-up. While the current override system doesn't support adding or editing shape keys on overridden meshes, it does allow you to add modifiers, so this add-on leverages that.

## Installation
Find installation instructions [here](https://studio.blender.org/pipeline/addons/overview).

# How to use
The add-on's UI is only visible on [linked and overridden](https://docs.blender.org/manual/en/latest/files/linked_libraries/library_overrides.html#make-an-override) meshes.  
It can be found under Properties->Object Data->Shape Keys->GeoNode Shape Keys:

<img src="/media/addons/geonode_shapekeys/gnsk_ui.png" width=500>

You can then hit +, which will prompt you for a UV Map, and a name for your shape. By default it will be named after the current frame.

Once you press OK, you can start sculpting. But you're not actually sculpting on your original mesh. A duplicate has been created for you, and the original was hidden. You can switch back to the original using this button:

<img src="/media/addons/geonode_shapekeys/switch_to_render_objs.png" width=500>

Removing a GeoNode ShapeKey entry will also remove the relevant modifier and object. Don't remove those in any other way.

Here is a workflow example video showing all of the above steps:  

<video controls src="/media/addons/geonode_shapekeys/gnsk_example.mp4" title="Title"></video>

### Why a UV Map?
If your mesh doesn't have any overlapping in its UVs, you can just use that. Otherwise however, you should create a separate UVMap for use with this add-on. The UVMap is used by the GeoNodes set-up to match the vertices of the real object with the local copy that you sculpt on.

### Multi-object sculpting
The add-on also supports selecting multiple objects before pressing the + button. In this case, the sculpt object will have all your previously selected objects. The principle that the sculpt object shouldn't have any overlapping UVs still stands.
An operator is provided to easily create UVMaps across all of your asset's objects without any overlaps, for use with this add-on. You can find this here:

<img src="/media/addons/geonode_shapekeys/ensure_uvmap_op.png" width=500>
