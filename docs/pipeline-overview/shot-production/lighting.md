# Lighting

::: warning
October 6th 2023 - The content of this page is currently being edited/updated.
:::

## Requirements

We can start lighting a shot as soon as there is a first blocking pass available. Further, all assets within the framing of the shot should have at least a basic shading pass to give us a rough estimate. It can be helpful to have a color script of the whole film at hand, as well as a color key or a set of lighting guidelines to keep the continuity of the movie in place. Often we would already have made a simple test setup in look development that can be used as base for the shot.

## Render engine choice

Which renderer we use depends very much on the style of the production. That choice factors into the lighting workflow and how assets are authored and shaded, so it's important to select an engine already in pre-production.

## Lighting workflow

The workflow is highly dependent on the production requirements and its art style. In general, we try to identify the key shots in a sequence first and set up their lighting first. When there is an establishing shot or a wide angle view of the scene, we derive close ups and inserts from that as a starting point.

## Eye highlights

A large part of lighting is making characters appealing. Eye highlights are an important aspect of that appeal, so extra care is given to them. We used a variety of different approaches for eye highlights in the past, each of them is perfectly valid so the technique is dependent on the art style of the production. For example, “Spring” and “Agent 327: Operation Barbershop” both use the real reflections of the scene's lights plus additional hand-placed highlight lights. “Sprite Fright”, being more cartoony in style, utilizes eye highlights which are placed by the animators using the character rig.


## Maintaining Continuity

There are different methods for maintaining the continuity between each shot in a film. They all need to link up to the adjacent shots in the sequence in terms of light intensity, color and style. We use different techniques for that.

In cases where there is a strong emphasis on spatial continuity (like a dialogue scene, or a fast action set piece) we have to ensure that the light direction is consistent across a sequence. In outdoor shots it can be helpful to draw a top-down view of the scene to discuss the camera angles and general light direction.
In “Sprite Fright” we used a simple [light direction chart](https://studio.blender.org/films/sprite-fright/391c5d112594c2/?asset=5023) which showed colored arrows on a grid of viewport rendered shots to indicate the direction of each shot's key light. The same chart was also used by the animators to match the (cheated) eye highlights to the actual lighting of each shot. Whenever the light direction was changed, the corresponding shot was updated in the chart and the animator knew how to re-align the eye highlight.

It is vital to match the color values for each type of light across shots. In recent productions we tried to simplify the light types down to four: Key, key-soft, fill and rim. Each type had a corresponding RGB value for each scene. We store these values in a library file. For Cycles they can simply be added to a node group which can be linked into each shot. Thus, whenever the value in the central file changes, all the shots automatically get the update and simply have to be re-rendered.


## File hierarchy

The lighting file is responsible for outputting the final rendered frames of a shot, either to be used as-is in the edit or as an image sequence in the compositing step. The lighting file therefore links in the output collection from the animation file, as well as from the corresponding effects files. When the lighting gets approved and a shot is marked for final rendering, the rendering quality settings should be changed from preview quality to the final output configuration before the shot gets submitted to the farm.

## Collection Layout

Lights and all other objects necessary to illuminate the shot are placed in a separate collection called *{shot number}.lighting*. Often there can be several additional elements in addition to the anim and effects data: Set extensions, matte paintings, high res assets, shot specific dressing. 

## Syncing updates from animation

Whenever the animator updates their file, the changes automatically trickle down to the lighting file. 
How much to get from animation vs. additional geo (set extensions)
Modifying linked data 
Since a big part of the shot comes from the animation file, we often need to adjust the data that flows into the lighting file. This can be done in a variety of ways and depends on the project's setup and complexity.

The most basic level of control is changing visibility: Often a specific asset is made to be fast in animation playback, but we might want to see a more complex representation of it in the lighting file. In that case we want to split the asset's geometry into several different representations which could be controlled by switches in the rig or are simply placed in different collections.
The best way to hide a linked collection using the exclusion function in the Outliner. Exclusion is stored in the current (local) ViewLayer; unlike render and viewport visibility, which are stored on the collection and can not be written to a linked data block (unless the data is changed with library overrides). It's important to keep in mind that view and render visibility are directly read from the source file, so changing it in the asset (or the animation file) will directly affect the lighting file.

In the last productions we tried to move away from direct visibility control and opted for rig switches based on geometry nodes. But to change those, we still need to modify values on linked data. Using Blender's Python API we can modify pretty much any value, local or linked. We can write a set of instructions into a text data block (just make sure its name ends in .py) and make it auto-execute when the file is loaded. This is very powerful because we can even use loops to iterate through a large set of values. The downside is that changing values is pretty cumbersome, and we need to execute the script every time a value has been changed. 

To automate the creation of RNA overrides we wrote the [Lighting Overrider](https://studio.blender.org/pipeline/addons/lighting_overrider) add-on. It automates the creation of the text data block and makes tweaking values much easier. Just hover over any value in the UI and press “O”, then choose the desired value and press “OK”. 

A significant drawback of both methods is that animation is very hard to do. A hacky way is to create a driver on a linked RNA value with python and hook it up to a local ID property on a dummy object. This method was used on “Sprite Fright” to animate Ellie's bruising appearing in a shot. However, the easier method is to dive into the animation file and animate the value locally. Just make sure to communicate this with the animator of the shot.

## Debugging motion blur issues

Motion blur issues can happen quickly if there is a constraint switch in animation. For example, when a character picks up a prop from a table, the parenting hierarchy has to change over the course of a few frames. If done wrong, this can result in long motion blur streaks where the asset can travel between its rest position and the final position in the hand of the character. Often a solution can be to execute those constraint switches only in Constant keyframe interpolation, but sometimes this can also cause other issues. 
The most visual way - apart from rendering the frames - to debug this is using Blender's subframe view. Just enable the Subframe toggle in the Playback popover of the timeline editor. This lets you scrub the timeline between frames which reveals what the renderer samples to create the motion blur. This needs some experimentation as we haven't found a way to eliminate the glitches in every case, but it should be a good starting point to give notes to the animator.
