
## Creating your first Asset
The next step is to create an asset and store that information into the Kitsu Server.

1. Launch Blender via [Project Blender](/artist-guide/project_tools/project-blender.md) Guide
2. Under `Edit>Preferences>Add-Ons` ensure `Asset Pipeline` is enabled
3. Follow the [asset pipeline guide](https://studio.blender.org/pipeline/addons/asset_pipeline) to create a new asset collection, ensure these assets are marked as an [Asset in Blender](https://docs.blender.org/manual/en/latest/files/asset_libraries/introduction.html#creating-an-asset).
4. Save the above asset within the directory `your_project_name/svn/pro/assets/char` (or similar depending on type)

## Kitsu Casting
Casting is the process of associating a Kitsu Asset Entity with a given shot, this is how the Shot Builder knows what Assets to link into a given shot. 
1. Please follow the [Kitsu Breakdown](https://kitsu.cg-wire.com/getting-started-production/) guide to Cast your assets to shots.


## Load Asset Data into Kitsu
To match Assets File to the casting breakdown on the Kitsu server, we need to tag the Asset with a filepath and collection. This can be done via the Blender Kitsu Add-On. This data will be used to match a Kitsu Asset with a Collection within a .blend file, that will be linked into all shots that have that Asset "casted in it". 

1. Open the file for a given Asset.
2. Under the Kitsu>Context Panel, check the following settings.
    - **Type** is set to Asset. 
    - **Asset Type** is set to the correct Asset Type (Collection, Prop, etc) 
    - **Asset** Field is set to the matching entry on the Kitsu server for the current file.
3. Under the Kitsu>Context>Set Asset sub-panel...
    - **Collecton**  is set to the Asset's parent collection.
    - Run the **Set Kitsu Asset** operator to send the current filepath and selected collection to the Kitsu Server. 


![Set Kitsu Asset](/media/pipeline-overview/shot-production/kitsu_set_asset.jpg)

If you are using the Asset Pipeline, the latest publish file will be prompted to confirm using the latest Publish as the Asset target. 

![Publish Asset Pipeline with Set Kitsu Asset](/media/pipeline-overview/shot-production/kitsu_asset_with_asset_pipeline.jpg)

You should now see the filepath and collection under the Asset's Metadata on the Kitsu.

![Kitsu Asset Metadata](/media/pipeline-overview/shot-production/kitsu_asset_metadata.jpg)
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