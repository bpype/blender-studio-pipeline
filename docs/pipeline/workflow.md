# Workflow

Blender Studio uses an edit-centric workflow. Make sure you have at least the Expo Project Manager add-on and Kitsu installed and set up.

![Workflow Diagram](/media/pipeline-overview/pipeline_workflow_overview.jpg)

## Requirements
 - [Kitsu Server](/studio-setup/kitsu_server.md)
 - [Expo Project Manager Add-on](/addons/expo_project_manager.md)

## Overview

- **Versionless filenames.** Version control snapshots every save, so files never need version numbers. That lets the [Shot Builder](/addons/expo_project_manager.md) link in your assets, and each task's [Output Collection](/addons/expo_project_manager.md) is linked to the next task file.
- **The editorial loop.** Adjust your edit and your shot files get the new timing through the [Frame Range](/addons/expo_project_manager.md) panel. Each new preview you publish is linked back into the edit, so you always see your latest work in context.
- **Publish and review.** [Publishing](/addons/expo_project_manager.md) posts a preview straight to the task on Kitsu for feedback, and a [convention check](/addons/expo_project_manager.md) can catch common mistakes first. For final renders, send them to the farm and approve them in [Render Review](/addons/expo_project_manager.md).

## Step by Step

1. **Start with an edit.** [Prepare the edit](./project-workflow/usage-sync-edit.md) by turning your storyboard or preview into shots on Kitsu. Each shot gets a strip that holds its timing.
2. **Create your assets.** [Make the assets](./project-workflow/usage-asset.md) your shots will need, like characters, props and environments, and link them to Kitsu.
3. **Build a shot.** [Build the shot](./project-workflow/usage-build-shot.md) and it comes ready to work in, with the assets linked in and the timing taken from the edit.
4. **Work on your shot.** Anything you want the next task to use goes in the [Output Collection](/addons/expo_project_manager.md).
5. **Playblast it.** [Publish a playblast](./project-workflow/usage-playblast.md) to share your progress with the team on Kitsu.
6. **See it in the edit.** [Import the playblast](./project-workflow/usage-import-playblast.md) into the edit to check it in context.
7. **Adjust the timing.** If the shot needs to be longer or shorter, [update the shot](./project-workflow/usage-update-shot.md) so the edit and your shot file match again.
8. **Repeat.** Keep going through steps 4-7 for each task type until both the shot and the edit feel right.
9. **Render.** [Send your shot to the farm](./project-workflow/usage-render-flamenco.md) when it's ready.
10. **Review the render.** [Check the render](./project-workflow/usage-render-review.md) and approve the version you want in the edit.
11. **Deliver.** [Export the final film](./project-workflow/usage-final-render.md) as image sequences, audio and encoded video.
