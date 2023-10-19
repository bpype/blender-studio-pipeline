# Shared Folder Structure

::: warning Work in Progress
October 17th 2023 - The content of this page is currently being edited/updated.
:::

<!---
TODO Add logic & Introduction
--->

```bash
shared
├── artifacts # Where Global Blender & Add-Ons are stored
└── editorial
    ├── audio # Audio
    ├── deliver # Delivery for script
    ├── export # Renders coming out of edit
    │   ├── _archive
    │   │   └── gold-edit-v001_storyboard.mp4
    │   ├── gold-edit-v001_previs.mp4
    └── footage
        ├── sequences # Sequence Playblasts / Renders
        │   ├── 010_intro
        │   │   ├── 010_intro-beats
        │   │   │   └── 010_intro-beats-v001.mp4
        │   │   └── 010_intro-storyboards
        │   │       └── ...
        │   └── 020_water
        │       └── ...
        ├── shots # Playblasts and Render Previews
        │   ├── 010_intro
        │   │   └── 010_0010
        │   │       ├── 010_0010-previs
        │   │       │   └── 010_0010-previs-v001.mp4
        │   │       │       └── ...
        │   │       └── 010_0010-animation
        │   │           └── 010_0010-animation-v001.mp4
        │   │               └── ...
        │   └── 020_water
        │       └── ...
        └── frames # Render Review Output
            └── 010_intro
                └── 010_0010


```
