# Index Assets

This tool will create a dictionary of all data-blocks (collections only) [marked as an Asset](https://docs.blender.org/manual/en/latest/files/asset_libraries/introduction.html#asset-create) and stores this information in a JSON file at `you_project/svn/pro/assets/asset_index.json`. This JSON File is used by other tools like the Blender Kitsu Add-On to quickly discover assets to use in the shot builder.

To run this tool use the following command, followed by the path to your project's root folder

```bash
./run_index_assets.py your_project/
```

