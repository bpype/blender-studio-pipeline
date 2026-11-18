# Asset
<!-- Assets automatically appear in Blender's native [Asset Library](https://docs.blender.org/manual/en/latest/editors/asset_browser.html). TODO Add automatic asset libraries before writing this-->
The Asset Task maps to the [Asset entity on Kitsu](https://kitsu.cg-wire.com/guides/production/manage-assets/#managing-assets).

The `patterns.Asset` section defines Asset file and Publish paths; see [Pattern Tokens](configuration.md#pattern-tokens).

## Set Asset Collection
Assets are automatically linked into Shots during the [Shot building](file_builder.md#shot-building) process. To do this, Expo needs to store the file path and target collection on the Kitsu server per Asset.

1. Use `Expo > New Asset` at the top of Blender to create a new Asset file.

![Set Asset Panel](/media/addons/expo_manager/topmenu_new_asset.jpg)

2. In the `Set Asset` panel, select the Asset's parent collection and run `Set Kitsu Asset` to send the collection name and project-relative file path to Kitsu.

![Set Asset Panel](/media/addons/expo_manager/asset_set_asset.jpg)


3. [Cast the Asset to Shots](/pipeline/project-workflow/usage-build-shot.md#kitsu-casting) on Kitsu. The [Shot Builder](file_builder.md#shot-building) uses the casting and saved metadata to link it when building those Shots.

When Expo builds a new Asset file, it creates an asset collection and registers its name and file path on Kitsu. Use `Set Kitsu Asset` to register a different collection or an existing Asset file.

The `asset_type_to_override` [Shot Builder setting](configuration.md#shot-builder) controls whether a cast Asset Type (e.g. prop or character) is linked with a library override, based on the registered collection name.

## Publish
Create a Publish for the Asset Task on Kitsu directly from your blend file. This creates a [Publish revision and comment](https://kitsu.cg-wire.com/guides/review-publishing/publish/#publish-a-preview-as-a-version) on the specified Kitsu Task. If publishing backups are enabled, this also creates a [backup version](backups.md).

![Asset Publish](/media/addons/expo_manager/asset_publish_preview.jpg)

- **Publish Type**: Select either *Image* or *Video* mode. Most Assets only require an image, but video may be useful for turnarounds or test animations.
- **Task Type**: The Asset file maps only to the Asset entity. When publishing, you can select the Task Type (e.g. modeling or shading) for the Publish.
- **Status**: Set your Task's status (Done, WIP, Retake, etc.), which will appear in the comment alongside your Publish revision.
- **Comment**: Add details to accompany your Publish.
- **Render Mode**: Choose either *Scene* or *Viewport* rendering. Viewport uses what you see in the 3D viewport; Scene matches the output of `Render Image`.
