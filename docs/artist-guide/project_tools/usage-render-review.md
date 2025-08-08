# Render Review

## Review and Approve Renders
Once your shot(s) have been rendered by Flamenco, you are ready to review your renders using the Render Review Add-On. This add-on allows you to review different versions of your render, assuming you rendered with Flamenco for multiple versions, and select the version you would like to use as your approved version.

1. Ensure the Blender Kitsu Add-On is enabled and you are logged in.
2. Go to `File > New > Render Review`.
3. In the dialog box, select the sequence name you would like to review.
4. Select the video strip for the render you are reviewing.
5. Select `Push to Edit & Approve Render`:
	- **Push to Edit** will take the MP4 of your Flamenco render and add it to the `your_project_name/shared/editorial/shots` directory.
	- **Approve Render** will copy the image sequence of your Flamenco render to the `your_project_name/shared/editorial/frames` directory.

## Import Approved Renders into VSE
Renders approved by the Render Review Add-On can be automatically imported into your edit using the same function used to update the playblast of shots in the edit.

1. Open your edit `.blend` file.
2. Select the video strip representing the shot that has an approved render. In the Kitsu sidebar under General Tools, select `^` to load the next playblast from that shot automatically, which is an **MP4 preview** of your final render.
3. Select the metadata strips representing all the shots you have approved renders for. Use the `Import Image Sequence` operator to import the final image sequences for each shot as EXR or JPG and load them to a new channel in the VSE.

