# Quick Start

This guide will walk you through the steps to set up a new project on a new machine. It provides a brief overview of the steps required to set up a new project and deploy it to artist workstations. Follow the links in this guide to learn more about each step.

---

## 🚀 Quick Start

1. **Install Python**  
   Ensure [Python 3.11+](python.md) and its dependencies are installed.

2. **Set Up Kitsu**  
   Set up the [Kitsu](/td-guide/kitsu_server.md) Server & Project.

3. **Run Setup Assistant**  
   Download and run the [Setup Assistant](setup_assistant.md) to initialize your project.

4. **Prepare Project Folders**  
   Ensure project folders are accessible on artist workstations:
   - **Version Control Software:**  
     Set up an [`SVN`](svn-setup.md) repository and a [`Shared`](syncthing-setup.md) folder according to the [Folder Structure](folder_structure_overview#version-controlled-folder-layout), and install them on artist workstations.
   - **Disk Version:**  
     Mount both the `SVN` and `Shared` directories according to the [Folder Structure](folder_structure_overview#disk-versions-folder-layout) on all artist workstations via network file share or [file sync](syncthing-setup.md).

5. **Run Deployment Assistant**  
   Run the [Deployment Assistant](deployment_assistant.md) on artist workstations to finalize configuration.

6. **Set Up Flamenco**  
   Set up the [Flamenco](flamenco_setup.md) Server.

---