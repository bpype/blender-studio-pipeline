## Kitsu Casting
Casting is the process of associating a Kitsu Asset Entity with a given shot. This is how the Shot Builder knows which assets to link into a given shot.
- Please follow the [Kitsu Breakdown](https://kitsu.cg-wire.com/getting-started-production/) guide to cast your assets to shots.

## Building Your First Shot

1. Open a new Blender file and select `Project > New Shot`.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/invoke_new_shot.jpg" width="600" alt="Invoke New Shot" style="display: block; margin: auto;" />
</div>

2. Select the desired sequence/shot from Kitsu and click OK to start building.

<div style="padding: 12px; background: var(--color-bg-secondary, transparent); border-radius: 8px; margin-bottom: 20px;">
    <img src="/media/artist-guide/project_tools/draw_new_shot.jpg" width="600" alt="Draw New Shot" style="display: block; margin: auto;" />
</div>

3. The new file will be saved to `your_project_name/svn/pro/shots/{sequence}/{shot}/{shot}.blend`.

::: info Shot Builder Hooks 
Use the `Save Shot Builder Hook File` operator in the **Blender Kitsu** Add-on preferences.

Edit the file `your_project/svn/pro/assets/scripts/shot-builder/hooks.py` to customize.
:::
