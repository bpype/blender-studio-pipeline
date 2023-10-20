# Shot Assembly

::: warning Work in Progress
October 10th 2023 - The content of this page is currently being edited/updated.
:::


Before Shot Assembly can begin two requirements need to be met. Firstly, shots to be assembled need to have corresponding Tasks on the Kitsu Server, and secondly those shots must have Assets ‘cast’ or associated with each shot. These will describe when the shot happens in the edit and what assets appear in the shot.


### Preparing Metastrips from a Previz Sequence

To begin Shot Assembly it is required to describe the name/length of each shot inside a “Video Sequence Editor” .blend file. Once a Previz Sequence has been assembled into the VSE, ['Metastrips’](https://studio.blender.org/pipeline/addons/blender_kitsu#metastrips) can be created for each shot. A metastrip is an empty video strip that is linked into the project management software Kitsu. Metastrips are used to push updates to the frame ranges of each shot to Kitsu, which are later used in the Shot Assembly process. 

Metastrips are created from the Previz Strips, they are either linked to an existing Kitsu Shot, or a new Shot/Sequence can be pushed from the VSE to the Kitsu Server. The shot’s in, out and duration will be determined by the strip’s length. Multiple metastrips can be made out of a single previz strip if required, adjust the shot’s timing by simply trimming the metastrip in the timeline. These metastrips are then pushed to Kitsu Server to update the shot info on the server side. Below is a Previz Sequence with it’s metastrips.


![Metastrips](/media/pipeline-overview/shot-production/Pets_Previz__Meta_Strips.png)


For more information about metastrips and the processes involved in managing the edit of your film see the [Blender Kitsu Add-On documentation](https://studio.blender.org/pipeline/addons/blender_kitsu).


### Casting Assets in Kitsu

Assets or their place holders, need to be saved into the central location where assets are saved, on the [production directory](https://studio.blender.org/pipeline/td-guide/project-setup#project-directory). Once Assets or their place holders have been created, users can begin casting. Casting is completed on the Kitsu Server, [a demo of the asset casting process in Kitsu](https://forum.cg-wire.com/t/breakdown-casting-widget-for-kitsu/31) can be found on the CGWire Forum. 


### Using Shot Builder

Now that all external requirements are met it is time to run the Shot Builder, which is a feature of the [Blender Kitsu Add-On](https://studio.blender.org/pipeline/addons/overview). 

Inside your production’s directory the Shot Builder configuration files need to be created using the [examples](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts-blender/addons/blender_kitsu/shot_builder/docs/examples) included in the Add-On's directory. See the Shot Builder Config [Directory Layout](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts-blender/addons/blender_kitsu/shot_builder/docs#directory-layout) for details. The only configuration file that requires production specific edits is `assets.py`. This configuration file links the Kitsu Asset entries to their corresponding files in the production directory, please see the [Shot Builder API](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts-blender/addons/blender_kitsu/shot_builder/docs#api) for more details. 


![New Shot](/media/pipeline-overview/shot-production/new_shot_file.png)


The Shot Builder is started by navigating to File>New>Shot File. Then users can select a sequence, shot and type of shot to build. The Shot Builder is capable of assembling the following types of shots.



* <span style="text-decoration:underline;">Animation</span> contains all Assets with Rigs and a linked set, Animators work here, all data that needs to move down the pipeline is placed in a **shot_name.anim** collection.
* <span style="text-decoration:underline;">FX</span> contains any effects objects in a collection **shot_name.fx**. This file will have the **shot_name.anim** collection linked into it and the **shot_name.lighting** collection if available.
* <span style="text-decoration:underline;">Lighting</span> contains all lighting objects, like lights, shadow catchers and any other data related to lighting the scene in an **shot_name.lighting** collection. This .blend file will also contain a linked version of the **shot_name.anim** collection and the **shot_name.fx** collection when available. 
* <span style="text-decoration:underline;">Compositing</span> contains linked copies of the **shot_name.anim**, **shot_name.fx**,  **shot_name.lighting** collections. Compositing file contains a Compositing Node Group used for final render. The compositing file is usually used for rendering.


### Maintaining Existing Shots

After shots have been created in some cases the shot’s length or position may be adjusted by the editor. These changes will be tracked in Kitsu using the metastrips described above. If a metastrip for a given shot has been changed, those changes will be pushed into Kitsu. In this case when users open a shot file they will be warned within the Playblast Tools section of their Kitsu add-on to pull the new frame range into their .blend file. 


![Frame Range Outdated](/media/pipeline-overview/shot-production/frame_range_out_of_date.png)