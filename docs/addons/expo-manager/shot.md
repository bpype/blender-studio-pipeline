# Shot
Shot files map to [Shot Tasks on Kitsu](http://kitsu.cg-wire.com/guides/production-structure/manage-shots/).

The `patterns.Shot` section determines Shot file and Publish paths; see [Pattern Tokens](configuration.md#pattern-tokens).

## New Shot
1. Create a Shot on Kitsu by following the [Editing](edit.md#create-shots) workflow or creating it manually on your Kitsu server.
2. Use `Expo > New Shot` at the top of Blender to create a new Shot file. Each Shot file is associated with a Shot and Task Type.
3. Use `Expo > Open Shot` to open an existing Shot file.

## Frame Range
The Frame Range panel appears in the sidebar of Shot files when `frame_range_sync` is set to `true` in your [Shot Builder configuration](configuration.md#shot-builder). It provides operations for pushing and pulling frame-range changes between Edit and Shot files.

![Frame Range Panel](/media/addons/expo_manager/frame_range_panel.jpg)

The frame range consists of four values:
- Frame In: Where the Shot starts in the Edit.
- Frame Out: Where the Shot ends in the Edit.
- 3D Start Frame: Where the Shot starts in the 3D file.
- Duration: The Shot's length, determined by the Edit's in and out points.

The Edit's in and out points determine the Shot duration. The Shot file's end frame is calculated from its 3D start frame and duration. In animation files, the scene's start frame sets the 3D start frame. Expo Manager uses the `3d_start` value in [Project Settings](configuration.md#project-settings) as the default start frame for Shot files.

First, push timing changes from the [Edit](edit.md#push), then pull the frame range into the shot file. After updating and publishing the Shot, pull its latest Publish into the Edit. When frame-range synchronization is enabled, Expo Manager checks the frame range when the file is opened.

### Push Frame Range
Push the scene's 3D start frame and duration to Kitsu. This changes the Shot's stored frame count and 3D start frame, so coordinate duration changes with editorial.

### Pull Frame Range
Update the current blend file to match the Edit frame range on the Kitsu server. The [Edit Task](edit.md) sets this range. This operator appears red when the current frame range is out of date.

### Check Frame Range
Fetch the frame range from the Kitsu server and check that it matches the current file. If the check fails, the [`Pull Frame Range`](#pull-frame-range) operator appears red.

## Editorial Reference
Load the latest [editorial Publish](edit.md#export--publish) into the sequence editor, replacing any previous editorial Publishes.

The `load_editorial_ref` [Shot Builder setting](configuration.md#shot-builder) controls which Shot Task Types load this reference when built.

## Output Collection
Output collections define how information moves downstream between Shot Tasks. The [Shot Builder settings](configuration.md#shot-builder), `output_col_create` and `output_col_link_mapping`, control which collections are created and linked.

## Publishing
The Publish panel offers Preview and Render publishing, as well as Farm Job submission. Each uses specific file paths. Previews and renders are images or movies that represent a snapshot of your work and are uploaded as comments to your Kitsu server.

The Shot's [file patterns](configuration.md#file-patterns) specify `publish_dir`, `publish_file`, and `publish_frames`.

![Shot Publish Panel](/media/addons/expo_manager/shot_publish.jpg)

### Publish Preview & Publish Render
Create a Publish for the Shot Task on Kitsu directly from your blend file. This creates a [Publish revision and comment](https://kitsu.cg-wire.com/guides/review-publishing/publish/#publish-a-preview-as-a-version) on the specified Kitsu Task. If publishing backups are enabled, this also creates a [backup version](backups.md).

**Publish Preview** creates a preview movie in `publish_dir` using `publish_file` from your [file patterns](configuration.md#file-patterns).

**Publish Render** creates an image sequence in `publish_frames` and a preview movie of that sequence in `publish_dir`.

![Shot Publish Preview](/media/addons/expo_manager/shot_publish_preview.jpg)

- **Task Type**: The shot file's context determines its Task Type.
- **Status**: Set your Task's status (Done, WIP, Retake, etc.) alongside your Shot revision.
- **Comment**: Add details to accompany your Publish.
- **Thumbnail Frame**: Select which frame (within the render frame of your timeline) to use as a thumbnail. Uses the current frame by default.
- **Render Mode**: Choose either *Scene* or *Viewport* rendering. Viewport will use exactly what you see in your 3D Viewport, Scene matches the output of `Render Animation`.


### Submit Farm Job

Submit your current Shot Task to the [Flamenco](https://flamenco.blender.org/) render farm. The job renders the current file's frame range and uses path components configured in your [file patterns](configuration.md#file-patterns). Farm jobs can be reviewed and published using [Render Review](render-review.md). The `farm_job_type` [project setting](configuration.md#project-settings) selects a [job type](https://flamenco.blender.org/usage/job-types/) configured on your Flamenco server. Once a farm output folder exists for the active Shot Task, an "Open Folder" button appears next to "Submit Farm Job".

![Shot Submit Farm Job](/media/addons/expo_manager/shot_submit_farm_job.jpg)

- **Media Type**: Choose either *PNG* for preview jobs or *OpenEXR+JPG* for final render.
