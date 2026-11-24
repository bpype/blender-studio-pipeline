# Shot Assembly


Before shot assembly can begin, two requirements must be met. First, the Shots to be assembled need corresponding Tasks on the Kitsu server. Second, those Shots must have Assets cast or associated with them. These records describe when each Shot happens in the Edit and which Assets appear in it.



::: info Building a Project
Learn how to build a complete project, including Shots, in the [Project Workflow](/pipeline/workflow.md).
:::
## Preparing Metadata Strips from a Previz Sequence

To begin shot assembly, create strips with each Shot's name and duration in an [Edit .blend file](/addons/expo-manager/edit.md). After assembling a previz Sequence in the VSE, create [metadata strips](/addons/expo-manager/edit.md#metadata-strips) for each Shot. Each metadata strip represents a Shot linked to Kitsu and is used to push its frame range to the server.

Metadata strips are created from previz strips. They can be linked to an existing Kitsu Shot, or a new Shot and Sequence can be created in the VSE and pushed to the Kitsu server. The Shot's start frame, end frame, and duration are determined by the strip's length. If needed, create multiple metadata strips from one previz strip and adjust each Shot's timing by trimming its metadata strip in the timeline. Push the metadata strips to Kitsu to update the Shot information. The image below shows a previz Sequence with its metadata strips.


![Metadata Strips](/media/addons/expo_manager/edit_metadata_strips.jpg)

::: info Preparing an Edit
For more information about metadata strips and the processes involved in managing your film's Edit, see the [Prepare Edit Guide](/pipeline/project-workflow/usage-sync-edit.md).
:::

## Shot Types
* <span style="text-decoration:underline;">Animation</span> contains all Assets with Rigs and a linked set, Animators work here, all data that needs to move down the pipeline is placed in a **shot_name.anim** collection.
* <span style="text-decoration:underline;">FX</span> contains any effects objects in a collection **shot_name.fx**. This file will have the **shot_name.anim** collection linked into it and the **shot_name.lighting** collection if available.
* <span style="text-decoration:underline;">Lighting</span> contains all lighting objects, like lights, shadow catchers and any other data related to lighting the scene in an **shot_name.lighting** collection. This .blend file will also contain a linked version of the **shot_name.anim** collection and the **shot_name.fx** collection when available.
* <span style="text-decoration:underline;">Compositing</span> contains linked copies of the **shot_name.anim**, **shot_name.fx**,  **shot_name.lighting** collections. Compositing file contains a Compositing Node Group used for final render. The compositing file is usually used for rendering.


## Maintaining Existing Shots

After Shots have been created, the editor may adjust their length or position. These changes are tracked in Kitsu through the metadata strips described above. Push the changes to Kitsu. When users open a Shot file, Expo Manager's Frame Range panel warns them if they need to pull the updated frame range into their `.blend` file.


![Frame Range Outdated](/media/addons/expo_manager/frame_range_panel.jpg)
