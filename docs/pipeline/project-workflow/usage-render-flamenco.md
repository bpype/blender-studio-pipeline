# Render Shot

Once your first shot is animated, you are ready to render a publish of this shot, which will later be imported into your edit .blend file.

1. Open your shot .blend file by navigating to `Expo > Open Shot`.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_open_shot.jpg" width="600" alt="Invoke Open Shot" style="display: block; margin: auto;" />
</div>

2. In the Expo Side panel, under Publish, you have two options for Final Render.
<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/shot_publish.jpg" width="600" alt="Shot Publish" style="display: block; margin: auto;" />
</div>

## Render on Farm
- Use the [`Submit Farm Job`](/addons/expo-manager/shot.md#submit-farm-job) operator to submit a farm job to Flamenco. Review & Approve your render via the [Render Review](usage-render-review.md) workflow.

## Render Locally
- Use the [`Publish Render`](/addons/expo-manager/shot.md#publish-preview--publish-render) operator to render your scene locally, then [import the render into your edit](usage-import-render.md). This skips Render Review.
