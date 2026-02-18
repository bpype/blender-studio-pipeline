# Setup Blender Extensions

::: info Update Extensions
To learn how to update the core Blender Studio Extensions, see the [Update Blender Studio Extensions](blender_setup#update-blender-studio-extensions) guide.
:::

## Modify Update Extensions Script

*Users can modify the [`update_extensions.py`](https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools/update_extensions.py) script to include external extensions not managed by Blender Studio.*

**Example**
```bash
# Append the following lines to the end of the `update_extensions.py` script.
download_file(
   "https://projects.blender.org/Mets/CloudRig/archive/master.zip",
   download_folder_path,
   "CloudRig.zip",
)
```

## Automatically Installing Extensions
A helper script is provided to easily generate a `sha256sum` for a given add-on and place it in the correct directory.

```bash
cd  ~/data/your_project_name/svn/tools
python deploy_custom_addon.py 
```

You will be prompted to provide the path to the custom add-on you want to deploy. Once your file is verified to exist and is a .zip file, it will be copied to the `shared/artifacts/extensions` folder for distribution. 

## Manually Installing Extensions
To manually install extensions without using any scripts, simply drop the .zip file and the sha256 file of the extension into the project's `shared/artifacts/extensions` folder.
If the zip doesn't already have a sha256 file, you can generate it yourself with the `sha256sum` program.
For example, on Linux you can generate it like this:
```bash
sha256sum my_test_extension.zip > my_test_extension.zip.sha256
```

## Removing Extensions
To remove extensions you are no longer using, remove both the extension's zip file and sha256 file from the project's `shared/artifacts/extensions` folder.
The next time you run the `run_blender.py` script, it will remove the extension locally.

## Package Blender Studio Extensions from Source
Blender extensions can be packaged directly from the [Blender Studio Pipeline](https://projects.blender.org/studio/blender-studio-tools) repository. Personal add-ons/extensions can be installed [normally](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#installing-add-ons).

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
./pipeline_release.py --local # Linux/Mac
```
```bash
python pipeline_release.py --local # Windows
```

4. Copy Output to Artifacts
Copy the output to `~/data/your_project_name/shared/artifacts/extensions/` to distrubte the add-ons to your project.


::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
