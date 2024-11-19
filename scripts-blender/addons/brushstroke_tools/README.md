# Brushstroke Tools

Set of tools for a painterly brushstroke stylization workflow of 3D assets developed by the Blender Studio

You can find a guided workshop on how to use the tools to create a painterly scene go here:
https://studio.blender.org/training/stylized-rendering-with-brushstrokes/

# Fundamental Concept

The Brushstroke Tools add-on provides a convenient interface, as well as different operators to create, manage and modify 3D brushstroke geometry that is based on the procedural generation of textured mesh strips based on curve geometry using Geometry Nodes.

All brushstroke layers created with the add-on are associated to a surface mesh object.

There are two types of brushstroke layers to provide different modes of interaction:
- Fill
- Draw

One key paradigm of its implementation is that the surface object does not have to be local data for it to work.

# User Interface

The user interface for the addon can be found in the properties panel on the right side of the 3D viewport in the `Brushstroke  Tools` category.

## Context Brushstroke Layers

All associated brushstroke layers that belong to the same brushstroke object show up in a list based on the active context. There are different operators to make changes the active brushstroke layer to the right of the list.

## Brushstroke Layer Properties

Below the list of context brushstroke layers you can find the properties of the active brushstroke layer. The properties are split up into three tabs: Shape, material and settings. 

In the header of the `Brushstroke Settings` panel there is a toggle to enable UI options. This temporarily reveals more functionality of the properties and allows to modify the interface.

### Shape

The shape panel presents you with a simplified version of the modifier interface of the active brushstroke layer. Here you can adjust procedural parameters of the setup on a brushstroke layer level.

### Material

The material panel presents you with a simplified user interface for the brushstroke material. You can select and edit the material that the active brushstroke layer uses and modify it from here.

#### Material Properties

These are the base settings of the material to define different PBR properties.

#### Brush Style

The brush style defines which texture is mapped to the individual brushstrokes. There is a selection of oil painting brushes based on real-life scans. The `Default` brush style is a procedural texture that comes with a set of input settings to modify its look.

The available brush styles are stored in the user preferences and can be reloaded with the refresh button.

Below the brush style selection is a curve to map the texture to the brush opacity for more control.

#### Effects

Adding more effects is a matter of inserting more nodes in the node-tree and the interface adjusts dynamically.

### Settings

The settings panel provides a list of additional settings for the active brushstroke layer.

#### Deforming Surface

Controls the stable deformation functionality of the Brushstroke Tools add-on for the brushstroke layer.  
This toggle can also be used when the surface is linked data. Keep in mind that the `add_rest_position_attribute` flag needs to be set on the object for this to work.

#### Animated Strokes (experimental)

Enables the fuctionality to animated the drawn brushstrokes based on the frame they were drawn(similar to Grease Pencil). Turn on auto-keying for this to take effect.

#### Shadow Visibility

Controls the shadow visibility of the brushstrokes layer.

# User Preferences

In the user preferences for the Brushstroke Tools addon you can modify the way resource assets are loaded into the file. Be catious of linking to the default directory though, since links can easily break when moving the file, or sharing it with others.  
When changing the resource directory path, you need to provide the resource files in the directory. Use the operator to do so and copy the resource files from the add-on directory to your custom directory.

## Brush Styles

Here you see a list of all the available brush styles that have been loaded by the add-on.

# Add-on Customization

When choosing an external path for the add-on resources in the user preferences all resources can be customized in place. Currently there are no mechanisms in place to make customization more convenient, so do this at your own risk.

## Additional Brush Styles

There will be more brush style packs available to achieve different styles in the future. Adding more brush styles is a matter of duplicating the node-group asset that defines one in the resource directory and changing its referenced texture and parameters.  
Brush styles can be spread out over multiple files in the resource directory. They are identified via the node-group name.

# FAQ
- Why does the fill layer not react to me drawing the flow curves?
    - Most likely you don't have a valid UV map on your surface mesh. Try doing a simple Auto-UV unwrap and adding the fill layer again.
- Why is the fill layer reacting badly and inaccurately to the drawn flow curves?
    - Most likely your surface mesh has a low resolution. The flow requires a certain mesh resolution to be interpolated properly.
- I am using Cycles for rendering and there are black spots all over the place.
    - This method of stylized rendering makes heavy use of overlapping transparent planes. This means Cycles need to do a high number of transparent bounces for the image to resolve nicely during rendering. To help with this setting you can use the `Render Setup` operator in the `Advanced` panel.
- I'm experiencing poor performance. How can this be avoided?
    - This method is computationally intensive and relies on high level hardware to run smoothly. But there are a few things that can be done to avoid low perfromance.
    - If it's about tweaking shape parameters, then it doesn't have to do with the rendering, but is about the geometry evaluation and it just helps to keep the amount of brushstrokes and their resolution low, to reduce the amount of geometry that needs to be processed.
    - If just in the static case, orbiting the camera is slow, then it has to do with Eevee and keeping the amount of pixels that need to be rendered low helps most. For example you can change the Pixel Size in the `Performance` - `Viewport` settings. Samples don't help with interaction, since during that only 1 sample is rendered anyways.