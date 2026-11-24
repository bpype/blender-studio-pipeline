# Update a Shot

During production, a shot's length or position in the edit may change. Push the updated timing to Kitsu, pull it into the shot file, and then publish and import a new preview into the edit with Expo Manager.


## Push Frame Range from Edit
1. Open your edit .blend file by navigating to `Expo > Open Edit`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_open_edit.jpg" width="600" alt="Open Edit" style="display: block; margin: auto;" />
</div>

2. Select a shot and its Metadata Strip. Adjust the timing of both strips so they remain in sync.
3. Select your metadata strip. In the Expo sidebar of the VSE, select `Push 1 Shot` to push the shot's new frame range to the Kitsu Server.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/edit_push_shot.jpg" width="600" alt="Push Shot Metadata" style="display: block; margin: auto;" />
</div>


## Pull Frame Range into Shot
1. Open your shot .blend file by navigating to `Expo > Open Shot`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_open_shot.jpg" width="600" alt="Invoke New Shot" style="display: block; margin: auto;" />
</div>

2. In the Expo sidebar's Frame Range panel, if your frame range on Kitsu has changed, you will see a red `Pull Frame Range` button. Select it to update the file's frame range.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/frame_range_panel.jpg" width="600" alt="Frame Range Out of Date" style="display: block; margin: auto;" />
</div>


3. Adjust the shot's animation to accommodate the new frame range. Then select `Publish Preview` in the Publish panel. Expo determines the next publish version automatically.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/shot_playblast.jpg" width="600" alt="Draw Publish" style="display: block; margin: auto;" />
</div>

## Update Publish in Edit
1. Open your edit .blend file and select the metadata strip or linked content strip for the shot you would like to update.
2. In the Expo sidebar, select `Pull 1 Shot`. Enable `Import Latest Previews`, select the task type and an empty preview channel, then confirm to import the latest preview.

The import adds a new strip; remove or manage older preview strips as needed.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/edit_pull_shot_publish.jpg" width="600" alt="Update Playblast" style="display: block; margin: auto;" />
</div>
