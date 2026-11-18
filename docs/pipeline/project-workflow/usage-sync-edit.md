# Prepare Edit

Most productions begin with a previz or storyboard step, showing the overall direction and plan for the production. By inputting this as video strip(s) into a VSE file, you can automatically create the corresponding shots on the Kitsu Server directly from the VSE.

1. If not already done, ensure your project settings are set up in [Expo Add-On Preferences](/addons/expo-manager/introduction.md#setting-add-on-preferences).
2. Navigate to `Expo > New Edit` in the header or `File > New > Edit File` to create a new Edit file.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_new_edit.jpg" width="600" alt="Invoke New Edit" style="display: block; margin: auto;" />
</div>

3. The operator provides the option to automatically create an Edit task if it doesn't already exist on your Kitsu server.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/edit_new_draw.jpg" width="600" alt="Draw New Edit" style="display: block; margin: auto;" />
</div>

4. Populate your new edit file with your previz or storyboard.
5. Use the [`Bulk Rename`](/addons/expo-manager/edit.md#bulk-rename) Operator to set the naming for your strips by their Shot names. Each Shot on needs to be associated with a sequence. If needed you can create a sequence on the Kitsu server if you haven't created one yet.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/edit_bulk_rename_full.jpg" width="600" alt="New Metadata Strip" style="display: block; margin: auto;" />
</div>

6. With your renamed strips selected, use the [`Create Shots`](/addons/expo-manager/edit.md#create-shots) operator to populate matching Kitsu Shot entities per strip (using the strip name as the Shot name).

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/edit_create_shots_full.jpg" width="600" alt="New Metadata Strip" style="display: block; margin: auto;" />
</div>
