---
outline: deep
---

# Rigging

Our rigging workflow for characters as well as complex props, is based on procedurally generating control rigs, then manually weight painting and authoring corrective shape keys. We've built some custom tools to make these processes more efficient, foolproof and as iterative as possible. We try to tailor each rig to the needs of the animators on any given production.

## Rig Generation with CloudRig
A character model may be handed off to rigging either in final, production-ready retopo phase, or in a messy automatic retopo state for the sake of layout or previz. In both cases, generating the control rig is the first step in rigging it. The control rig is generated using CloudRig, our rig generation tool. Features are tweaked and added according to the needs of each production.

* [CloudRig on the Extensions Platform](https://extensions.blender.org/add-ons/cloudrig/)  
* [CloudRig Wiki](https://studio.blender.org/tools/addons/cloudrig/introduction)   

The facial rigging is usually done with CloudRig's [Action set-up system](https://studio.blender.org/training/blender-studio-rigging-tools/actions/).

## Weight Painting
Weight painting character meshes to the generated rig has so far happened simply manually, as there hasn't been a need to mass-produce characters with high quality deformation. Still, the **Easy Weight** add-on helps to make this manual weight painting workflow efficient with some custom UI, and less error-prone with a rogue weight checking system. There is also a short tutorial series about my weight painting workflow, which also includes a section about this add-on specifically.

* [EasyWeight on the Extensions Platform](https://extensions.blender.org/add-ons/easyweight/)  
* [EasyWeight Wiki](https://studio.blender.org/tools/addons/easy_weight)
* [2020 Weight Painting Course](https://studio.blender.org/training/weight-painting/)

## Corrective Shape Keys
After creating the control rig and weighting the mesh to its deform bones, we want to create shape keys to improve the quality of the deformations, as a final level of polish.
Normally, the control rig and the weight painting has to be finalized before corrective shape keys can be authored, but our workflow with the **Pose Shape Keys** add-on allows us to make changes to the rig and the weights while preserving the resulting corrective shapes. This lets us work in a less restricted way when it comes to iteration.

* [Pose Shape Keys on the Extensions Platform](https://extensions.blender.org/add-ons/pose-shape-keys/)  
* [Pose Shape Keys Tutorial Video](https://studio.blender.org/training/blender-studio-rigging-tools/pose-shape-keys/)

## Examples
* [Snow Character Rigging Live Streams (20 hours)](https://www.youtube.com/watch?v=SB3qIbwvq8Y&list=PLav47HAVZMjnA3P7yQvneyQPiVxZ6erFS)
- [Mikassa Character Rigging Live Streams (Unfinished)](https://www.youtube.com/watch?v=nJQbMqbWeuc&list=PLav47HAVZMjmQNihV3a22ztg0ielYFEas&index=2)
* [Blender Conference 2022 Live Character Rigging (50 minutes)](https://conference.blender.org/2022/presentations/1723/)
* [Example Character Rigs](https://studio.blender.org/characters/) (Everything up until Lunte)