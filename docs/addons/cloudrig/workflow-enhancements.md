# Workflow Enhancements
CloudRig includes several quality of life features, each with a default hotkey. If these interfere with your workflow, you can easily rebind or disable them in the preferences.

<img src="/media/addons/cloudrig/hotkeys_ui.png">

## MetaRig Swapping / Generation
- **Shift+T** swaps between a metarig and its generated rig, syncing bone collections, visibility, and selection.
- **Shift+T** on a mesh object enters pose mode on its deforming armature, if any.
- **Ctrl+Shift+R** regenerates the active metarig/rig. If there is only one metarig in the scene, it doesn't need to be active.

## Better Duplicate & Extrude
- **E** (Extrude) and **Shift+D** (Duplicate) increment bone names:
    - Duplicating `Bone1` creates `Bone2`, not `Bone1.001`.
    - Hold **Shift** while confirming to keep the original numbering.
- Handles occupied names: if `Bone2` exists, it creates `Bone3`.
- Supports symmetry: increments names on the opposite side.
- **Shift+D** also copies drivers on bone and constraint properties.

<video src="/media/addons/cloudrig/better_duplicate_extrude.mp4" controls></video>

## Bone Selection Pie (Alt+D)
Select bones related to the active bone. Available in Pose, Weight Paint, and Edit modes.
<img src="/media/addons/cloudrig/pie_bone_find.png">

- **Up/Down**: Select a bone with a higher/lower number in its name, e.g., from `Hair1.L` to `Hair2.L`.
- **Left/Right**: Select the parent bone or a child bone. Multiple children are shown in a drop-down menu.
- **Top Left/Right**: Select bones that target or are targeted by this bone via constraints.
- **Bottom Left**: Select the start and end handles of Bendy Bones.
- **Bottom Right**: Open a pop-up menu to search for a bone by name.

## Bone Specials Pie (X)
Bone deletion and symmetry.
<img src="/media/addons/cloudrig/pie_bone_specials.png">

- **Toggle Armature X-Mirror**: Toggle symmetrical armature editing.
- **Toggle Pose X-Mirror**: Toggle symmetrical posing.
- **Delete**: Deletes selected bones and their drivers. Works in Pose Mode. Indicates X-Mirror status to prevent accidental deletions.
- **(Enhanced) Symmetrize**: Works in Pose Mode. Symmetrizes Actions of Action Constraints. Attempts to symmetrize drivers.

## Bone Parenting Pie (P)
Quickly parent and un-parent bones without having to enter Edit Mode.
<img src="/media/addons/cloudrig/pie_bone_parenting.png">

- **Clear Parent**: Clear the parent of selected bones.
- **Selected to Active**: Parent all selected bones to the active one.
- **Disconnect**: Disconnect a bone from its parent without un-parenting, allowing free translation.
- **Parent & Connect**: Parent selected bones to the active one, and connect them to the parent.
- **Active to All Selected**: Parent the active bone to all other selected bones equally using an [Armature Constraint](https://docs.blender.org/manual/en/latest/animation/constraints/relationship/armature.html).
<video src="/media/addons/cloudrig/parent_active_to_all_selected.mp4" controls></video>
- **Parent Object to All Selected**: Parent selected objects outside of the active armature equally among all selected bones using Armature Constraints.
<video src="/media/addons/cloudrig/parent_object_to_selected_bones.mp4" controls></video>


## Edit Custom Shapes Pie (Ctrl+Alt+E)
A comprehensive toolset to manage bone custom shapes.

<img src="/media/addons/cloudrig/pie_edit_widget.png">

- **Edit Transforms**: Quick access to custom shape transform properties.
- **Unassign Custom Shape**: Remove the custom shape from selected bones.
- **Assign Selected Object**: Set the selected mesh object as the custom shape of selected bones.
- **Reload Custom Shapes**: Reload widgets from the Widgets.blend file, discarding any modifications to them.
- **Edit Custom Shapes**: Enter mesh edit mode on the selected bones' widgets. Press Ctrl+Alt+E again to return to pose mode.
- **Select Custom Shape**: Assign a widget from a library to the selected bones. Local objects named "WGT-" will also be listed.
- **Duplicate & Edit Custom Shapes**: Duplicate selected bones' widgets before editing them. Handy when you want to edit only one usage of a widget, not all of them.
- **Copy to Selected**: Copy the custom shape and transforms from the active bone selected bones.

## Bone Collections pop-up (Shift+M)
A pop-up menu to can access bone collections without leaving the 3D View.
Available with the rig, even if a user doesn't have CloudRig installed.
<img src="/media/addons/cloudrig/bone_collections_popup.png">

## Quick Select (Shift+Alt+W)
Pops up a list of collections that were [marked](organizing-bones#selection-sets) to be included in this list. Clicking on one of them selects the bones within. Shift+Click extends the selection. Ctrl+Click symmetrizes the selection. Alt+Click deselects the collection's bones. 
Available with the rig, even if a user doesn't have CloudRig installed.
