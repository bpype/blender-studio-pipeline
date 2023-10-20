# Editorial

::: warning Work in Progress
October 20th 2023 - The content of this page is currently being edited/updated.
:::

At Blender Studio we use the Blender VSE to create and maintain a story edit. A couple of reference links for now:

* [Charge Previsualization](https://studio.blender.org/blog/charge-previsualization/)
* [Story Pencil](https://www.youtube.com/watch?v=b25kfE6qd_c) - Currently not used at Blender Studio, but worth checking when working with storyboard artists.

## Requirements, any of the following:
* Film script
* Thumbnails/sketches
* Storyboard drawings
* Previs images
* Previs videos
* Concept art
* Temp music
* Temp sfx
* Temp vocals

## Goal of the task

During the early stages of the project, the goal is to take any available materials into the VSE and create a rough animatic version of the film
- based on the most current version of the scrip
- or based on the most recent feedback from the director.

Over the course of the project, sections of the rough animatic **get replaced** with 
- alternative storyboard drawings,
- layout shots,
- animated playblasts
- and final renders.

So at any given moment, parts of the edit are in different stages until the entire thing finally crosses the finish line with only final renders.

## Resolution

Set the file to the correct resolution, our most commonly used one is 2048x858. For some films it’s helpful to also include a letterbox border, to add subtitles or notes from the director. In those cases we usually simply add a bit to the height to make room for it.

As an example, in ‘Sprite Fright’ the final resolution was 2048x858 but in the beginning we were working with 2048x1146 in the edit and adding two black color strips (above and below) to keep the film area 2048x858. Then a text strip got added above to indicate which scene we were in, and a text strip below for the subtitles.

## Export settings

We usually export an **.mp4 file**, with the video codec **H.264** and audio codec AAC.

## Versioning

The edit file should get “-v001” at the end of its name (e.g. `short_film-edit-v001.blend`).

The version number is bumped up whenever there is a new export of the film, so that the export has the same version number as the work file (e.g. `short_film-edit-v001.mp4`). This might usually happen 1-4 times a week, depending on the situation.

## Legacy cleaning

As the project goes forward and gets more refined, it becomes increasingly more important to **keep the edit organized and tidy**.

A lingering alt version of a scene might be allowed to exist hidden inside the edit for 2-3 versions but it needs to be eventually deleted and the edit cleaned up. Otherwise it becomes too bogged down in legacy issues. You will always have the older versions to go back to, if an old scene needs to be revived.

## Organizing external files

All external files for the edit are usually put inside a well organized “editorial” folder, or in an adjacent folder.

### Organizing strips

In the beginning there is no hard and fast rule. Whatever works best for the editor to create a rough animatic.

As the project progresses and the complexity level of the edit gets raised, it becomes more important to create some rules of thumb.
- Allow 4-12 channels for the storyboards/previs/shots (or however many are needed),
- 3-5 for the temp music and ambiance,
- 2-3 channels for dialogue (depending on how many characters are in the film)
- and 10-20 channels for temp sfx.

The temp sfx can get very messy and unwieldy so be very selective in the beginning how many to use and for what purpose.

### Organizing temp vocals / scratch dialogue

When the film is dialogue heavy, it can be a nightmare to keep track of all the different versions of takes for each and every character.

For ‘Sprite Fright’ I made a new workspace for each character, with its own scene data pinned to it. There I could have a long edit of the various recordings of that character, using markers to help organize them. When I went over a recording, I would cut each take and move the ones I liked up one channel and the ones I didn’t like down one channel. Once I had the takes I needed, I would copy the strips, go back to the “main edit” workspace, paste them there and integrate them into the edit.with

### Adding meta strips

At some point during the production process, the animatic will become solid enough that scenes and shots will get **officially named**. The edit is not necessarily locked, but at this point changes to the story will be kept to a minimum.

In a single channel, a color strip will be created for each shot (to represent the position and timing of each shot). The **Kitsu addon** can then use those color strips to create meta strips out of them, all in a single channel. Each meta strip represents a shot and is connected to Kitsu, so that once any edit changes are made the information can be sent to Kitsu.

### Organizing exported shots

Once a shot is exported via the Kitsu addon, it needs to be **manually inserted** into the edit (this is for quality control and troubleshooting) and placed below the corresponding meta strip. From there on out the Kitsu addon can be used to update the shot to the latest version, if a new version has been exported.