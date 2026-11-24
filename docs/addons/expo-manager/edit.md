# Editing

The editing task maps to the [Edit entity on Kitsu](https://kitsu.cg-wire.com/guides/review-publishing/manage-edits/).

The `patterns.Edit` section defines Edit file and export paths; see [Pattern Tokens](configuration.md#pattern-tokens).

## Metadata Strips
Expo's sequence editor tools are built around a relationship between sequence strips and Shots on Kitsu. This relationship is defined by the metadata strip, a special strip in your sequence editor that represents a Shot and its frame range on your Kitsu server.

The metadata strip holds the Shot's timing separately from its content. A Shot can therefore be assembled from several media elements while one metadata strip represents its full range in the Edit. Keep the content and metadata timings in sync when editing.

![Metadata Strips](/media/addons/expo_manager/edit_metadata_strips.jpg)

You can create new Shots from media in your timeline (such as a storyboard) or link media to existing Shots; see [Active Shot](#active-shot).

## Create Shots
To create new Shots on the Kitsu server, import media into your timeline and use the `Create Shots` operator. It creates a Shot on your Kitsu server using the name and timing of each selected media strip, then creates a metadata strip for each Shot.

Choose the Sequence the new Shots belong to. For one selected strip, the dialog lets you change the Shot name and choose whether to create the project's default Shot Tasks. For multiple strips, select the Sequence first; the operator uses the strip names and skips Shots that already exist in that Sequence.


![Create Shots Panel](/media/addons/expo_manager/edit_create_shots.jpg)


### Bulk Rename
Before creating Shots, ensure that each strip has an accurate name. Use the Bulk Rename operator to rename selected strips according to the pattern set in the panel. The Sequence number can be used as a variable in the pattern.

![Bulk Rename Panel](/media/addons/expo_manager/edit_bulk_rename.jpg)

Enable Advanced mode with the screwdriver/wrench icon next to the counter value to access additional settings. You can adjust the number of counter digits, the increment, and the pattern used to generate Shot names. The supported wildcards are `<Sequence>`, `<Sequence_number>`, and `<Counter>`.


## Active Shot
The Active Shot panel lets you manage the relationship between your strips and Shots on the Kitsu server.

![Active Shot Panel (unlinked)](/media/addons/expo_manager/edit_active_shot_unlinked.jpg)
![Active Shot Panel (linked)](/media/addons/expo_manager/edit_active_shot_linked.jpg)

### Link Shot
When a media strip is not linked, use the `Link Shot` operator to associate it with a Shot on Kitsu.

### Unlink Shot
If you select a media strip or metadata strip linked to Kitsu, use the `Unlink Shot` operator to disconnect it from the Shot.

### Push Still
Select linked metadata strips to render a still image for each Shot and upload it to the selected Task Type on Kitsu. If one strip is selected, Expo uses the current frame if it falls within the Shot; otherwise, it uses the middle frame. If multiple strips are selected, it uses the middle frame of each Shot.

### Render Shot
Select linked metadata strips to render preview movies from the media on your timeline and upload them to the associated Shots on Kitsu.


## Sync Shots
The Sync Shots panel manages timing and media between your editing session and the Kitsu server. Its operators act on selected linked Shots, or all Shots when no linked Shot strips are selected.

### Push
The `Push` operator sends the frame ranges of selected Shots to Kitsu. If no linked Shot strips are selected, it pushes the ranges for all linked metadata strips. Shot files use this timing when synchronizing their [frame range](shot.md#frame-range).

![Pull Operator](/media/addons/expo_manager/edit_pull_shot.jpg)

### Pull
The `Pull` operator updates metadata strips to match Shot timing on Kitsu. If linked strips are selected, it updates those Shots. Otherwise, it reconciles all Shots in the project (or the current Episode in a TV project): it updates existing strips, creates missing strips when their time ranges are free on the metadata channel, and removes orphaned metadata strips from that channel.

::: warning
Pull can change metadata-strip timing and, when no linked Shot strips are selected, remove orphaned strips. Push your intended Edit changes first, and check the chosen metadata channel before pulling.
:::

The `Pull` operator can also import the latest Publish preview or rendered image sequence for a selected Task Type onto a target channel. It finds Published files using the configured project paths.

## Export & Publish
Create a Publish for your Edit Task on Kitsu directly from your blend file. This creates a [Publish revision and comment](https://kitsu.cg-wire.com/guides/review-publishing/publish/#publish-a-preview-as-a-version) on the specified Kitsu Task. If publishing backups are enabled, this also creates a [backup version](backups.md).

The Edit's [file patterns](configuration.md#file-patterns) determine the export's `publish_dir` and `publish_file`.

![Edit Export Publish](/media/addons/expo_manager/edit_publish.jpg)

- **Task Type**: The Edit file maps only to the Edit entity. When publishing, you can select the Task Type for the Publish.
- **Status**: Set your Task's status (Done, WIP, Retake, etc.), which will appear in the comment alongside your Edit revision.
- **Comment**: Add details to accompany your Publish.
- **Thumbnail Frame**: Select which frame (within the render frame of your timeline) to use as a thumbnail. Uses the current frame by default.
