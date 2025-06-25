# Setup Blender Extensions

::: info Update Extensions
To learn how to update the core Blender Studio Extensions see [Update Blender Studio Extensions](blender_setup#update-blender-studio-extensions) guide.
:::

## Modify Update Extensions Script

*Users can modify the [`update_extensions.py`](https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools/update_extensions.py) script to include external extensions not managed by the Blender Studio.* 

**Example**
```bash
# Append the follow lines to the end of the `update_extensions.py` script.
download_file(
   "https://projects.blender.org/Mets/CloudRig/archive/master.zip",
   download_folder_path,
   "CloudRig.zip",
)
```

## Manually installing Extensions
To manually install Extensions without using any scripts, simply drop the .zip file and the shasum256 file of the extension into the projects `shared/artifacts/extensions` folder.
If the zip doesn't already have a shasum file, you can generate it yourself with the `shasum256` program.
For example, on Linux you can generate it like this:
```bash
shasum256 my_test_extension.zip > my_test_extension.zip.sha256
```

## Removing Extensions
To remove Extensions you are not using anymore, you remove both the Extensions zip file and shasum file from the projects `shared/artifacts/extensions` folder.
Next time you run the `run_blender.py` script, it will remove the extension locally.

## Package Blender Studio Extensions from Source
Blender Extensions can be packaged directly from the [Blender Studio Pipeline](https://projects.blender.org/studio/blender-studio-tools) repository. Personal Add-Ons/Extensions can be installed [normally](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#installing-add-ons).

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
./package_local.py ~/data/your_project_name/shared/artifacts/extensions # Linux/Mac
```
```bash
python package_local.py %HOMEPATH%\data\your_project_name\shared\artifacts\extensions # Windows
```


::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
