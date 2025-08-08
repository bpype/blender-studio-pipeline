# Setup Assistant

The `setup_assistant.py` script is a wizard that helps you set up a new Blender Studio Tools project. It guides you through connecting to your Kitsu server, creating project folders, and configuring everything you need. You can download it as part of the [project-tools release package](https://projects.blender.org/studio/blender-studio-tools/releases/download/project-tools/project-tools-main.zip).

## 🛠️ What Does the Script Do?

- **Creates all required folders**  
  Sets up the standard Blender Studio project structure.

- **Configures Blender**  
  Ensures the correct Blender version is used for your project.

- **Downloads Blender & Add-ons**  
  Runs `update_blender.py` and `update_extensions.py` to fetch the right versions.

- **Saves your settings**  
  Stores all configuration for use with `deployment_assistant.py`.
  

## 🚀 Quick Start

1. **Download & Unzip**  
  Get the release package and unzip it.

2. **Run the Script**  
  - **Linux/Mac:**  
    ```bash
    ./setup_assistant.py
    ```
  - **Windows:**  
    ```bash
    python setup_assistant.py
    ```

---

## 🖥️ Interactive Setup Walkthrough

### Welcome

```text
****************************************
****************************************
* Blender Studio Tools Setup Assistant *
****************************************
****************************************
Welcome to the Blender Studio Tools Setup Assistant!
This script will help you set up your Blender-Studio-Tools project.
Please follow the prompts to set up your project and set your Blender branch.
```

### Kitsu Setup

- Enter your Kitsu server URL, username, and password.  
  Kitsu is the source of truth for your projects—make sure your project exists there.

```text
********************
*   Kitsu Setup    *
********************
Input Kitsu Server URL: localhost
Kitsu Server URL set to: https://localhost/api
Login to Kitsu Account
Email: admin@example.com
Password: 
```

### Project Selection

- Choose your project from the list.

```text
************************
* Select Kitsu Project *
************************
(0): Singularity
(1): Wing It!
(2): Charge
Select a project by number: 1
Selected Project: Wing It!
```

### Shortname

- If needed, set a shortname (lowercase, no spaces).

```text
***********************
* Set Kitsu Shortname *
***********************
Kitsu project shortname 'wing_it' is valid.
```

### Project Folder

- Choose where to create your project directory. The script builds the standard folder structure using `init_folder_structure()`.

```text
************************
* Setup Project Folder *
************************
Enter the path where the project directory will be created. 
This directory will be named after the Kitsu project.

Enter the project path:  ~/data/
Project path created at: ~/data/your_project_name
```

### Version Control

- Indicate if you use SVN or GIT-LFS. If not, disk-based versioning is enabled.  
  See [Version Management Modes](folder_structure_overview.md#version-management-modes) for details.

```text
*************************
* Version Control Setup *
*************************
The Blender Studio Tools project is designed to work with version control software (SVN/GIT-LFS) to manage versioning of project files such as Assets & Shots.
If you are not using version control, the Blender Kitsu add-on will create version files on your disk to provide versioning functionality.
Are you using a version control software (SVN/GIT-LFS)? (y/n): y
```

### Blender Branch

- Pick the Blender version for your project.

```text
*************************
* Select Blender Branch *
*************************
Select the Blender branch you want to use for this project.
Only 4.5+ versions are supported.
(0): 5.0.x main (latest)
(1): 4.5.x v45
Select Blender Branch from List: 1
Selected Blender Branch: 4.5.x v45
```

---

## 📂 Mounting Project Folders

After setup, make sure the `svn` and `shared` directories are available on artist workstations. Then, run [deployment assistant](deployment_assistant.md) on each workstation.

::: info Setting Up SVN & Syncthing
- If using [SVN](https://studio.blender.org/tools/td-guide/svn-setup) or GIT LFS, make your initial commit of `your_project_name/svn` now.
- If using [Syncthing](https://studio.blender.org/tools/td-guide/syncthing-setup) or a NAS, set up your shared folder `your_project_name/shared` now.
:::

---

## ⚙️ Usage with CLI Arguments

You can also provide setup options as command-line arguments:

| Argument         | Description                                   |
|------------------|-----------------------------------------------|
| `-u`, `--url`    | Kitsu server URL (e.g., `http://localhost/api`) |
| `-e`, `--user`   | Kitsu username or email                       |
| `-p`, `--password` | Kitsu password                              |
| `-r`, `--root`   | Folder where your new project will be created |

Example:

```bash
./setup_assistant.py --url http://localhost/api --user admin@example.com --password mysecretpassword --root /mnt/projects
```

If you make a mistake in your arguments, the script will prompt you to correct them during execution.

