# Shared Folder Structure

The shared folder is mainly meant for content that should not be stored in SVN. In particular,
the `footage` folder contains all the previews and renders for the work being done on sequences
and shots. The `footage` folder contains directories named after the different produciton
stages (dev, pre, pro and post). This helps to keep track of data depending on its production
stage. The directory structure inside each directory is similar:

```bash
<sequence identifier>
├── sequence_previews # Videos for review
├── thumbnails # Loose frames that can be combined in any order
└── [<shot identifier>] # Individual shots that make up the sequence
```

```bash
shared
├── artifacts # Where Global Blender & Add-Ons are stored
└── editorial
    ├── audio
    ├── deliver
    ├── export # Renders coming out of edit
    │   ├── _archive
    │   │   └── gold-edit-v001_storyboard.mp4
    │   └── gold-edit-v001_previs.mp4
    └── footage
        ├── dev
        │   └── 010_intro
        │       ├── sequence_previews
        │       │   └── 010_intro-beats-v001.mp4
        │       └── thumbnails
        │           └── 010_intro-beats-001.jpg
        ├── pre
        │   ├── 010_intro
        │   │   ├── thumbnails
        │   │   │   ├── 010_intro-001.jpg
        │   │   │   ├── 010_intro-002.jpg
        │   │   │   └── ...
        │   │   ├── sequence_previews
        │   │   │   ├── 010_intro-previs-v001.mp4
        │   │   │   ├── 010_intro-previs-v001_weekly.mp4
        │   │   │   └── ...
        │   │   └── 010_0100
        │   │       ├── 010_0100-previs
        │   │       │   ├── thumbnails
        │   │       │   │   └── 010_0010-previs-001.jpg
        │   │       │   ├── 010_0010-previs-v001.mp4
        │   │       │   ├── 010_0010-previs-v002.mp4
        │   │       │   └── ...
        │   │       └── 010_0100-storyboard
        │   │           ├── thumbnails
        │   │           │   ├── 010_0010-storyboard-001.jpg
        │   │           │   └── ...
        │   │           └── 010_0010-storyboard-v001
        │   │               ├── 010_0010-storyboard-v001-001.jpg
        │   │               └── ...
        │   ├── 070_explosion
        │   └── 090_explosion
        ├── pro
        │   ├── 010_intro
        │   │   └── 010_0010
        │   │       ├── 010_0010-animation
        │   │       │   ├── 010_0010-animation-v001.mp4
        │   │       │   └── ...
        │   │       └── 010_0010-lighting
        │   │           ├── 010_0010-lighting-v001.mp4
        │   │           └── ...
        │   ├── 070_explosion
        │   └── 099_happy
        └── post
            └── 010_intro
                └── 010_0010
                    └── 010_0010-lighting
                        ├── 000001.exr
                        └── ...

```
