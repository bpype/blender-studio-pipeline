# Modeling

::: warning Work in Progress
October 17th 2023 - The content of this page is currently being edited/updated.
:::

## **General**

* The **approved concept design** is required at this point. But overlap in these stages is possible.

* The important difference for this page is the focus on **delivering a production ready model** based on an approved design.


## Organic

There needs to be a handover of design material:

* Concept Design. Typically sculpted ([T-Pose](https://studio.blender.org/films/sprite-fright/39362c69939a56/?asset=4319) & optional [Hero Pose](https://studio.blender.org/training/stylized-character-workflow/6-pose-test/))
* [Deformation Tests](https://studio.blender.org/films/sprite-fright/39362c69939a56/?asset=4356) (Like [expressions](https://studio.blender.org/films/sprite-fright/character_lineup/?asset=4340) & [poses](https://studio.blender.org/films/sprite-fright/sprite/?asset=4243))
* [Style guides & limitations](https://studio.blender.org/films/sprite-fright/3993b3b741b636/?asset=4910)

**The outcome usually is a final topology**. More can be added if required:

* Basic UV maps
* Animation Shape Keys
* Baked textures from sculpted details
* Pivot Point Markers (via empty objects)
* Helper Shape Keys (Closed eyes, open mouth)
* Hero Pose Shape Keys
* Cleanup (Applied Transforms, manifold check, naming, dummy materials)

### Topology

**The goal is to create an optimized topology** for next asset creation tasks (shading, texturing, rigging & animation). \
**A full UV unwrap** is also added at this stage and the modeling is done with them in mind.

Typically we do a retopology since the shape and design was already developed via sculpting and loose modeling. \
For more, read the [full explanation of our workflow and theory](https://studio.blender.org/blog/live-retopology-at-bcon22/).

We also have a [deeper look into the workflow for stylized characters \
](https://studio.blender.org/training/stylized-character-workflow/chapter/5d384edea5b8f5c2c32c8507/)as well as [realistic characters](https://studio.blender.org/training/realistic-human-research/chapter/retopology-layering/). \
This information can be extrapolated to other types of assets.

* [Retopology in Blender](https://studio.blender.org/blog/live-retopology-at-bcon22/)
* [Retopology & Layers from Charge](https://studio.blender.org/training/realistic-human-research/chapter/retopology-layering/)
* [Retopology Course based on Spring/Coffee Run](https://studio.blender.org/training/stylized-character-workflow/chapter/5d384edea5b8f5c2c32c8507/)
* [Retopology Cheat Sheets](https://studio.blender.org/training/stylized-character-workflow/chapter/5e5fea8470bde75aac156718/)

### UV Unwrapping

**The topology heavily influences where UV seams can be placed.** Especially for clothing this is vital to keep in mind.

The focus is mostly on **minimized stretching and texel density**. \
UDIMs are great for this to order uv islands by needed detail level. \
Areas that are closer to the camera are given higher texture resolution, \
while covered or hidden parts could be heavily reduced in resolution or even stripped of textures.

**Pattern aligned UV maps** are useful. \
They align texture patterns better on surfaces like for clothing. \
Add them as secondary UV maps, as they can have more visible stretching.


* [UV Mapping Live Streams for Snow](https://www.youtube.com/watch?v=_LI28r-Nk5g&list=PLav47HAVZMjl5VQRoVPd0481fsJNNQi9J&index=9&ab_channel=BlenderStudio)

### Sculpted Details & Animation Shapes

Existing sculpted surface details are ideally reprojected onto the subdivided retopology and refined for production. \
For this the **multiresolution modifier** is used and the final topology should be made of **relatively evenly distributed quads for the best results**.

For the use of sculpted animation shapes and detailed sculpted layers we use Shape Keys extensively as well as the \
[Sculpt Layers](https://blenderartists.org/t/sculpt-layers-addon/1288145) addon when needed. \
Also see the use of [Corrective Shape Keys](https://hackmd.io/VZ4wN5VmQBS5w9MLFolD3A) for already rigged characters.

* [Layered Sculpting from Charge](https://studio.blender.org/training/realistic-human-research/chapter/shapes-and-baking/)
* [Manual Clothing Dynamics from Charge](https://studio.blender.org/training/realistic-human-research/chapter/clothing-shapes-rotation/)
* [Baking Sculpted Details from Charge](https://studio.blender.org/training/realistic-human-research/chapter/baking-and-exporting/)

#### Helper Shape Keys

For handover to the next steps it’s good to add some shape keys.

For example shapes to **open/close the eyes and mouth**. If multiple objects are affected, the shape keys can be driven by a single property. \
These shape keys are extremely helpful for texturing and rigging.

For previz purposes a **full hero pose** is also useful. This way the texturing, shading and grooming could be rendered in an appealing pose instead of overly relying on the default T-Pose.


## Static/Hard-Surface

### Reference

For simple “static” assets it helps to use webshops or manufacturer websites to view specific dimensions of an object. These often come with many reference images and videos. The best way to gather reference is by physically holding it and being able to measure the object.

Creating hard-surface assets often comes with mechanical or moving parts, making the modeling more elaborate. With a specific design or concept, it helps to create a collage of images to work more accurately when parts move and slide in a believable manner.

These may include videos, photos, separate dimensions, technical diagrams, and blueprints (multiple angles) to help understand the asset better. When using blueprints or diagrams make sure the vertical and horizontal lines are perfectly straight before modeling. 

### Setup

Starting with a cube to only show “Wire”, match the rough dimensions to maintain consistent scale and create a visual guide with the help of imported reference images or dimensions. Linking existing assets or characters to the scene is another useful way to match scale and proportions. For example, the hands of a character that will use the prop.

### Blocking

Starting with simple shapes and topology to block a basic version of the asset. Use modifiers to increase the speed and flexibility which is usually preferred at this stage for changes later.

Common modifiers used are:

* If the asset is symmetrical use the Mirror modifier
* Using the Solidify modifier to add thickness to a planar surface
* The Bevel modifier adds a chamfer to the edges. It is common in conjunction with the solidify modifier
* Array modifier is useful to repeat multiple instances of the same object in multiple directions or based on another object to repeat the object radially
* Edge Split modifier can be used to create non-destructive part lines using Mark Sharp in edit mode, in conjunction with the Solidify and Bevel modifiers
* Booleans to quickly shape an object without managing topology too much
* Curve modifier has a lot of uses combined with the array modifier to deform the mesh

Testing movement is achievable in different ways without the use of an armature. The way the asset is split into different collections can be important with some of these methods:


* Using Empty objects where the various (instanced) collections are parented to. Using instances of the collections is more flexible to avoid unwanted changes in topology
* Using shapekeys to animate more simplified movement
* Using the 3D cursor with basic object parenting to manipulate simplified set-ups

Creating a simplified animated version is a good method to improve the model and design. This new information feeds back into modeling and changes can be made easily and viewed again with the instanced collections.

### Refinement

At this point it is wise to strategically apply modifiers to remain flexible enough before fully committing. Retopology might be necessary to improve the surface curvature and clean-up any previous booleans.

Adding smaller details like screws, cables, insets and more to increase believability. Adding Subdivision Surface modifier, creasing and manual bevels for smoothing and control over edge sharpness. Inspecting the model from different angles helps determine if bigger shapes aren’t lost and to avoid errors. 


### Sets

::: warning Work in Progress
October 17th 2023 - The content of this page is currently being edited/updated.
:::


## Delivery

Any asset needs refinements and additions to make sure they are ready to hand over:

* **Check for ‘doubles’** or vertices that are too close and merge them (Use ‘Merge by Distance’)
* **Consistent direction of normals** (‘Face Orientation’ overlay and ‘Recalculate Normals’)
* **Use smooth shading on objects**
* **Apply the object scale** and if needed also the location & rotation
* **Apply most modifiers**. Any that are best to have static in the model. 
* **Double check UV Maps**. Any cleanup modeling could affect them negatively.
* **Logical naming and sorting** into collections
* **Add placeholder materials** with basic viewport colors. Very helpful for handover to initial shading and animation 
* **Delete unused attributes** and any data that isn’t needed for the handover
* **Add Empty objects to mark pivot points** of deformations. These are helpful helper objects especially if the rotation points on joints are not obvious