# Update a Shot's Frame Range
During production in some cases the frame range of a shot will change, either adjusting a shot's length or adjusting it's position in the edit. Once adjusted, we can update the shot .blend file's frame range so new playblasts will match this updated frame range. Once a new playblast is available the shot can automatically be updated in the VSE via the Blender Kitsu Add-On

1. Open your edit .blend file inside the directory `your_project_name/svn/edit`
2. Select a shot and it's Metadata Strip, adjust the timing of both strips so they remain in sync.
3. Select your Metadata Strip, in the Kitsu Sidebar of the VSE Under Push select `Metadata 1 Shot` to push your shot's new frame range to the Kitsu Server
4. Open your shot .blend file inside the directory
	`your_project_name/svn/pro/shots/{sequence_name}/{shot_name}/`
5. Inside the Kitsu Sidebar, under Playblast tools, if your frame range on Kitsu has changed you will see a red `Pull Frame Range` button. Select it to update the file's Frame Range
6. Adjust the shot's animation to accommodate the new frame range, then under Playblast use the `+` button to create a new version, then select `Create Playblast` to render a new playblast
7. Open your edit .blend file, and select the movie strip for the shot you would like to update.
8. In the Kitsu Sidebar under General Tools select, `^` to load the next playblast from that shot automatically
