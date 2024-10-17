# Lattice Magic
This addon adds some Lattice-based utilities to Blender. 

![Lattice Magic UI](/media/addons/lattice_magic/lattice_magic.png)

## Table of Contents

- [Installation](#installation)
- [Tweak Lattice](#tweak-lattice)
    - [Parenting](#parenting)
    - [Deletion](#deletion)
    - [Adding/Removing meshes](#addingremoving-meshes)
    - [Going under the hood](#going-under-the-hood)
- [Camera Lattice](#camera-lattice)
    - [Creation](#creation)
    - [Parenting](#parenting-1)
    - [Animation](#animation)
    - [Deletion](#deletion-1)


## Installation
This add-on is now available through the [Blender Extension Platform](https://extensions.blender.org/add-ons/latticemagic/), so you can simply search for it in Blender's interface to grab it.

---

# Tweak Lattice
Tweak Lattice lets you create a lattice setup at the 3D cursor to make deformation adjustments to the selected objects.  

<video controls src="/media/addons/lattice_magic/tweak_lattice.mp4" title="Title"></video>

### Parenting
This tool was designed for use with a character rig: After pressing the "Create Tweak Lattice" button, you can simply select the desired parent rig object and bone in the pop-up before confirming.

### Deletion
If you want to delete a lattice, don't just delete the empty object that was created for you. This would leave behind broken modifiers and drivers. Instead, use the "Delete Tweak Lattice" button.

### Adding/Removing meshes
When creating a lattice, it will affect all mesh objects which were selected at the moment of its creation.  

If you want more meshes to be influenced by a lattice, just select them, then select the lattice control. There will be an "Add Selected Objects" button.  

Once objects are added to the lattice, you can remove them in the same way, or just click the "X" next to them in the "Affected Objects" list.

### Masking
If you want a tweak lattice to only affect a certain area, you can create a vertex group, and then specify this under the "Affected Objects" list.

### Going under the hood
With the lattice control selected, you can see a "Helper Objects" section in the UI. This lists two objects which are taking care of things under the hood. If you want, you can enable them with the screen icon, which will let you mess with them. This should rarely be necessary though, and you should only do it at your own risk, since there's no way to get these back to their original states once modified.


## Camera Lattice
Camera Lattice lets you create a lattice in a camera's view frame and deform a character (or any collection) with the lattice.

<video controls src="/media/addons/lattice_magic/camera_lattice.mp4" title="Title"></video>

### Creation
Add an entry to the Camera Lattice list with the + icon. Each entry corresponds to deforming a single collection with a single lattice object from the perspective of a single camera.  

You must select a collection and a camera, then hit Generate Lattice. Note that you cannot change the resolution after the fact, so find a resolution that you're happy with, as you will be locked into that.  

### Parenting
On creation, the lattice is parented to the camera. You can feel free to remove or change this parenting to your heart's desire, it shouldn't cause any issues. The lattice object also has a Damped Track constraint, the same applies there: You can remove it if you want.  

Just remember, there's no reset button for these sort of things.

### Animation
Feel free to animate the lattice in object mode as you wish, although unless the above mentioned Damped Track constraint is enabled, you will only be able to rotate it on one axis.  

Animating the lattice's vertices is possible using shape keys. The addon provides some UI and helper operators for this, but at the end of the day it's up to you how you organize and keyframe these shape keys.
The intended workflow is that a shape key should only be active for a single frame. To help with this, shape keys are named when they are added, according to the current frame. There are also some buttons above the list:
- Zero All Shape Keys: Operator to set all shape key values to 0.0. This does not insert a keyframe!  
- Keyframe All Shape Keys: Operator to insert a keyframe for all shape keys on the current frame with their current value.  
- Update Active Shape Key: Toggle to automatically change the active shape key based on the current frame. Useful when switching into edit mode quickly on different frames.  

Note that Blender is not capable of displaying the effect of multiple shape keys on a lattice at the same time, which is another reason to go with the intended workflow, since that will always only have one shape key active at a time.


### Deletion  
Similar to Tweak Lattice, never ever delete a lattice setup by simply pressing the X or Del keys, as this will leave behind a huge mess. Instead, use the "Delete Lattice" button, or the "-" button in the top list.  
