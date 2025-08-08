# Populating `shared`

This is the folder that should be shared over the network (using Syncthing, NFS shares, Samba, Dropbox, etc.). Connect this folder to your sharing software of choice and create the following folder structure. More details about the shared folder structure can be found [here](/naming-conventions/shared-folder-structure.md).

## Initial Directory Set-Up

1. Create your shared folder directly in the target directory or symlink it to `data/your_project_name/shared`.
2. Use the following commands to generate the folder structure below.
    ```bash
    # Linux/Mac    
    cd ~/data/blender-studio-tools/scripts/project-tools
    ./init_project_folder_structure.py ~/data/your_project_name/shared --json_file folder_structure_shared.json
    ```
    ```bash
    # Windows
    cd %HOMEPATH%\data\blender-studio-tools\scripts\project-tools
    python init_project_folder_structure.py %HOMEPATH%\data\your_project_name\shared --json_file folder_structure_shared.json
    ```

## Add Existing Directory to User Workstation

1. Clone your shared folder directly into the target directory `data/your_project_name/shared`.

```bash
shared
├── artifacts   # Where global Blender & add-ons are stored
└── editorial   
    ├── audio      # Audio
    ├── deliver    # Delivery for script
    ├── export     # Renders coming out of edit
    │   ├── _archive
    └── footage 
        ├── dev    # Early development
        ├── pre    # Pre-production steps like previs
        ├── pro    # Playblast from production
        └── post   # Image sequences/final renders
```