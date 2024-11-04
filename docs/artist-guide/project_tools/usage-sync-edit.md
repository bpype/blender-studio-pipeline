# Prepare Edit
## Sync your Edit with Kitsu Server
Most productions begin with a previz or storyboard step, showing the overall direction and plan for the production. By inputting this as video strip(s) into a VSE file we can automatically create the corresponding shots on the Kitsu Server directly from the VSE.

1. If not already ensure your project settings are setup [Blender Kitsu Add-On Preferences](https://studio.blender.org/pipeline/addons/blender_kitsu#how-to-get-started)
2. At the directory `your_project_name/svn/edit` create a new "Video Editing" File.
3. Populate your new edit file with your previz video strips
4. With your first strip selected, in the Blender Kitsu side panel of the VSE select "Create Metadata Strip from Active Shot” to create a new Metadata Strip.
5. Next select “Init Active Shot”, and enter the Shot and Sequence names you would like to submit to Kitsu.
6. Finally select the “Submit New Shot Button” to submit this new Shot to the Kitsu Server.

Repeat steps 4-6 for each shot in the sequence. Multiple Metadata Strips can be made out of a single previz strip if required, adjust the shot’s timing by simply trimming the Metadata Strip in the timeline. Below is an example of a previz sequence with Metadata Strips.

