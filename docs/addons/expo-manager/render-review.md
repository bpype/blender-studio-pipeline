# Render Review

Prerequisites:
- [Flamenco](https://flamenco.blender.org/) must be set up in your production environment, and its Add-on must be installed and enabled.
- Your Flamenco server must be configured according to the [Studio Setup](/studio-setup/flamenco_setup.md) guide.
- You must have submitted at least one farm job using the [Submit Farm Job](shot.md#submit-farm-job) operator.

The `farm_output` [shared path](configuration.md#shared-paths) is where Expo Manager looks for farm jobs. Approved Shot frames are copied to `publish_frames` in the Shot's [file patterns](configuration.md#file-patterns).


#### New Render Review Session

To start a render review session, navigate to `New > Render Review`. This opens the Render Review template and prompts you to load a Sequence for review.

![New Render Review Session](/media/addons/expo_manager/new_render_review_session.jpg)

- **Sequence**: Select the Sequence to review.
- **Match Latest Length**: Only import jobs whose EXR frame count matches the current Shot length on Kitsu.
- **Use Video**: Import the MP4 video preview instead of the image sequence.
- **Latest Version Only**: When enabled, all previous job versions are loaded as image sequences and only the most recent job is loaded as video (requires **Use Video** to be enabled). Defaults to off.
- **Filter Name**: Only load farm jobs from Shots whose name contains this substring. Leave blank to load all Shots.
- **Filter Task Type**: Restrict loading to a single Task Type (e.g. "Animation"). Leave blank to load all Task Types.

The Render Review template is loaded from `render_review.blend` in the `templates_dir` defined in your [shared paths](configuration.md#shared-paths). If that file is not found, Expo Manager uses the built-in template.

#### Render Review Panel

![Render Review Panel](/media/addons/expo_manager/render_review_panel.jpg)

**Kitsu Server**
- **Load Sequence Jobs**: Load farm jobs for a Sequence, appending them after existing strips. Supports the same **Filter Name** and **Filter Task Type** options as the new session dialog.
- **Load Shot Jobs**: Load farm jobs for a specific Shot, appending them after existing strips. Supports **Filter Task Type** to restrict which Task Types are loaded.

**Folder**
- **Load Job Folder**: Manually load a farm job from a folder. Approvals are not available for media imported this way.

**Active Render Panel**
- **Inspect EXR**: Open the matching EXR frame for the current Shot in an Image Editor.
- **Approve & Publish Render**: Copy the rendered frames to `publish_frames` and the video preview to `publish_file`, as defined in the project configuration, then create a new version on the Kitsu server.
- **Open Render Job Folder**: Open the render job folder in your system's file browser.

Approval also writes `metadata.json` in the render directory, recording the current source farm job folder and, when available, the previously recorded source. Use it to trace approved frames back to their render jobs.
