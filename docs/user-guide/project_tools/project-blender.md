# Project Blender

Project Tools will store a version of Blender within the `shared` directory. This version of Blender is internal to that project. This allows for multiple Blenders to be installed on your system, each with their own preferences tailored specifically to that project. The main advantage to running/managing Blender using the Project Tools scripts is that it will synchronize the Blender version and Shared Add-Ons across for all users contributing the the project. Project Tools also allows you to run a custom build of Blender with the Add-Ons and preferences set for your project. 

<!---
TODO Note from Julien:
An important info atm is that the `datafiles` folder is NOT being used from the Project Blender. This folder is directly referenced from the primary Blender preferences (on Linux at `/home/<user>/.config/blender/<version>/datafiles/`)
So if there are any World HDRIs and Matcaps that you'd like to use, these will be availible on both Blender versions.
--->

## Blender Setup
The next step is to deploy the required software onto each of the studio's workstations.

1. Download the latest Blender
```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./update_blender.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python update_blender.py
```

This will download the latest blender to `data/your_project_name/local/blender`

::: info Choosing Branch to Install
You can specify a [daily build](https://builder.blender.org/download/daily/) branch to fetch by editing the `BLENDER_BRANCH` variable in the script file.
:::
## Create Shortcut

Once your project has been setup using the "Project Tools" scripts Blender should be available inside your application's native application launcher. The run Blender script will take the correct blender version for your operating system from `your_project_name/shared/artifacts/blender` and extract it to the local directory. Along with any add-ons in the `your_project_name/shared/artifacts/addons` folder. Your Blender preferences are stored on a per project basis in `{directory-path}`

### Create Linux Shortcut
```bash
cd ~/data/your_project_name/svn/tools
./install_desktop_file.sh
```
::: info Available on Gentoo
To learn more about running the Blender if you are on a Gentoo system please see the [Gentoo guide](/gentoo/user/running-blender.md), including how to run a [debug build](/gentoo/user/running-blender.md#debug-build). 
:::

#### Launch with Custom Build on Linux
You must run the Create Linux Shortcut step before running a custom build. This will launch blender using your custom binary, but with the Add-Ons and preferences of your project.

1. Navigate to your custom Blender binary
2. Right Click the binary
3. Select `Open with > Blender your_project_name`



<!---
TODO Replace Image with Project-Tools version

![Image of Blender Icon in KDE Taskbar/Start Menu](/media/user-guide/launch_blender.mp4)
--->

### Create Windows Shortcut

1. Open the directory `%HOMEPATH%\data\your_project_name\svn\tools` 
2. Create a shortcut to `launch_blender_win.bat` on your desktop

### Create Mac Shortcut

1. Open the directory `~/data/your_project_name/svn/tools` 
2. In finder, select the `launch_blender_mac.command` and press `ctrl+shift+command+t` to add it to the dock.


## Launch via Terminal 

To launch Blender from the terminal, open the tools directory within your project folder, and from the terminal use the run Blender script.

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./run_blender.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python run_blender.py
```

::: warning Command Line Arguments
Note: Command Line Arguments also known as Flags are not supported by the `run_blender.py` script. 
:::

## Update Blender

This script will fetch the latest Blender download from https://builder.blender.org/download/  The Blender download for Linux, Mac, and Windows will be downloaded into the `your_project_name/shared/artifacts/blender` folder. It will keep up to 10 previous downloaded versions for backup. This Blender doesn't update automatically, at least one user in the project must manually initiate an update, all users will receive this update because blender is stored within the `shared` directory. 

::: info  Blender Studio Users
Internally to the Blender Studio only, the blender inside your project is automatically updated overnight, not manual update is required. 
:::

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./update_blender.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python update_blender.py
```
## Rollback Blender

Use `rollback_blender.py` to switch the "current" version hosted in `your_project_name/shared/artifacts/blender` to one the older downloads, rolling back affects all users using your project. This is intended to be used to rollback to an older version in case of bugs in newer downloaded versions.

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./rollback_blender.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python rollback_blender.py
```


### Run a previous version of Blender Locally

In some cases users may want to run a previous version of Blender on their machine without affecting other users. 

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./run_blender_previous.py
```
```bash
# Windows
cd %HOMEPATH%\your_project_name\svn\tools
python rollback_blender_local.py
```

## Install/Update Add-Ons
Blender Add-ons can be packaged directly from the [Blender Studio Pipeline](https://projects.blender.org/studio/blender-studio-pipeline) repository. Personal Add-Ons can be installed [normally](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#installing-add-ons).

1. Enter Directory

```bash
cd ~/data/blender-studio-pipeline/scripts/pipeline-release # Linux/Mac
```
```bash
cd %HOMEPATH%\data\blender-studio-pipeline\scripts\pipeline-release # Windows
```

2. Update Git 
```bash
# Windows & Linux/Mac
git checkout main # Checkout main branch
git reset --hard # Remove any changes stored in your branch
git pull --rebase origin # Pull to update to latest commit
```

3. Run Package Local Script
```bash
./package_local.py ~/data/your_project_name/shared/artifacts/addons # Linux/Mac
```
```bash
python package_local.py %HOMEPATH%\data\your_project_name\shared\artifacts\addons # Windows
```


::: info Blender Studio Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
