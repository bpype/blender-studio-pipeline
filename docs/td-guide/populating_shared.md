# Populating `shared`
This is the folder that should be shared over the network. (By using Syncthing, NFS shares, Samba, Dropbox, etc) Connect this folder to your sharing software of choice and create the following folder structure. More details about shared folder structure can be found [here](/naming-conventions/shared-folder-structure.md)

## Initial Directory Set-Up
1. Create your Shared Folder directly in the target directory or symlink it to`data/your_project_name/shared`. 
2. Use the following commands to generate the below folder structure.
    ```bash
    # Linux/Mac    
    cd ~/data/blender-studio-pipeline/scripts/project-tools
    init_project_folder_structure.py ~/data/your_project_name/shared --json_file folder_structure_shared.json
    ```
    ```bash
    # Windows
    cd %HOMEPATH%\data\blender-studio-pipeline\scripts\project-tools
    python init_project_folder_structure.py %HOMEPATH%\data\your_project_name\shared --json_file folder_structure_shared.json
    ```

## Add Existing Directory to User Workstation
1. Clone your SVN Folder directly into the target directory `data/your_project_name/shared`.

```bash
shared
├── artifacts # Where Global Blender & Add-Ons are stored
└── editorial   
    ├── audio # Audio
    ├── deliver # Delivery for script
    ├── export # Renders coming out of edit
    │   ├── _archive
    └── footage 
        ├── dev # Early Development
        ├── pre # Pre-Production steps like previs
        ├── pro # Playblast from Production
        └── post # Image Sequences/Final Renders
```