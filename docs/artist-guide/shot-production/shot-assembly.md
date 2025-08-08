# Shot Assembly


Before Shot Assembly can begin two requirements need to be met. Firstly, shots to be assembled need to have corresponding Tasks on the Kitsu Server, and secondly those shots must have Assets ‘cast’ or associated with each shot. These will describe when the shot happens in the edit and what assets appear in the shot.



::: info Building a Project
Learn how to build a complete project including shots in a step-by-step format, see the [Project Usage Guide](/artist-guide/project_tools/project-usage.md).
:::
## Preparing Metadata Strips from a Previz Sequence

To begin Shot Assembly it is required to describe the name/length of each shot inside a “Video Sequence Editor” .blend file. Once a Previz Sequence has been assembled into the VSE, ['Metadata Strips’](https://studio.blender.org/tools/addons/blender_kitsu#metadata-strips) can be created for each shot. A Metadata Strip is an empty video strip that is linked into the project management software Kitsu. Metadata Strips are used to push updates to the frame ranges of each shot to Kitsu, which are later used in the Shot Assembly process.

Metadata Strips are created from the Previz Strips, they are either linked to an existing Kitsu Shot, or a new Shot/Sequence can be pushed from the VSE to the Kitsu Server. The shot’s in, out and duration will be determined by the strip’s length. Multiple Metadata Strips can be made out of a single previz strip if required, adjust the shot’s timing by simply trimming the Metadata Strip in the timeline. These Metadata Strips are then pushed to Kitsu Server to update the shot info on the server side. Below is a Previz Sequence with it’s Metadata Strips.


![Metadata Strips](/media/pipeline-overview/shot-production/pets_metadata_strips.png)

::: info Preparing an Edit
For more information about Metadata Strips and the processes involved in managing the edit of your film see the [Prepare Edit Guide](/artist-guide/project_tools/usage-sync-edit.md).
:::

## Shot Types
* <span style="text-decoration:underline;">Animation</span> contains all Assets with Rigs and a linked set, Animators work here, all data that needs to move down the pipeline is placed in a **shot_name.anim** collection.
* <span style="text-decoration:underline;">FX</span> contains any effects objects in a collection **shot_name.fx**. This file will have the **shot_name.anim** collection linked into it and the **shot_name.lighting** collection if available.
* <span style="text-decoration:underline;">Lighting</span> contains all lighting objects, like lights, shadow catchers and any other data related to lighting the scene in an **shot_name.lighting** collection. This .blend file will also contain a linked version of the **shot_name.anim** collection and the **shot_name.fx** collection when available.
* <span style="text-decoration:underline;">Compositing</span> contains linked copies of the **shot_name.anim**, **shot_name.fx**,  **shot_name.lighting** collections. Compositing file contains a Compositing Node Group used for final render. The compositing file is usually used for rendering.


## Maintaining Existing Shots

After shots have been created in some cases the shot’s length or position may be adjusted by the editor. These changes will be tracked in Kitsu using the Metadata Strips described above. If a Metadata Strip for a given shot has been changed, those changes will be pushed into Kitsu. In this case when users open a shot file they will be warned within the Playblast Tools section of their Kitsu add-on to pull the new frame range into their .blend file.


![Frame Range Outdated](/media/artist-guide/project_tools/frame_range_out_of_date.png)
