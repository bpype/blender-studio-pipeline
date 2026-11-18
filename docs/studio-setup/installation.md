# Installation

This guide will walk you through the steps to set up a new project on a new machine. It provides a brief overview of the steps required to set up a new project and deploy it to artist workstations. Follow the links in this guide to learn more about each step.

---

1. **Install Python**
   Ensure [Python 3.11+](python.md) and its dependencies are installed.

2. **Set Up Kitsu**
   Set up the [Kitsu](/studio-setup/kitsu_server.md) server and project.

3. **Create Project Folders**
   Follow the [Project Folder Setup](/tools/scripts/project-tools/folder_structure_setup.md) guide to create the required project directories.

4. **Prepare Project Folders**
   Ensure project folders are accessible on artist workstations:
   - **Version Control Software:**
   Set up a [`Git`](git-setup.md) repository and a [`Shared`](syncthing-setup.md) folder according to the [Folder Structure](folder_structure_overview#version-controlled-folder-layout), and make them available on artist workstations.
   - **Disk Versioning:**
     Mount both the `Project Files` and `Shared` directories according to the [Folder Structure](folder_structure_overview#disk-versions-folder-layout) on all artist workstations via network file share or [file sync](syncthing-setup.md).

5. **Install Expo Manager**
   Install and configure the [Expo Manager add-on](/addons/expo-manager/introduction.md) in Blender. To use disk versions instead of version control, enable `version_backups` in the [project configuration](/addons/expo-manager/configuration.md#project-settings).

6. **Set Up Flamenco**
   Set up the [Flamenco](flamenco_setup.md) Server.

---
