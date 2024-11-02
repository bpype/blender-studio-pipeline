# Playblast Shot

## Playblast your First Shot
Once your first shot is animated you are ready to render a playblast of this shot, which will be later imported into your edit .blend file. 
1. Launch Blender via [Launching Software] Guide and Open a Shot
2. In the Kitsu Sidepanel, under context, use the refresh icon to reload your file's context if it is not set already.
3. In the Kitsu Sidepanel under Playblast tools you are now ready to create a new playblast version, select `Create Playblast` which will render a preview of your shot and add it as a comment on your Kitsu Task for this shot
	1. Status: select the status to set your Kitsu Task to
	2. Comment: add any notes you would like to include in your comment
	3. Use Current Viewport Shading: Enable this to render will the settings from your current viewport
	4. Thumbnail Frame: Which frame in your current file should be the thumbnail for your preview file

## Loading First Playblast into the Edit
For each new task type, Anim/Layout etc needs to be added manually, then it can update the shot afterwards

Returning to your edit .blend file, we can now load the playblast from the animation file into the edit.

1. Open your edit .blend file inside the directory `/your_project_name/svn/edit`
2. Select the Metadata Strip associated with your shot
3. From the Sequencer Side Panel select `Import 1 Shot Playblast`
3. Select the Task Type you would like to load the playblast from and an empty channel
4. Your new playblast will be imported with the same timing as the corresponding metadata strip