# Project Usage

Once your project is set-up there are several things that users can do when using the pipeline, including creating new shots on Kitsu directly from Blender, automatically building shots based on Kitsu data and updating the frame range of existing shots within the project. 

::: warning Work in Progress
15 Oct. 2023 - The content of this page is currently being edited/updated.
:::

## Sync your Edit with Kitsu Server
Most productions begin with a previz or storyboard step, showing the overall direction and plan for the production. By inputting this as video strip(s) into a VSE file we can automatically create the corresponding shots on the Kitsu Server directly from the VSE.

1. If not already ensure your project settings are setup [Blender Kitsu Add-On Preferences](https://studio.blender.org/pipeline/addons/blender_kitsu#how-to-get-started)
2. At the directory `your_project_name/svn/edit` create a new "Video Editing" File.
3. Populate your new edit file with your previz video strips
4. With your first strip selected, in the Blender Kitsu side panel of the VSE select "Create Metastrip Active Shot” to create a new metastrip.
5. Next select “Init Active Shot”, and enter the Shot and Sequence names you would like to submit to Kitsu.
6. Finally select the “Submit New Shot Button” to submit this new Shot to the Kitsu Server.

Repeat steps 4-6 for each shot in the sequence. Multiple metastrips can be made out of a single previz strip if required, adjust the shot’s timing by simply trimming the metastrip in the timeline. Below is an example of a previz sequence with metastrips.



## Creating your first Asset
The next step is to create an asset and store that information into the Kitsu Server.

1. Launch Blender via [Project Blender](/user-guide/project_tools/project-blender.md) Guide
2. Under `Edit>Preferences>Add-Ons` ensure `Asset Pipeline` is enabled
3. Follow the [asset pipeline guide](https://studio.blender.org/pipeline/addons/asset_pipeline) to create a new asset collection, ensure these assets are marked as an [Asset in Blender](https://docs.blender.org/manual/en/latest/files/asset_libraries/introduction.html#creating-an-asset).
4. Save the above asset within the directory `your_project_name/svn/pro/assets/char` (or similar depending on type)

## Load Asset Data into Kitsu
To match Assets File to the data on the Kitsu server, we need to first enter the data into the Kitsu server and secondly create an Asset Index. This is a json file that contains the mapping of the asset's name to the asset's filepath. Any collection Marked as an Asset in Blender in the directory your_project/svn/pro/assets will be added to this index.

1. Create a matching entry in Kitsu for each asset via the [Kitsu Create Assets guide](https://kitsu.cg-wire.com/first_production/#create-assets)
2. Follow the [Kitsu Breakdown guide](https://kitsu.cg-wire.com/first_production/#create-a-breakdown-list) to assign/cast assets to shots.
3. Create a text [Metadata Column](https://kitsu.cg-wire.com/production_advanced/#create-custom-metadata-columns) with the exact name `slug`.
4. Populate the new `slug` column with the exact name of the asset's collection.
5. Use the [Index Assets Script](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts/index_assets) to create an `asset_index.json` file.

**Example of `asset_index.json*`*
```json
{
    "CH-rain": {
        "type": "Collection",
        "filepath": "your_project/svn/pro/assets/chars/rain/rain.blend"
    },
    "CH-snow": {
        "type": "Collection",
        "filepath": "your_project/svn/pro/assets/chars/snow/snow.blend"
    }
}
```

## Building your First Shot
Before building your first shot, you will need to customize your production's Shot Builder hooks. Inside your production’s `assets/scripts/shot-builder` directory the Shot Builder hook file should be stored, based on the [example](https://projects.blender.org/studio/blender-studio-pipeline/src/branch/main/scripts-blender/addons/blender_kitsu/shot_builder/hook_examples) included in the Add-On. This file can be automatically created at the correct directory using an operator in the **Blender Kitsu** Add-On preferences. Hooks are used to extend the functionality of the shot builder, and can be customized on a per project basis.


1. Open `Edit>Preferences>Add-Ons`
2. Search for the **Blender Kitsu** Add-On
3. In the **Blender Kitsu** Add-On preferences find the Shot Builder section
4. Run the Operator `Save Shot Builder Hook File`
5. Edit the file `your_project/svn/pro/assets/scripts/shot-builder/hooks.py` to customize your hooks.
6. Open a new Blender File, select `File>New>Shot File`
7. Select the desired Sequence/Shot from Kitsu and select OK to start Building
8. New file will be saved to  `your_project_name/svn/pro/shots/{sequence}/{shot}/{shot}.blend`

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
2. From the Sequencer Header select `Add>Movie`
3. Navigate to the directory of the playblast for your shot's .blend file `your_project_name/shared/footage/pro/{sequence_name}/{shot_name}/{file_name}` and select the `.mp4` file
4. Place the new shot at the same timing as the corresponding metastrip

## Adjusting a Shot's Frame Range
During production in some cases the frame range of a shot will change, either adjusting a shot's length or adjusting it's position in the edit. Once adjusted, we can update the shot .blend file's frame range so new playblasts will match this updated frame range. Once a new playblast is available the shot can automatically be updated in the VSE via the Blender Kitsu Add-On

1. Open your edit .blend file inside the directory `your_project_name/svn/edit`
2. Select a shot and it's metastrip, adjust the timing of both strips so they remain in sync.
3. Select your metastrip, in the Kitsu Sidebar of the VSE Under Push select `Metadata 1 Shot` to push your shot's new frame range to the Kitsu Server
4. Open your shot .blend file inside the directory
	`your_project_name/svn/pro/shots/{sequence_name}/{shot_name}/`
5. Inside the Kitsu Sidebar, under Playblast tools, if your frame range on Kitsu has changed you will see a red `Pull Frame Range` button. Select it to update the file's Frame Range
6. Adjust the shot's animation to accommodate the new frame range, then under Playblast use the `+` button to create a new version, then select `Create Playblast` to render a new playblast
7. Open your edit .blend file, and select the movie strip for the shot you would like to update.
8. In the Kitsu Sidebar under General Tools select, `^` to load the next playblast from that shot automatically

## Render Shot with Flamenco
<!--- TODO improve description --->
Once your shots are all ready to go, you can now render a final EXR from each of your shot files.

1. Open a shot file
2. In the properties panel navigate to Output, and set your file format to OpenEXR with Previews Enabled
3. In the properties panel navigate under Flamenco 
	1. Select `Fetch Job Types`
	2. From the Dropdown select `Simple Blender Render`
	3. Set Render Output Directory to `your_project_name/render/` 
	4. Set Add Path Components to `3`
	5. Finally Select `Submit to Flamenco` 

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

## Final Render
Once the approved image sequences have been loaded into the main edit you are ready to create a final render of your film. 

1. Open your Edit .blend file
2. Render Video as PNG Sequence
	1. Under `Properties>Output` Set the output directory to `your_project_name/shared/editorial/deliver/frames/`
	2. Set the File Format to `PNG`
	3. Select `Render>Render Animation` 
3. Render Audio
	1. Select `Render>Render Audio`
	2. In the Side Panel select Container `.wav`
	3. Set the output directory to `your_project_name/shared/editorial/deliver/audio/`
4. Run Deliver script
	1. Copy the `delivery.py` from `your_project_name/blender-studio-pipeline/film-delivery/` to the directory `your_project_name/shared/editorial/deliver/`
	2. Enter delivery directory `cd /your_project_name/shared/editorial/deliver/ 
	3. Encode audio with `./deliver.py --encode_audio audio/{name_of_audio}.wav`
	4. Encode video with `.deliver.py --encode_video frames/`
	5. Finally `.delivery.py --mux`
5. Final Render will be found in the `mux` directory





