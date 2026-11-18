# Update a Shot

During production, the frame range of a shot may change—either adjusting the shot's length or its position in the edit. Once adjusted, you can update the shot's .blend file frame range so new playblasts will match the updated frame range. After a new playblast is available, the shot can be automatically updated in the VSE via the Blender Kitsu Add-On.


## Push Frame Range from Edit
1. Open your edit .blend file by navigating to `Project > Open Edit`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/invoke_open_edit.jpg" width="600" alt="Open Edit" style="display: block; margin: auto;" />
</div>

2. Select a shot and its Metadata Strip. Adjust the timing of both strips so they remain in sync.
3. Select your Metadata Strip. In the Kitsu Sidebar of the VSE, under Push, select `Metadata 1 Shot` to push your shot's new frame range to the Kitsu Server.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/push_shot_metadata.jpg" width="600" alt="Push Shot Metadata" style="display: block; margin: auto;" />
</div>


## Pull Frame Range into Shot
1. Open your shot .blend file by navigating to `Project > Open Shot`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/invoke_open_shot.jpg" width="600" alt="Invoke New Shot" style="display: block; margin: auto;" />
</div>

2. Inside the Kitsu Sidebar, under Playblast tools, if your frame range on Kitsu has changed, you will see a red `Pull Frame Range` button. Select it to update the file's frame range.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/frame_range_out_of_date.png" width="600" alt="Frame Range Out of Date" style="display: block; margin: auto;" />
</div>


3. Adjust the shot's animation to accommodate the new frame range. Then, under Playblast, use the `+` button to create a new version, and select `Create Playblast` to render a new playblast.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/draw_playblast.jpg" width="600" alt="Draw Playblast" style="display: block; margin: auto;" />
</div>

## Update Playblast in Edit
1. Open your edit .blend file and select the movie strip for the shot you would like to update.
2. In the Kitsu Sidebar, under General Tools, select `^` to automatically load the next playblast from that shot.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/update_playblast_edit.jpg" width="600" alt="Update Playblast" style="display: block; margin: auto;" />
</div>
