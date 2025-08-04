# Prepare Edit
## Sync Your Edit with Kitsu Server

Most productions begin with a previz or storyboard step, showing the overall direction and plan for the production. By inputting this as video strip(s) into a VSE file, you can automatically create the corresponding shots on the Kitsu Server directly from the VSE.

1. If not already done, ensure your project settings are set up in [Blender Kitsu Add-On Preferences](https://studio.blender.org/tools/addons/blender_kitsu#how-to-get-started).
2. Navigate to `Project > New Edit` in the header or `File > New > Edit File` to create a new Edit file at the path `your_project_name/svn/edit`.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/invoke_new_edit.jpg" width="600" alt="Invoke New Edit" style="display: block; margin: auto;" />
</div>

3. The operator provides the option to automatically create an Edit task if it doesn't already exist on your Kitsu server.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/draw_new_edit.jpg" width="600" alt="Draw New Edit" style="display: block; margin: auto;" />
</div>

4. Populate your new edit file with your previz or storyboard.
5. With your strip selected, in the Blender Kitsu side panel of the VSE, select "Create Metadata Strip from Active Shot" to create a new Metadata Strip.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/new_edit_new_metadata.jpg" width="600" alt="New Metadata Strip" style="display: block; margin: auto;" />
</div>

6. Next, select “Init Active Shot” and enter the Shot and Sequence names you would like to submit to Kitsu.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/new_edit_init_active_shot.jpg" width="600" alt="Init Active Shot" style="display: block; margin: auto;" />
</div>

7. Finally, select the “Submit New Shot” button to submit this new shot to the Kitsu Server.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/new_edit_submit_shot.jpg" width="600" alt="Submit New Shot Button" style="display: block; margin: auto;" />
</div>

Repeat steps 5–7 for each shot in the sequence. Multiple Metadata Strips can be made from a single previz strip if required; adjust the shot’s timing by simply trimming the Metadata Strip in the timeline. Below is an example of a previz sequence with Metadata Strips.

