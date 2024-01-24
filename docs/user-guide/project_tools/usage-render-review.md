# Render Review

## Review and Approve Renders
Once your shot(s) have been rendered by Flamenco, you are ready to review your renders using the Render Review Add-On. This Add-On allows you to review different versions of your Render, assuming you rendered with Flamenco for multiple versions, and select the version you would like to use as your approved version.

1. Ensure Blender Kitsu Add-On is enabled and Logged In 
2. From `File>New>Render Review`
3. From the dialogue box select a Sequence Name you would like to Review
4. Select the video strip for the render you are reviewing
5. Select `Push to Edit & Approve Render` 
	- Push to Edit will take the mp4 of your flamenco render and add it to the `your_project_name/shared/editorial/shots` directory
	- Approve Render will copy the Image Sequence of your flamenco render to the `your_project_name/shared/editorial/frames` directory

## Import Approved Renders into VSE
Renders approved by the render review Add-On can be automatically imported into your edit using the same function used to update the playblast of shots in the edit.

1. Open your Edit .blend file
2. Select the video strip representing the shot that has an approved render. In the Kitsu Sidebar under General Tools select, `^` to load the next playblast from that shot automatically, which is an **mp4 preview** of your final render
3. Select the video strips representing all the shots you have approved renders for. Use `Shot as Image Sequence` to import the final image sequences for each shot as EXR or JPG and load it to a new channel in the VSE
