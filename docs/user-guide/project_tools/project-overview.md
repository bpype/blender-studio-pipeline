# Project Overview

## Introduction
"Project Tools" is a collection of scripts included in the [Blender Studio Pipeline](https://projects.blender.org/studio/blender-studio-pipeline) repository, developed to assist you in running and managing one or more projects. These scripts automate and standardize many common operations involved in setting up a production pipeline. 

It all starts with the directory layout, which should be deployed by a Technical Director following the [Project Tools Setup Guide](/td-guide/project-tools-setup.md). This standard directory layout defines where things like .blend files and playblasts are stored. It enables project tools the ability to ensure all users are running the same Blender and have a similar experience with minimal setup required by the individual users.


## Directory Layout

Typically projects are stored at the following path `/data/your_project_name` where `data` is at the root of the filesystem. This is for consistency between computers at the Blender Studio. External studios can use a different root folder for their projects for example a user's home folder.

The project folder contains all data related to a project including .blend files, playblasts, the blender that is used on the project for all operating systems and even preferences are stored within the project. 

 * `local` This is where the local copy of Blender and the add-ons will be installed. This directory is populated by the `run_blender.py` script with the Blender & Add-Ons from `shared`.
 * `shared` This is the folder that should be shared over the network, it contains renders, playblast and other items that don't require version control. (By using Syncthing, NFS shares, Samba, Dropbox, etc)
 * `svn` This the versioned controlled folder where the .blend production files will live.

```bash
.
└── my_project/
    ├── local # The local copy of Blender and the add-ons will be installed.
    ├── shared # Shared over the network (Syncthing, NFS, Dropbox, etc)
    └── svn # Contains the `.blend` production files. (SVN, GIT-LFS, etc)
```

To learn the layout of the above directories, see the [`shared`](/naming-conventions/shared-folder-structure.md) and [`svn`](/naming-conventions/svn-folder-structure.md) directory overviews.
