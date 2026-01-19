# Generator Parameters
These parameters are found under Properties->Armature->CloudRig->Generation, and are the high level options used for generating a rig from a metarig.

<img src="/media/addons/cloudrig/generator_parameters.png" width=450>  

### Target Rig
The armature object used as the generation target. If empty, a new one will be created, and assigned here. You may rename the object.

### Post-Generation Script
You may specify a text datablock stored in this .blend file, to be executed as a python script as one of the last steps of rig generation. You can use this to make hyper-specific tweaks to your rigs, or loop over all the bones and change some settings. You may leave it empty.

### Generate Action
This option only appears when your metarig contains [FK Chain](cloudrig-types#chain-fk) components. If this option is enabled, a test Action will be generated with keyframes defined by the generated rig's hierarchy and the parameters of each FK Chain component. The purpose of this Action is to help you in a common weight painting workflow, where the character is rotated on each of their joints to test deformations. If you want to make manual tweaks to this action, make sure to disable this option, so that your keyframe tweaks don't get overwritten when you regenerate the rig.

### Root Bone
Name of the root bone. While optional, some rig features such as FK Hinge require the rig to have a root bone. This is not a bone selector, because this option will actually affect the metarig, by creating a bone with the specified name. After that, you're free to fully customize this root bone, with two caveats: 
1) If you want to rename the bone, you also have to change the name in this input box. 
2) You cannot parent this bone to another bone. The parenting will be cleared. This bone should be the true root.

### Properties Bone
Name of the default properties bone to create, when necessary. For example, for a limb rig with IK/FK sliders, those sliders are properties, which need to be stored somewhere. This setting specifies a bone name to create as fallback for that storage. If no properties are needed by the rig, this bone won't be created.

# Custom Shapes

### Collection
The collection where rig widgets will be stored. This collection shouldn't contain anything else, since this is also used for detecting duplicate or unused widgets. If not specified, it will be created. You may rename the collection. If the refresh icon is enabled, widgets will be force-reloaded each time you regenerate.

### Preserve Properties
When enabled, custom shape properties (like translation, rotation, scale, wire width, etc) will be preserved when re-generating the rig.
#### With Shapes
When disabled, only the properties or custom shapes will be preserved on the generated rig, but the shape object assignments will be reset.


# Rig Components

This panel shows a hierarchy of your rig components. Selecting an entry will select the corresponding bone. The list also defines the generation order, which can matter in some cases. You can re-order elements at the same hierarchy depth (ie. siblings). The hierarchy itself is defined by bone parenting in the metarig. You can also disable elements, which will cause them and their children to be ignored by the generator.

Adding a new entry means assigning a component type to a bone. It's the same as if you did that on the Bone->CloudRig Component panel.
Removing an entry means un-assigning the component type from the given bone.

# Actions
This panel lets you configure automated Action constraint set-ups, which is incredibly useful for bone-based face rigging. See the [Actions](actions) page for more details.

# Generation Log
This panel warns you of things in your rig that are likely to be unintentional. Of course it can't catch everything, and could even have some false positives sometimes (hopefully very rarely). See the [Troubleshooting](troubleshooting) page for more info.
