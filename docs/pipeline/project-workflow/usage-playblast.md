# Publish Shot

Once your first shot is animated, you are ready to render a publish of this shot, which will later be imported into your edit .blend file.

1. Open your shot .blend file by navigating to `Expo > Open Shot`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_open_shot.jpg" width="600" alt="Invoke Open Shot" style="display: block; margin: auto;" />
</div>

2. In the Expo Side panel, under Publish, use the [`Publish Preview`](/addons/expo-manager/shot.md#publish-preview--publish-render) operator to create a preview render of your shot and add it as a comment on your Kitsu Task for this shot:
	1. **Status:** Select the status to set your Kitsu Task to.
	2. **Comment:** Add any notes you would like to include in your comment.
	3. **Render Mode:** Choose viewport or scene rendering.
	4. **Thumbnail Frame:** Choose which frame in your current file should be the thumbnail for your preview file.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/shot_playblast.jpg" width="600" alt="Draw publish" style="display: block; margin: auto;" />
</div>

::: info Version Management
If you are using [Git](/pipeline/operations/git-usage.md) or similar version control software, it is recommended to create a new commit at the time of publish. If you are not using version control software, see Expo [Backups](/addons/expo-manager/backups.md).
:::
