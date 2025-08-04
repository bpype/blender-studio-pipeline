# Project Blender

Project Tools will store a version of Blender within the `shared` directory. This version of Blender is internal to that project. This allows for multiple Blender installations on your system, each with their own preferences tailored specifically to that project. The main advantage of running/managing Blender using the Project Tools scripts is that it will synchronize the Blender version and Shared Extensions across all users contributing to the project. Project Tools also allows you to run a custom build of Blender with the Extensions and preferences set for your project.

<!---
TODO Note from Julien:
An important info atm is that the `datafiles` folder is NOT being used from the Project Blender. This folder is directly referenced from the primary Blender preferences (on Linux at `/home/<user>/.config/blender/<version>/datafiles/`)
So if there are any World HDRIs and Matcaps that you'd like to use, these will be availible on both Blender versions.
--->

## Blender Setup
The next step is to deploy the required software onto each of the studio's workstations.

### Using our scripts to download the latest Blender LTS or daily build version
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

This will download the latest Blender to `data/your_project_name/local/blender`.

::: info Choosing Branch to Install
You can specify a [daily build](https://builder.blender.org/download/daily/) branch to fetch by editing the `BLENDER_BRANCH` variable in the script file.
:::

### Manually deploying Blender versions of your choosing
You can download and put any Blender release into the `your_project_name/shared/artifacts/blender` folder with its corresponding shasum file.
**Note:** If you do this, it is strongly advised not to run the `update_blender.py` script as it will overwrite your files.

There are a few things to keep in mind:
1. It has to be the `.zip` release for Windows, `.tar.gz` for Linux, and `.dmg` for Mac.
2. Each file must have a shasum file. You can generate this yourself easily on Linux with:

`sha256sum file.tar.gz > file.tar.gz.sha256`

3. The file names for the Blender archives must follow the naming scheme:

Linux:
`blender-linux.x86_64.tar.xz`

Mac:
`blender-darwin.arm64.dmg` or `blender-darwin.x86_64.dmg`

Windows:
`blender-windows.arm64.zip` or `blender-windows.amd64.zip`

Note that the file names do not have to match exactly with the examples above as long as their corresponding shasum file is picked up by the following file globbing schema:

`"blender*" + operating_system + "." + architecture + "*.sha256"`

4. There can be no ambiguity about which archive the `run_blender.py` script should use. For example, you cannot have both `blender-windows.arm64.zip` and `blender2-windows.arm64.zip` in the `your_project_name/shared/artifacts/blender` folder at the same time.

## Create Shortcut

Once your project has been set up using the "Project Tools" scripts, the `run_blender.py` script should be available inside `your_project_name/svn/tools`. Follow the steps below to create a shortcut to this script. This shortcut will call the `run_blender.py` script, which will fetch the correct Blender version for your operating system from the `your_project_name/shared/artifacts/blender` directory and extract it to the `local` directory. It will also fetch extensions in the `your_project_name/shared/artifacts/extensions` folder.

### Create Linux Shortcut
```bash
cd ~/data/your_project_name/svn/tools
./install_desktop_file.sh
```
::: info Available on Gentoo
To learn more about running Blender if you are on a Gentoo system, please see the [Gentoo guide](/gentoo/user/running-blender.md), including how to run a [debug build](/gentoo/user/running-blender.md#debug-build).
:::

#### Launch with Custom Build on Linux
You must run the Create Linux Shortcut step before running a custom build. This will launch Blender using your custom binary, but with the Extensions and preferences of your project.

1. Navigate to your custom Blender binary
2. Right-click the binary
3. Select `Open with > Blender your_project_name`

<!---
TODO Replace Image with Project-Tools version

![Image of Blender Icon in KDE Taskbar/Start Menu](/media/artist-guide/launch_blender.mp4)
--->

### Create Windows Shortcut

1. Open the directory `%HOMEPATH%\data\your_project_name\svn\tools`
2. Create a shortcut to `launch_blender_win.bat` on your desktop

### Create Mac Shortcut

1. Open the directory `~/data/your_project_name/svn/tools`
2. In Finder, select the `launch_blender_mac.command` and press `ctrl+shift+command+t` to add it to the dock.

## Run Blender 

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
Note: Command line arguments, also known as flags, are not supported by the `run_blender.py` script.
:::

## Update Blender

This script will fetch the latest Blender download from https://builder.blender.org/download/. The Blender download for Linux, Mac, and Windows will be downloaded into the `your_project_name/shared/artifacts/blender` folder. It will keep up to 10 previously downloaded versions for backup. This Blender does not update automatically; at least one user in the project must manually initiate an update. All users will receive this update because Blender is stored within the `shared` directory.

::: info Blender Studio Users
Internally to the Blender Studio only, the Blender inside your project is automatically updated overnight; no manual update is required.
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

Use `rollback_blender.py` to switch the "current" version hosted in `your_project_name/shared/artifacts/blender` to one of the older downloads. Rolling back affects all users using your project. This is intended to be used to rollback to an older version in case of bugs in newer downloaded versions.

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

### Run a Previous Version of Blender Locally

In some cases, users may want to run a previous version of Blender on their machine without affecting other users.

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

## Update Blender Studio Extensions
All extensions in the Blender Studio Pipeline repository can be quickly downloaded using the `update_extensions.py` script.

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./update_extensions.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python update_extensions.py
```

*To learn more, see the [Extensions Setup page](/td-guide/extensions_setup.md).*

::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more, see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
