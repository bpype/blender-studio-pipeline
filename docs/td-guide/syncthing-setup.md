# Syncthing Setup

## Install Syncthing
The Blender Studio Pipeline relies on [syncthing](https://syncthing.net/) to sync large files like Renders and Playblasts used in production. This guide will show you how to install an Syncthing on a workstation, assuming you already have an Syncthing server setup. To learn more about how to setup an Shared server visit the [Syncthing Documentation](https://docs.syncthing.net/intro/getting-started.html)
### Linux/Mac

**Debian/Ubuntu**
Install the latest Syncthing Packages via the official [Syncthing Repository](https://apt.syncthing.net/)

**Other Linux Distrubutions**
Get the [latest release](https://github.com/syncthing/syncthing/releases/tag/v1.27.2) for your distribution.

### Windows
Syncthing can be installed on windows with the official [Syncthing Installer](https://github.com/Bill-Stewart/SyncthingWindowsSetup/) by following [this video](https://www.youtube.com/watch?v=2QcO8ikxzxA&ab_channel=UsefulVid) but it is recommended for novice users to use the Community Contributed package [SyncTrayzor](https://github.com/canton7/SyncTrayzor)

Download and Install the latest version of [SyncTrazor](https://github.com/canton7/SyncTrayzor#installation)

## Setup Syncthing

1. Launch Syncthing Web GUI
    - Browser: The default address for web GUI `127.0.0.1:8384`
    - Linux: Find "Syncthing Web UI" in Application Launcher
    - Windows: Right Click SyncTrazor icon in the system tray and select  `Open SyncTrazor`
    ![Launch syncthing GUI via tray (windows)](/media/td-guide/syncthing_tray_windows.jpg)


2. Select `+ Add Remote Device` and enter the Device ID of the Syncthing Server
    ![Add Remote Device](/media/td-guide/syncthing_new_device.jpg)
3. On the Server's Web GUI, select `+ Add Device` from the "New Device" pop-up.
    ![Add Device to Server](/media/td-guide/syncthing_new_device_server.jpg)
4. In the "Add Device" pop-up under "Sharing" select the folder(s) to share.
    ![Share Folder from Server](/media/td-guide/share_folder_server.jpg)
5. Return to the Client's Web GUI, select `Add` from the "New Folder" pop-up
    ![Add New Folder from Server](/media/td-guide/add_new_folder.jpg)
6. Enter the following path under **Folder Path** `~/data/your_project_name/shared`. 
    ![New Folder Settings](/media/td-guide/new_folder_settings.jpg)
    *The tilde "~" will be replaced with the home path for your operating system*
7. Select save to being syncing your "Shared" Folder