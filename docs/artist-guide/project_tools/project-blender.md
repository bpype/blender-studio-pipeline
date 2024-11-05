# Project Blender

Project Tools will store a version of Blender within the `shared` directory. This version of Blender is internal to that project. This allows for multiple Blenders to be installed on your system, each with their own preferences tailored specifically to that project. The main advantage to running/managing Blender using the Project Tools scripts is that it will synchronize the Blender version and Shared Add-Ons across for all users contributing the the project. Project Tools also allows you to run a custom build of Blender with the Add-Ons and preferences set for your project.

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

This will download the latest blender to `data/your_project_name/local/blender`

::: info Choosing Branch to Install
You can specify a [daily build](https://builder.blender.org/download/daily/) branch to fetch by editing the `BLENDER_BRANCH` variable in the script file.
:::

### Manually deploying Blender versions of your choosing
You can download and put any Blender release into the `your_project_name/shared/artifacts/blender` folder with their corresponding shasum file.
NOTE: If you do this, it is strongly adviced to not run the `update_blender.py` script as it will overwrite your files.

There are a few things to keep in mind though:
1. It has to be the `.zip` release for Windows, `.tar.gz` for Linux, and `.dmg` for Mac.
2. Each file has to have a shasum file. You can generate this yourself easily on Linux with:

`shasum256 file.tar.gz > file.tar.gz.sha256`

3. The file names for the Blender archives has to have the following naming scheme:

Linux:
`blender-linux.x86_64.tar.xz`

Mac:
`blender-darwin.arm64.dmg` or `blender-darwin.x86_64.dmg`

Windows:
`blender-windows.arm64.zip` or `blender-windows.amd64.zip`

Note that the file names doesn't have to match exactly with the examples above as long as their corresponding shasum file is picked up by the following file globbing schema:

`"blender*" + operating_system + "." + architecture + "*.sha256"`

4. There can be no ambiguity on which archive the `run_blender.py` script should use. So for example you can not have `blender-windows.arm64.zip` and `blender2-windows.arm64.zip` in the `your_project_name/shared/artifacts/blender` folder at the same time.

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

![Image of Blender Icon in KDE Taskbar/Start Menu](/media/artist-guide/launch_blender.mp4)
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

## Update Blender Studio Add-Ons
All Add-Ons in the Blender Studio Pipeline repository can be quickly downloaded using the `update_addons.py` script.

```bash
# Linux/Mac
cd ~/data/your_project_name/svn/tools
./update_addons.py
```
```bash
# Windows
cd %HOMEPATH%\data\your_project_name\svn\tools
python update_addons.py
```

*To learn more see [Add-On Setup page](/td-guide/addon_setup.md)*


::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
