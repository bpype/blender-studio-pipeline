# Populating `Project Files`

This folder should contain version-controlled files (using Git LFS or similar) or be shared over the network for disk-based versioning. Connect it to your chosen version control system and create the folder structure below. See the [Project Files folder structure](/naming-conventions/project-files-folder-structure.md) documentation for details.

## Initial Directory Set-Up

1. Follow the [Git Setup Guide](/td-guide/git-setup.md) to create your Git repository **before** populating the directory with folders. *(Skip if using Disk Versions)*
2. Use the following commands to generate the folder structure below.
    ```bash
    # Linux/Mac
    cd ~/data/blender-studio-tools/scripts/project-tools
    ./init_project_folder_structure.py ~/data/your_project_name/project_files --json_file folder_structure_project_files.json
    ```
    ```bash
    # Windows
    cd %HOMEPATH%\data\blender-studio-tools\scripts\project-tools
    python init_project_folder_structure.py %HOMEPATH%\data\your_project_name\project_files --json_file folder_structure_project_files.json
    ```


```bash
.
└── project_files/
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