# Creating Your First Asset

The next step is to create an Asset and store its information on the Kitsu server. If you are using the Asset Pipeline Add-on, see the [Asset Pipeline Guide](https://studio.blender.org/tools/addons/asset_pipeline).

1. Follow the Kitsu [New Asset Guide](https://kitsu.cg-wire.com/guides/production/manage-assets/#managing-assets) to create your Asset on the Kitsu server.
2. Navigate to `Expo > New Asset` in the header or `File > New > Asset File` to create a new Asset file.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_new_asset.jpg" width="600" alt="Invoke New Asset" style="display: block; margin: auto;" />
</div>

3. Select an Asset Type and Asset in the operator pop-up. Your Asset file will open.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/asset_new.jpg" width="600" alt="Draw New Asset" style="display: block; margin: auto;" />
</div>

4. In the Expo sidebar, open the Set Asset panel:
    - **Collection** is set to the Asset's parent collection.
    - Run the **Set Kitsu Asset** operator to send the current file path and selected collection to the Kitsu server.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/asset_set.jpg" width="600" alt="Set Kitsu Asset" style="display: block; margin: auto;" />
</div>

You should now see the file path and collection in the Asset's metadata on Kitsu.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/kitsu_asset_metadata.jpg" width="600" alt="Kitsu Asset Metadata" style="display: block; margin: auto;" />
</div>
