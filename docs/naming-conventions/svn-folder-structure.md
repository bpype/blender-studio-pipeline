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
```
pro  
├── assets
│   ├── chars
│   │   ├── dog
│   │   ├── cat
│   │   └── ..
│   ├── props
│   │   ├── rocket_exterior
│   │   ├── wings
│   │   └── ...
│   ├── sets
│   │   ├── barn
│   │   ├── rocket_interior
│   │   └── ...
│   ├── lib
│   │   ├── rocks
│   │   ├── trees
│   │   ├── crates
│   │   └── ...
│   ├── maps
│   ├── lgt
│   ├── cam
│   ├── fx
│   ├── poses
│   ├── nodes
│   └── scripts
├── shots
│   ├── 000_titles
│   ├── 010_intro
│   ├── 020_tryout
│   ├── ...
│   ├── 900_animtest
│   └── 990_promo
└── config
pre
├── shots
└── assets
    ├── cam
    ├── char
    └── ...
dev
├── concepts
├── boards
├── tests
└── ...
.blender_project
promo
tools
```