# Organizing Bones

In Blender, bones can be organized using [Bone Collections](https://docs.blender.org/manual/en/latest/animation/armatures/bones/bone_collections.html), or [Bone Selection Sets](https://docs.blender.org/manual/en/dev/addons/animation/bone_selection_sets.html).

## Bone Collections
CloudRig has a slightly tweaked Bone Collections UI from what you might be used to. This is shown in both the Sidebar (N panel) as well as under Properties->Armature->Bone Collections->CloudRig.
Besides the usual Hide/Solo buttons, there are a number of other things which can be shown or hidden using the Funnel icon:
- Number of selected/total bones in a collection (recursive).
- A [custom Select operator](#quick-select-shift-alt-w).
- [Quick Access toggle](#display-collections-as-selection-set) (circle icon).
- [Preserve On Regenerate](#protected-collections) toggle (shield icon).
- Reorder Collections (compass icon): This implements a best effort equivalent to Drag&Drop.

<img src="/media/addons/cloudrig/sidebar_collections.png" width=500>

You can also summon them using **Shift+M** on a CloudRig armature.

## Organizing Bones
If you want to customize which generated bones get placed in which bone collections, you can do this using Bone Sets.
Let's say we have a strand of hair rigged with the FK Chain component type, and we want the hair FK bones to go on a Hair collection that we created, not the "FK Controls" collection that it uses by default.

Organizing bones is considered an advanced feature, so enable **Advanced Mode**.
At the bottom of the parameters, you'll find the Bone Organization sub-panel:

<img src="/media/addons/cloudrig/bone_sets.png" width=500>

What you see listed here are the so-called "Bone Sets" of the active rig component. Every generated bone belongs to a Bone Set, which is hard-coded; Bone Sets cannot be re-named, added or removed. However, they allow you to customize certain visual and organizational properties of their corresponding bones:
- Which bone collections they are assigned to. This list can be reset with the refresh icon.
- What theme color the bones use.
- Wire width of the bone shapes.
The eye icon reveals additional Bone Sets, which you would rarely need to customize because they should be hidden from animators.

#### Bone Colors
You can also choose a color preset to assign. This preset will be converted to a custom color, meaning the rig will have the same colors regardless of the theme colors of whoever is using the rig.
Additionally, you can change Blender's default color presets to alternative presets in the preferences. I recommend the Lanaro preset.
<img src="/media/addons/cloudrig/bone_color_preset.png" width=800>

## Protected Collections
Protected Collections allow you to author and preserve collections on the generated rig across subsequent generations. They will not be removed, and the assigned bones will be preserved. Here's how to create a protected collection:
1. On the generated rig, enable the collection authoring UI:

    <img src="/media/addons/cloudrig/collections_extras.png" width=400>
1. Create your collections and assign bones as normal.
1. Mark the collection as protected, using the shield icon.

Note that this does **not** mean that you can now create arbitrary bones on the generated rig and expect them to stick around. For that, you still need to add bones in the metarig.

<img src="/media/addons/cloudrig/pasted_sel_sets.png" width=400>

## Selection Sets

#### Quick Select (Shift + Alt + W)
CloudRig hijacks the built-in shortcut for quick selecting Selection Sets. In addition to displaying Selection Sets, it can also display bone collections. The menu also has additional functionality when clicking an entry with modifier keys held:
- `Shift + Click`: Extend current selection.
- `Ctrl + Click`: Select the opposite side bones of the selection set.
- `Alt + Click`: Deselect the bones of the selection set.

These modifier keys can be combined, eg. `Ctrl + Alt + Click` will deselect the opposite side bones.

#### Display Collections as Selection Set
To have a bone collection appear in the Quick Select menu:

1. Enable collection editing (gear icon) as shown above.
1. Enable the circular icon button named "Quick Access" on a given collection.
1. That collection will now appear in the `Shift + Alt + W` menu.

<img src="/media/addons/cloudrig/collections_quick_select.png" width=300>

#### Convert Selection Set to Collection

Alternatively, you can also choose to convert your selection sets to collections:

1. Enable collection authoring UI **on the generated rig**, as mentioned above.
2. Copy Selection Sets to clipboard:

<img src="/media/addons/cloudrig/copy_sel_sets.png" width=400>

3. Paste Selection Sets as Collections **on the generated rig** via CloudRig:

<img src="/media/addons/cloudrig/paste_sel_sets.png" width=600>

4. Your selection sets are pasted as collections. The filled circle indicates that they were marked for Quick Access, and the shield icon indicates that they will be preserved when the rig is re-generated.

<img src="/media/addons/cloudrig/pasted_sel_sets.png" width=400>

5. You can now delete your selection sets.


## Bone Display Size
You might often encounter that the sizes of the bone shapes are too big or too small for some parts of your character. This can result in important controls being lost inside the character's body, or on the flipside, being oversized.

You can easily scale the generated bone display sizes using the [Scale Custom Shapes](workflow-enhancements#scale-custom-shapes-ctrl-shift-s) operator. You can also quickly affect translation and rotation using the [Edit Custom Shapes Pie](workflow-enhancements#edit-custom-shapes-pie-ctrl-alt-e).
