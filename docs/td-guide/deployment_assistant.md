---
next: 
  text: "Flamenco"
  link: "td-guide/flamenco_setup"
---

# Deployment Assistant

The `deployment_assistant.py` script finalizes your Blender Studio Tools project after initial setup with `setup_assistant.py`. It configures Blender, installs extensions, and prepares the project for artists.

## ⚙️ What Does the Script Do?

- **Updates extensions**  
  Ensures the latest add-ons are installed for your project.

- **Configures Blender**  
  Sets up Blender with the correct version and preferences.

- **Saves Kitsu credentials**  
  Stores login info for seamless artist experience.

- **Creates desktop shortcut**  
  (Linux only) Adds a launcher for easy project access.


## 🚀 Quick Start

1. **Navigate to the tools directory**  
   - **Linux/Mac:**  
     ```bash
     cd ~/data/your_project_name/svn/tools
     ./deployment_assistant.py
     ```
   - **Windows:**  
     ```bash
     cd %HOMEPATH%\data\your_project_name\svn\tools
     python deployment_assistant.py
     ```

2. **Follow the prompts**  
   The script will guide you through the deployment steps.

---

## 🖥️ Interactive Deployment Walkthrough

### Welcome

```text
*********************************************
* Blender Studio Tools Deployment Assistant *
*********************************************
INFO - Updating Extensions
...
INFO - Launching Blender
Blender 4.5.1 LTS (hash b0a72b245dcf built 2025-07-29 06:24:35)
...
```

### Project Configuration

- The assistant reads your `project_config.json` (created by `setup_assistant.py`) to determine project settings, folder locations, and Kitsu connection details.

### Extensions and Blender Setup

- Downloads and installs the latest [extensions](https://projects.blender.org/studio/blender-studio-tools/releases).
- Places the Blender executable in the `local` folder.

### Kitsu Login

- Prompts for your Kitsu credentials, which are saved in the `userprefs.blend` file for automatic loading in Blender.

```text
**********************
* Artist Kitsu Login *
**********************
Email: admin@example.com
Password: 
Info: Logged in as Admin
Writing userprefs: "your_project_name/local/config/userpref.blend" ok
Info: Preferences saved
```

- All [Kitsu Preferences](extensions_setup.md) are set automatically based on your project configuration.

### Create a Desktop Shortcut

- On Linux, a desktop shortcut is created for easy access to Blender for this project.
- For Windows and Mac, see the [Project Blender](/artist-guide/project_tools/project-blender.md#create-shortcut) guide for manual setup.

```text
**************************************
* Shortcut to launch Project Blender *
**************************************
Shortcut Successfully created!
```

### Completion
You're all set! Artists can now launch Blender with the correct project settings and start working right away.

