# Rig UI

Every rig generated with CloudRig will create a Text datablock called `cloudrig.py` which is a chunky piece of code responsible for the CloudRig sidebar panel. This allows this panel to work even if the CloudRig add-on itself isn't installed, which makes it easy to distribute rigs without hassle. Do note though, that while the script auto-executes when opening a .blend file that contains it, it does not auto-execute when linking or appending, so after those you need to save and reload your .blend.

This page, useful for both animators and riggers, describes the features included in the "CloudRig" Sidebar (N) panel. Keep in mind that the contents are procedurally generated based on the metarig, so your UI will look different from the screenshots.

## Settings
This panel contains a couple of operators, and houses built-in CloudRig features like IK/FK switching and snapping. It can also contain arbitrary properties and operators as defined by the rigger using the "UI Edit Mode" functionality, see below.

<img src="/media/addons/cloudrig/sidebar_settings.png" width=400>

#### Keyframe All Settings
Inserts a keyframe on the current frame for all (except bone collection) properties drawn anywhere in the Settings panel and all of its subpanels.

#### Reset Armature
<img src="/media/addons/cloudrig/reset_armature.png" width=400>
Powerful reset operator with a pop-up to specify what you want to reset:

- Unassign Action: Only appears if the armature has an Action assigned.
- Unhide Bones: Only appears if any bones are hidden. Unhides them all.
- Viewport Display: If enabled, resets the rig object's "Show Names", "Show Axes", and "In Front" options.
- Selected Only: Only appears if any bones are selected. If enabled, only selected bones will be affected by subsequent settings.
- Transforms: If enabled, resets Location/Rotatoin/Scale of bones.
- Custom Properties: If enabled, resets custom properties of bones to their default values.

#### UI Edit Mode
This option is aimed at riggers; It is only available on Metarigs, and only with the add-on installed. It allows the rigger to create their own interface for custom properties, or in fact any properties, nested into panels, labels, and rows. To learn how to use this feature, see the [Properties UI](properties-ui) page.

#### IK/FK Switch
If your rig containts any IK/FK components, their IK/FK switch properties will appear here.  
While you can simply use the slider to switch between FK and IK control schemes, this will not automatically preserve the existing pose.  
Next to each slider (that supports it), is a **Snap & Bake** operator. This lets you snap the bones of the IK controls to the FK controls or vice versa.  This will always insert a keyframe on all transforms of the affected bones, as well as the slider.  
You can also do this over a frame range by enabling the **Bake** option.

<img src="/media/addons/cloudrig/snap_bake_popup.jpg" width=400>

#### IK

<img src="/media/addons/cloudrig/sidebar_ik_settings.png" width=400>

May contain various IK related properties. They will come with the same Snap & Bake operator as described above, when possible. Common ones are:
- Spine Squash: Squashing factor of the Cartoon Spine rig.
- IK Stretch: Whether limbs are allowed to stretch while in IK mode.
- IK Pole Follow: Whether the IK poles should be parented to the IK master controls.
- Parent Switching: Select the parent of the IK master controls.

#### FK
Mostly houses the FK Hinge sliders, which when enabled cause an FK chain to not inherit rotation from its parent.

## Hotkeys

<img src="/media/addons/cloudrig/hotkeys_no_addon.png" width=400>

When CloudRig is not installed, this panel will show a limited set of hotkeys available for animators. If CloudRig is installed, this will show the same hotkey list as in the add-on preferences.

## Bone Collections
This shows a slightly tweaked version of Blender's built-in Bone Collections list. For the extra capabilities, see [Organizing Bones](organizing-bones#bone-collections).