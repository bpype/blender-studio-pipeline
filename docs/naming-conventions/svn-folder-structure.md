# SVN Folder Structure

::: warning Work in Progress
October 17th 2023 - The content of this page is currently being edited/updated.
:::

## Logic

* ‘pre’ folder: like a sandbox, can be messy
* ‘pro’ folder should be the very structured one
* Keep the structure as simple as possible, with assets / shots / others
* Inside an asset folder:
    * `blend` file
    * `published` folder
    * `maps` folder

## Proposal adopted in October 2023:
``` bash
svn
├── pro # All files from the production
│   ├── assets # All assets from the production
│   │   ├── chars # Characters & character variations
│   │   │   ├── dog
│   │   │   ├── cat
│   │   │   └── ..
│   │   ├── props # Rigged props that can have animation
│   │   │   ├── rocket_exterior
│   │   │   ├── wings
│   │   │   └── ...
│   │   ├── sets # Static background elements
│   │   │   ├── barn
│   │   │   ├── rocket_interior
│   │   │   └── ...
│   │   ├── lib # Libraries of smaller assets
│   │   │   ├── rocks
│   │   │   ├── trees
│   │   │   ├── crates
│   │   │   └── ...
│   │   ├── maps # General textures and HDRIs
│   │   ├── lgt # Lighting setups
│   │   ├── cam # Camera rig
│   │   ├── fx # Effects
│   │   ├── poses # Pose libraries for animation
│   │   ├── nodes # General Node groups
│   │   └── scripts
│   ├── shots
│   │   ├── 000_titles
│   │   ├── 010_intro
│   │   ├── 020_tryout
│   │   ├── ...
│   │   ├── 900_animtest
│   │   └── 990_promo
│   └── config
├── pre # For pre-production
│   ├── shots # Structured into sequences
│   └── assets
│       ├── cam
│       └── ...
│       ├── char
├── dev # Anything related to early development or tests
│   ├── concepts
│   ├── boards
│   ├── tests
│   └── ...
├── edit # Where the editorial .blend file lives
│   └── my_project_edit_v001.blend
├── .blender_project
├── promo
└── tools
```
