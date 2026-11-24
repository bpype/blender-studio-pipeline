# Workflow

Blender Studio uses an edit-centric workflow. Make sure you have at least the Expo Manager Add-on and Kitsu installed and set up.

![Workflow Diagram](/media/pipeline-overview/pipeline_workflow_overview.jpg)

## Requirements
 - [Kitsu Server](/studio-setup/kitsu_server.md)
 - [Expo Manager Add-on](/addons/expo-manager/introduction.md)

## Overview

- **Versionless filenames.** Version control snapshots every save, so files never need version numbers. That lets the [Shot Builder](/addons/expo-manager/file_builder.md#shot-building) link in your Assets, and each Task's [Output Collection](/addons/expo-manager/shot.md#output-collection) is linked to the next Task file.
- **The editorial loop.** Adjust your Edit and your Shot files get the new timing through the [Frame Range](/addons/expo-manager/shot.md#frame-range) panel. Pull each new Publish you create back into the Edit to see your latest work in context.
- **Publish and review.** [Publishing](/addons/expo-manager/shot.md#publishing) posts a preview to the Shot's Task on Kitsu for feedback, and a [convention check](/addons/expo-manager/conventions.md) can catch common mistakes first. For final renders, send them to the farm and approve them in [Render Review](/addons/expo-manager/render-review.md).

## Step by Step

1. **Start with an Edit.** [Prepare the Edit](./project-workflow/usage-sync-edit.md) by turning your storyboard or preview into Shots on Kitsu. Each Shot gets a strip that holds its timing.
2. **Create your Assets.** [Make the Assets](./project-workflow/usage-asset.md) your Shots will need, like characters, props, and environments, and link them to Kitsu.
3. **Build a Shot.** [Build the Shot](./project-workflow/usage-build-shot.md) to automatically create the file, with the Assets linked in and the timing taken from the Edit.
4. **Work on your Shot.** Anything you want the next Task to use goes in the [Output Collection](/addons/expo-manager/shot.md#output-collection).
5. **Publish it.** [Publish a preview](./project-workflow/usage-playblast.md) to share your progress with the team on Kitsu.
6. **See it in the Edit.** [Import the playblast](./project-workflow/usage-import-playblast.md) into the Edit to check it in context.
7. **Adjust the timing.** If the Shot needs to be longer or shorter, [update the Shot](./project-workflow/usage-update-shot.md) so the Edit and Shot file match again.
8. **Repeat.** Keep going through steps 4-7 for each Task Type until both the Shot and Edit feel right.
9. **Render.** [Send your Shot to the farm](./project-workflow/usage-render-flamenco.md) when it's ready.
10. **Review the render.** [Check the render](./project-workflow/usage-render-review.md) and approve the version you want in the Edit.
11. **Deliver.** [Export the final film](./project-workflow/usage-final-render.md) as image sequences, audio and encoded video.
