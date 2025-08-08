# Creating Your First Asset

The next step is to create an asset and store that information on the Kitsu Server. If you are using the Asset Pipeline Add-On, see the [Asset Pipeline Guide](https://studio.blender.org/tools/addons/asset_pipeline).

1. If you haven't already, ensure your project settings are set up: [Blender Kitsu Add-On Preferences](https://studio.blender.org/tools/addons/blender_kitsu#how-to-get-started).
2. Follow the Kitsu [New Asset Guide](https://kitsu.cg-wire.com/short/#create-an-asset) to create your asset on the Kitsu Server.
3. Navigate to `Project > New Asset` in the header or `File > New > Asset File` to create a new asset file.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/invoke_new_asset.jpg" width="600" alt="Invoke New Asset" style="display: block; margin: auto;" />
</div>

4. Select an Asset Type and Asset in the Operator Pop-Up. Your asset file will open.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/draw_new_asset.jpg" width="600" alt="Draw New Asset" style="display: block; margin: auto;" />
</div>

5. Under the Kitsu > Context > Set Asset sub-panel:
    - **Collection** is set to the asset's parent collection.
    - Run the **Set Kitsu Asset** operator to send the current filepath and selected collection to the Kitsu Server.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/kitsu_set_asset.jpg" width="600" alt="Set Kitsu Asset" style="display: block; margin: auto;" />
</div>

 - You should now see the filepath and collection under the asset's metadata on Kitsu.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/kitsu_asset_metadata.jpg" width="600" alt="Kitsu Asset Metadata" style="display: block; margin: auto;" />
</div>


6. Your new Asset file will be saved to `your_project_name/svn/pro/assets/{asset_type}/{asset_name}/{asset_name}.blend`.
