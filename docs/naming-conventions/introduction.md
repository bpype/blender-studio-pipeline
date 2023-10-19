# Naming Conventions

Naming things well is notoriousy difficult, mostly because a name that works well within one context, does not communicate as well in another. Here are the guidelines that we try to follow at Blender Studio when it comes to file naming.

* *No caps, no gaps*: name files with lowercase letter and avoid whitespaces.
* No special characters like +=#^*&^$()?!
* Underscores are allowed as spacing, dashes to separate items.
* Retain a sense of hierarchy within the file name, from wide to narrow context.
* We use dot notations to specify a different representation or variant of an asset.

## Versions and variations for file naming

`{show_prefix:optional}-{type:only for assets}-{name}.{variant:optional}-{task}-v{version:optional}_{version_info:optional}.{extension}`

- **type** (char, set, lib, props) of asset - not for shots
    - **variant** (voice, red, blurry) changes meaning of the content > only for exports and renders, not for work files
        - **version** (v001, v002) only for renders and exports, not for work files as they have a history on the SVN
            - **version_info** (720p, lowres, cache) the content is the same


## Asset file names

Examples:
* `char-gabby-concept.blend`
* `char-gabby-shading-v001.mp4` > we add the `{version}` because it is an export/render, like a turntable
* `char-gabby-rigging.blend`
* `char-gabby.red-shading-v006.png` > we can include the `.{variant}` because it is an export/render
* `lib-sea_shells-design-v001.kra`
* `lib-sea_shells.broken-modeling-v006.png` > we can include the `.{variant}` because it is an export/render

The main asset files should be as simple as possible, however we have decided to make it longer than our previous system, to better classify and structure them: `{type}-{asset name}-{task}.blend`

These main asset files are meant to be written by our asset pipeline, but should rarely be touched by hand (other than solving errors).

We use task identifiers to distinguish between the different stages of the asset:

- reference
- concept
- design
- sculpting
- modeling
- shading
- rigging

## Shot identifier

Example: `010_0030`
```
010_0030
─┬─ ─┬──
 │   └──► Shot: 4 digits, incremented by 10 at creation
 └──► Sequence: 3 digits, incremented by 10 at creation
 ```

## Shot file name

Example: `140_0010-anim.blend`

```
010_0030-anim.blend
─┬─ ─┬── ──┬─
 │   │     └──► Task (layout, anim, lighting, comp, fx, sim_hair, etc.)
 │   └────────► Shot
 └────────────► Sequence
```

Its position in the repository would be at:

`svn/pro/shots/140_credits/140_0010/140_0010-anim.blend`

