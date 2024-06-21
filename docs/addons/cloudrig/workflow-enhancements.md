# Workflow Enhancements
CloudRig ships with various small quality of life features. These usually have a default hotkey. If these ever get in the way for you, you can easily re-bind or disable them in the preferences.

<img src="/media/addons/cloudrig/hotkeys_ui.png">

## Better Duplicate & Extrude
-  Extruding (**E**) or duplicating (**Shift+D**) bones increments existing numbers in the bone name:
- `Bone1` becomes `Bone2` rather than `Bone1.001`.
- Works with symmetry. If `Bone2` already exists, it will just jump to `Bone3`, and so on.
- Shift+D duplicates bone and constraint drivers.

<video src="/media/addons/cloudrig/better_duplicate_extrude.mp4" controls></video>

## Bone Selection Pie (Alt+D)
A pie menu bound to **Alt+D** lets you select bones related to the active bone.
<img src="/media/addons/cloudrig/pie_bone_find.png">

- Up/Down: A bone with a higher/lower number in the name than current, letting you jump from `Hair1.L` to `Hair2.L`, even if those bones have nothing to do with each other.
- Left/Right: The parent bone, or child bone. If there are multiple children, it's a drop-down menu.
- Top Left/Right: Bones who target the active bone with any of their constraints, and bones targeted by this bone by any constraints.
- Bottom left: The start and end handles of Bendy Bones.
- Bottom right: A pop-up menu to search a bone by name.

## Bone Specials Pie (X)
A pie menu bound to the **X** key for deletion and symmetry.
<img src="/media/addons/cloudrig/pie_bone_specials.png">
- **Toggle Armature X-Mirror**: Whether armature editing operations affect both sides.
- **Toggle Pose X-Mirror**: Whether transforming bones affects both sides.
- **Delete**: Deletes the selected bones. Even in Pose Mode. Also deletes drivers of the deleted bones. The button indicates when Armature X-Mirror is on, to avoid accidental deletions.
- **Symmetrize**: Blender's Symmetrize operator with some changes: It's made available in Pose Mode, it also symmetrizes Actions when there are Action Constraints present, and it also tries to symmetrize drivers.

## Bone Parenting Pie (P)
A pie menu bound to the **P** key lets you quickly parent and un-parent bones without having to enter Edit Mode.
<img src="/media/addons/cloudrig/pie_bone_parenting.png">
- **Clear Parent**: Clear the parent of selected bones.
- **Selected to Active**: Parent all selected bones to the active one.
- **Disconnect**: Disconnect a bone from its parent, without un-parenting it, so the bone can be translated freely.
- **Parent & Connect**: Parent selected bones to the active one, and connect them to the parent.
- **Active to All Selected**: Parent the active bone to all other selected bones equally using an [Armature Constraint](https://docs.blender.org/manual/en/latest/animation/constraints/relationship/armature.html).
<video src="/media/addons/cloudrig/parent_active_to_all_selected.mp4" controls></video>
- **Parent Object to All Selected**: Parent selected objects outside of the active armature equally among all selected bones using Armature Constraints.
<video src="/media/addons/cloudrig/parent_object_to_selected_bones.mp4" controls></video>

## Bone Collections pop-up (Shift+M)
A pop-up menu so you can access bone collections without leaving the 3D View. There is also a [Quick Select](organizing-bones#selection-sets) menu on **Shift+Alt+W** for collections that are marked to be included in that menu. Click the link to learn more.
<img src="/media/addons/cloudrig/bone_collections_popup.png">
