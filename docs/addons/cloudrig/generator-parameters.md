# Generator Parameters
These parameters are found under Properties->Armature->CloudRig->Generation, and are the high level options used for generating a rig from a metarig.

<img src="/media/addons/cloudrig/generator_parameters.png" width=450>  

### Target Rig
The armature object used as the generation target. If empty, a new one will be created, and assigned here. You may rename the object.

### Widget Collection
The collection where rig widgets will be stored. This collection shouldn't contain anything else, since this is also used for detecting duplicate or unused widgets. If not specified, it will be created. You may rename the collection. If the refresh icon is enabled, widgets will be force-reloaded each time you regenerate.

### Ensure Root
Name of the root bone. All rigs must have a root bone, so if there is no bone with this name, it will be created. This bone should have the Bone Copy component assigned. Bones without parents will be automatically parented to this bone. Just like any other Bone Copy component, you may rename or customize this bone however you want. However, note that when you rename the bone, you will need to re-select it in this selection box.

### Properties Bone
Name of the default properties bone to create, when necessary. For example, for a limb rig with IK/FK sliders, those sliders are properties, which need to be stored somewhere. This setting specifies a bone name to create as fallback for that storage.

### Post-Generation Script
You may specify a text datablock stored in this .blend file, to be executed as a python script as one of the last steps of rig generation. You can use this to make hyper-specific tweaks to your rigs, or loop over all the bones and change some settings. You may leave it empty.

### Generate Action
This option is relevant when your rig contains FK Chain components. If this option is enabled, a test Action will be generated with keyframes defined by the generated rig's hierarchy and the parameters of each FK Chain component. The purpose of this Action is to help you in a common weight painting workflow, where the character is rotated on each of their joint to test deformations. If you want to make manual tweaks to this action, make sure to disable this option, so that your pose tweaks don't get overwritten when you regenerate the rig.