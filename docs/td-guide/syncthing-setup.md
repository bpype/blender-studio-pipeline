# Syncthing Setup

## Install Syncthing
The Blender Studio Pipeline relies on [Syncthing](https://syncthing.net/) to sync large files like renders and playblasts used in production. This guide will show you how to install Syncthing on a workstation, assuming you already have a Syncthing server set up. To learn more about how to set up a shared server, visit the [Syncthing Documentation](https://docs.syncthing.net/intro/getting-started.html).

### Linux/Mac

**Debian/Ubuntu**  
Install the latest Syncthing packages via the official [Syncthing Repository](https://apt.syncthing.net/).

**Other Linux Distributions**  
Get the [latest release](https://github.com/syncthing/syncthing/releases/tag/v1.27.2) for your distribution.

### Windows
Syncthing can be installed on Windows with the official [Syncthing Installer](https://github.com/Bill-Stewart/SyncthingWindowsSetup/) by following [this video](https://www.youtube.com/watch?v=2QcO8ikxzxA&ab_channel=UsefulVid), but it is recommended for novice users to use the community-contributed package [SyncTrayzor](https://github.com/canton7/SyncTrayzor).

Download and install the latest version of [SyncTrayzor](https://github.com/canton7/SyncTrayzor#installation).

## Setup Syncthing

1. Launch the Syncthing Web GUI:
    - Browser: The default address for the web GUI is `127.0.0.1:8384`
    - Linux: Find "Syncthing Web UI" in the application launcher
    - Windows: Right-click the SyncTrayzor icon in the system tray and select `Open SyncTrayzor`
    ![Launch syncthing GUI via tray (windows)](/media/td-guide/syncthing_tray_windows.jpg)

2. Select `+ Add Remote Device` and enter the Device ID of the Syncthing server.
    ![Add Remote Device](/media/td-guide/syncthing_new_device.jpg)
3. On the server's Web GUI, select `+ Add Device` from the "New Device" pop-up.
    ![Add Device to Server](/media/td-guide/syncthing_new_device_server.jpg)
4. In the "Add Device" pop-up, under "Sharing," select the folder(s) to share.
    ![Share Folder from Server](/media/td-guide/share_folder_server.jpg)
5. Return to the client's Web GUI and select `Add` from the "New Folder" pop-up.
    ![Add New Folder from Server](/media/td-guide/add_new_folder.jpg)
6. Enter the following path under **Folder Path**: `~/data/your_project_name/shared`.
    ![New Folder Settings](/media/td-guide/new_folder_settings.jpg)
    *The tilde "~" will be replaced with the home path for your operating system.*
7. Select save to begin syncing your "Shared" folder.