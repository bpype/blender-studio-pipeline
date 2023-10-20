# Shared Folder Structure

::: warning Work in Progress
October 20th 2023 - The content of this page is currently being edited/updated.
:::

The shared folder is manly meant for content that should not be stored in SVN. In particular,
the `footage` folder contains all the previews and renders for the work being done on sequences
and shots. The data inside those folders is grouped according to the type of deliverable.
For example, sequences are delivered in the `sequences` directory, shots are delivered in the
`shots` directory.

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
