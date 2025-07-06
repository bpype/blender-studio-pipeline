# Organizing Bones

In Blender, bones can be organized using [Bone Collections](https://docs.blender.org/manual/en/latest/animation/armatures/bones/bone_collections.html), or [Bone Selection Sets](https://docs.blender.org/manual/en/dev/addons/animation/bone_selection_sets.html), if you use that addon.

## Bone Collections
There are a couple of quick ways to access the Bone Collections UI in CloudRig; You can find them under **Sidebar(N panel)->CloudRig->Bone Collections**:

<img src="/media/addons/cloudrig/sidebar_collections.png" width=500>

You can also summon them using Shift+M on a CloudRig armature.

## Organizing Bones
If you want to customize which generated bones get placed in which bone collections, you can do this using Bone Sets.
Let's say we have a strand of hair rigged with the FK Chain component type, and we want the hair FK bones to go on a Hair collection that we created, not the "FK Controls" collection that it uses by default.

Organizing bones is considered an advanced feature, so enable **Advanced Mode**.
At the bottom of the parameters, you'll find the Bone Organization sub-panel:

<img src="/media/addons/cloudrig/bone_sets.png" width=500>

And as you can see, all we have to do is assign our Hair collection as one of the collections that the FK Controls of this component should be assigned to. You can assign them to as many collections as you wish. 

#### Bone Colors
You can also choose a color preset to assign. This preset will be converted to a custom color, meaning your personal color presets will propagate to whoever uses your rig. This ensures the rig looks the same way, no matter who's using it.
Additionally, you can change Blender's default color presets to CloudRig's recommended ones in the preferences, using this button:  
<img src="/media/addons/cloudrig/bone_color_preset.png" width=800>

## Protected Collections
You also have the ability to organize collections as you would with a normal armature, except you need to let CloudRig know which collections you don't want to be touched by the generation process. To do that, you first need to enable the collection authoring UI:

<img src="/media/addons/cloudrig/collections_extras.png" width=400>

Then you can create your collections and assign bones as you would on any armature. Then you need to mark the collection as protected, using the shield icon. These collection, and which bones are assigned to them, will be fully preserved when you regenerate the rig.

Note that this does **not** mean that you can now create arbitrary bones on the generated rig and expect them to stick around. The only way to do that is to add [Bone Copy](cloudrig-types#bone-copy) components in the MetaRig.

<img src="/media/addons/cloudrig/pasted_sel_sets.png" width=400>

## Selection Sets
Instead of having to use multiple systems to organize your bones, CloudRig implements all the features of SelectionSets.
To start, you can easily convert your selection sets to collections:

1. Enable collection authoring UI **on the generated rig**, as mentioned above.
2. Copy Selection Sets to clipboard as you normally would:

<img src="/media/addons/cloudrig/copy_sel_sets.png" width=400>

3. Paste Selection Sets as Collections **on the generated rig** via CloudRig:

<img src="/media/addons/cloudrig/paste_sel_sets.png" width=600>

4. Your selection sets are pasted. The filled circle indicates that they were marked for Quick Access, and the shield indicates that they will be preserved when the rig is re-generated.

<img src="/media/addons/cloudrig/pasted_sel_sets.png" width=400>

## Quick Select
Collections marked with the circle will be included in the Quick Select menu, which is bound to **Shift Alt W** by default:

<img src="/media/addons/cloudrig/collections_quick_select.png" width=300>


## Bone Display Size
You might often encounter that the sizes of the bone shapes are too big or too small for some parts of your character. This can result in an eye sore, or worse, important controls only being visible with Bone X-Ray. For this reason, all CloudRig components' bone shapes will scale according to the BBone scale of the bone in the metarig. You can find the Display Size X/Z properties in the Bendy Bone panel of the Properties Editor, or use the well-hidden Bone Envelope tool in the toolbar to change the bone size. In both cases, your armature's bone display type needs to be set to BBone. This will not affect any behaviour on the rig, it's purely for visual aid.

*Here I increase the BBone scale, then re-generate the rig, to make sure the FK controls are bigger than the mesh.*
<img src="/media/addons/cloudrig/bbone_scale.gif" width=600>
