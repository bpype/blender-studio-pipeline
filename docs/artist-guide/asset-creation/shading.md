# Shading

::: warning
6 October 2023 - The content of this page is currently being edited/updated.
:::

## Requirements
* Reference (Concepts, Material)
* Base Models for tests/ Final Topology for task
* Topology requirements
* Required LOD

## Initial Choices

### Rendering Style Choice (PBR vs NPR)
* General shading model

### Engine Choice (Cycles vs Eevee)
* Eevee shading settings
* Cycles shader displacement
* Hybrid workflow

### Workflow Choice (Procedural vs Data) 
* Ups and Downs
* Texture specs and color management
* Semi-procedural

### Coordinate space (UV vs 3D)	
* Deformation
* Procedurals

## Workflow

### Data Layers

Besides texture maps, data that the shader can use can be written directly onto the geometry. This data thus depends highly on the topology and needs to be checked under topological changes.

#### UV Maps

There are [certain requirements for UV maps](https://studio.blender.org/tools/pipeline-overview/asset-creation/modeling#uv-unwrapping) that are used for image texture painting and baking. At the same time UV maps can be used as a way to align generic patterns (procedural or not) to the surface in a way that takes advantage of the topology.

#### Color Attributes

Since the geometry is typically lower resolution than the texture maps color attributes are more suited for colors that are soft and gradual, follow the topology or are meant as a preview for quick editing.  
It can also be useful to bake a preview of the color from the shader into a color attribute instead of a texture for viewport display.

#### Attributes

Beyond these specialized attribute types any generic type of data on the respective domains can be used for shading. With Blender's node tools this allows to make a name-based attribute system for the production that the tools can hook into in a convenient way for the editing process.  
Developing these tools should be part of the pre-production phase.


### Texture Baking
* HiRes to LowRes
* Procedural to texture
* Pattern baking

### Shading Data Generation

#### Geometry Data

Besides using the stored data from baked or painted maps and attributes there are several types of implicit data to be used in the shader, such as for example the curve intercept or the pointiness of the mesh. This type of data is not stored on the geometry but implicitly derived and can change depending on outside parameters like the deformation.

#### Geometry Nodes

On top of the available shading information it can be incredibly useful to generate additional data for shading on the fly using geometry nodes. Instead of writing information as static data it can be generated depending on the context. For example to generate a mask based on the proximity of a mesh to another. This data can be calculated with Geometry Nodes and stored as an attribute that can be used in the shader.
([Example](https://youtu.be/1nvzwhbL-k0?si=BY-X-1Xe9D4FyySj&t=458))

### Camera Based Effects

### Node Group Structure (modularity)

#### Main shader
A lot of the time it is useful to build the shader network in such a modular way that large parts can be shared between assets of the entire production. Breaking down the base of all shaders into just a few main shaders makes it very easy to make adjustments on a global scale.

#### Utility node groups
Project specific, as well as generic node-setups that are reused throughout the production should be isolated into utility nodegroups and shared. That was adding functionality, making tweaks or improving the behavior propagates whereever they are used. 

---

All these nodegroups should sit in their respective library files and get linked into the asset files where they can be integrated into a local shading network.

Iterating over these library node-groups comes with the responsibility to make sure that there are no regressional changes. New nodegroup inputs should be set up in a way that the default means no visible change. Otherwise this can have consequences for the assets that use these libraries.

### External Control (Custom Properties)
