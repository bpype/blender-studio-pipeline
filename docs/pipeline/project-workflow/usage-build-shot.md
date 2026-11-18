# Building Shots

## Kitsu Casting
Casting is the process of associating a Kitsu Asset Entity with a given shot. This is how the Shot Builder knows which assets to link into a given shot.
- Please follow the [Kitsu Breakdown](https://kitsu.cg-wire.com/guides/production/breakdown-casting/) guide to cast your assets to shots.

## Building Your First Shot

1. Open a new Blender file and select `Expo > New Shot`.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/topmenu_new_shot.jpg" width="600" alt="Invoke New Shot" style="display: block; margin: auto;" />
</div>

2. Select the desired sequence, shot, and task type from Kitsu and click OK to start building.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/addons/expo_manager/shot_new.jpg" width="600" alt="Draw New Shot" style="display: block; margin: auto;" />
</div>


- Builder will automatically link Assets, based on Kitsu Casting Breakdown
- Builder will load the latest editorial publish as a reference movie if available and enabled for the task type in the project configuration.
- Customize the builder's behavior using [Shot Builder hooks](/addons/expo-manager/file_builder.md#shot-building).
