# Setup Blender Add-Ons

::: info Update Add-Ons
To learn how to update the core Blender Studio Add-Ons see [Update Blender Studio Add-Ons](blender_setup#update-blender-studio-add-ons) guide.
:::

## Modify Update Add-Ons Script

*Users can modify the [`update_addons.py`](https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools/update_addons.py) script to include external add-ons not managed by the Blender Studio.* 

**Example**
```bash
# Append the follow lines to the end of the `update_addons.py` script.
download_file(
   "https://gitlab.com/blender/CloudRig/-/archive/individual_addon/CloudRig-individual_addon.zip",
   download_folder_path,
   "CloudRig.zip",
)
```

## Manually installing Add-Ons
To manually install Add-Ons without using any scripts, simply drop the .zip file and the shasum256 file of the addon into the projects `shared/artifacts/addons` folder.
If the zip doesn't already have a shasum file, you can generate it yourself with the `shasum256` program.
For example, on Linux you can generate it like this:
```bash
shasum256 my_test_addon.zip > my_test_addon.zip.sha256
```

## Removing Add-Ons
To remove Add-Ons you are not using anymore, you remove both the Add-On zip file and shasum file from the projects `shared/artifacts/addons` folder.
Next time you run the `run_blender.py` script, it will remove the addon locally.

## Package Blender Studio Add-Ons from Source
Blender Add-ons can be packaged directly from the [Blender Studio Pipeline](https://projects.blender.org/studio/blender-studio-tools) repository. Personal Add-Ons can be installed [normally](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#installing-add-ons).

1. Enter Directory

```bash
cd ~/data/blender-studio-tools/scripts/pipeline-release # Linux/Mac
```
```bash
cd %HOMEPATH%\data\blender-studio-tools\scripts\pipeline-release # Windows
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


::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::