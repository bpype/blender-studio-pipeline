# Folder Structure Overview

This page explains the standard folder structure for Blender Studio Tools projects. Consistent folder layout ensures smooth collaboration and easy onboarding for new artists.

## Typical Project Location
Projects are typically stored at `/data/your_project_name`, where `data` is at the root of the filesystem. This is for consistency between computers at the Blender Studio.  
External studios can use a different root folder, such as a user's home directory.

## Folder Descriptions
- **local/**  
  Contains a local copy of the project's Blender version and any extensions distributed by the project. Also stores `userpref.blend` for per-project user preferences.
- **shared/**  
  Symlink to a shared network drive or a synchronized folder (e.g., Syncthing, Dropbox). Used for ephemeral data such as renders, audio, and video files that can be regenerated if lost.
- **project_files/**
  Contains .blend files for production and pre-production. Recommended to use version control software (Git-LFS, or Similar) to track changes.
- **tools** Contains helper scripts to run/setup specific blender versions/addons for the project.

## Version Management Modes
There are two methods of version control for projects:

- **Version Control (Recommended):**  
  Use Git-LFS to track changes to Blender files.
- **Disk Versions:**  
  As a backup, new versions are saved in the relevant shot or asset directory when new [playblast](/artist-guide/project_tools/usage-playblast) versions are created.

_This setting can be configured when using the [Setup Assistant](/td-guide/setup_assistant.md)._

### Version Controlled Folder Layout
```bash
project_name/
    ├── local   # Local Blender & Preferences
    ├── shared  # Symlink or sync folder (Syncthing, Dropbox, etc)
    ├── project_files # Version Controlled (Git-LFS, etc)
    ├── tools         # Helper scripts and tools
    └── render  # Symlink to Render Farm Output (optional)
```
TODO
See the [`shared`](/naming-conventions/shared-folder-structure.md) and [`project files`](/naming-conventions/project-files-folder-structure.md) directory overviews for more details.

### Disk Versions Folder Layout
```bash
project_name/
    ├── local   # Local Blender & Preferences
    ├── shared  # Symlink or sync folder (Syncthing, Dropbox, etc)
    ├── project_files # Symlink or sync folder (Syncthing, Dropbox, etc)
    └── render  # Symlink to Render Farm Output (optional)
```

## Creating Folder Structure

### Root Folder
For simplicity, this guide assumes you are working within your system's **home folder**.

- **Linux/Mac:**  
  ```bash
  mkdir ~/data
  ```
- **Windows:**  
  ```bash
  mkdir %HOMEPATH%\data
  ```

Next, create the project folder and all subfolders.  
This can be handled automatically by [`setup_assistant.py`](/td-guide/setup_assistant.md) or [created manually](/td-guide/folder_structure_setup.md) via the project tools scripts.

### Full Folder Structure Overview
```bash
data/
└── project_name/
    ├── local/   # Local copy of Blender & per-project user preferences
    ├── shared/  # Symlink to a shared drive or Syncthing mount point
    │   ├── artifacts   # Project Blender stored here for distribution
    │   ├── editorial   # All footage and editorial-related data
    │   ├── audio 
    │   ├── deliver     # Final approved render of film
    │   ├── export      # Exports of edit in progress
    │   └── footage     # Renders created during shot production
    ├── project_files/ # Version controlled (Git-LFS, etc) folder containing production files
    │   ├── dev        # Visual development and tests
    │   ├── edit       # Blend files for video editing
    │   │   ├── audio
    │   │   ├── deliver
    │   │   ├── export/
    │   │   │   └── prod_code-v001.mp4 # Export of edited movie
    │   │   └── footage/
    │   │       └── SQ01/
    │   │           └── SH01/
    │   │               └── SH01-anim/
    │   │                   └── Sh01-anim-v001.blend # Render used in edit
    │   ├── pre        # Pre-production sequences
    │   ├── pro        # Main production files
    │   │   ├── assets # Assets to be used in shot production
    │   │   │   ├── cam
    │   │   │   ├── chars/
    │   │   │   │   └── Rain/
    │   │   │   │       └── Rain.blend  # Asset file
    │   │   │   ├── props
    │   │   │   └── sets
    │   │   └── shots # Shot production (animation, light, fx, etc)
    │   │       ├── dev
    │   │       ├── edit/
    │   │       │   └── prod_code-v001.blend # Editorial file
    │   │       ├── pre
    │   │       └── pro/
    │   │           └── SQ01/
    │   │               └── SH01/
    │   │                   └── SH01-anim.blend # Animation file                
    │   └── tools # Project support scripts 
    └── render # Symlink to Flamenco Render Farm Output
```