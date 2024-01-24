
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