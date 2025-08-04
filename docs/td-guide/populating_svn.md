# Populating `SVN`

This folder should contain a version-controlled file system to be shared over the network (using SVN, GIT-LFS, etc.). Connect this folder to your version control software of choice and create the following folder structure. More details about the shared folder structure can be found [here](/naming-conventions/svn-folder-structure.md).

## Initial Directory Set-Up

1. Follow the [SVN-Setup guide](/td-guide/svn-setup.md) to create your SVN repository **before** populating the directory with folders. *(Optional)*
2. Use the following commands to generate the folder structure below.
    ```bash
    # Linux/Mac
    cd ~/data/blender-studio-tools/scripts/project-tools
    ./init_project_folder_structure.py ~/data/your_project_name/svn --json_file folder_structure_svn.json
    ```
    ```bash
    # Windows
    cd %HOMEPATH%\data\blender-studio-tools\scripts\project-tools
    python init_project_folder_structure.py %HOMEPATH%\data\your_project_name\svn --json_file folder_structure_svn.json
    ```

## Add Existing Directory to User Workstation

1. Clone your SVN folder directly into the target directory `data/your_project_name/svn`.

```bash
.
└── svn/
    ├── dev/        # Anything related to early development or tests
    │   ├── boards
    │   ├── concepts
    │   └── tests
    ├── pre/        # For pre-production
    │   ├── assets
    │   └── shots
    ├── edit        # Where the editorial .blend file lives
    ├── pro/        # All files from the production
    │   ├── assets/     # All assets from the production
    │   │   ├── cam     # Camera rig & setup
    │   │   ├── chars   # Characters & character variations
    │   │   ├── fx      # Effects
    │   │   ├── lgt     # Lighting setups
    │   │   ├── lib
    │   │   ├── maps    # General textures and HDRIs
    │   │   ├── nodes   # General Node groups
    │   │   ├── poses   # Pose libraries for animation
    │   │   ├── props
    │   │   ├── scripts
    │   │   └── sets
    │   ├── config
    │   └── shots       # Structured into sequences
    └── tools
```