# Project Tools

This is a collection of scripts to help creating and maintaining a movie production folder skeleton.

These are meant to help with getting smaller Blender productions up and running with the only requirement
of having a shared network folder available to all participants.
This shared folder can be read-only as it is used to ensure that all participants has the same Blender
version and add-ons.

The scripts themselves will be explained in the order one needs to execute them to setup everything correctly.
Let's get going! :)

**NOTE:** All scripts besides the `init_project_folder_structure.py` script, is only meant to be run from within the created folder skeleton!

## init_project_folder_structure.py

This script will initialize the folder structure skeleton.
To run it successfully, you need to specify the target folder.

Here is how you would create a folder skeleton in the temporary files folder on your Linux system:
```
./init_project_folder_structure.py /tmp/my_project
```

If you navigate to the `/tmp/my_project` folder you will see that there are three folders.
- `local` This is where the local copy of Blender and the add-ons will be installed.
- `shared` This is the folder that should be shared over the network. (By using Syncthing, NFS shares, Samba, Dropbox, etc)
- `svn` This the versioned controlled folder where the `.blend` production files will live.

Inside of the `svn` folder, there is a `tools` folder that contains all scripts listed here.
From this point on, all scripts are to be run from within the `tools` folder

## consistency_check.py

This script will check that the folder structure were created correctly.
Run it while in the created `tools` folder with `./consistency_check.py`.

## update_blender.py

This script will fetch the latest Blender download from https://builder.blender.org/download/
You can specify the branch to fetch by editing the `BLENDER_BRANCH` variable in the script file.

The Blender download for Linux, Mac, and Windows will be downloaded into the `shared/artifacts/blender` folder.
It will keep up to 10 previous downloaded versions for backup.

It is also possible to manually download Blender with their shasums and put then into this folder.
Note that only one version for each platform should exist at the same this in this folder if you do so.

## update_extensions.py

This is a script to fetch add-on .zip files and put them into `shared/artifacts/extensions` folder.

As with the `update_blender.py` script, it is possible to manually download the zip files and their shasums and put them in the `extensions` folder.

To specify which add-ons to download, edit the script file and use the `download_file` function.

## run_blender.py

This script will take the correct blender version for your operating system from `shared/artifacts/blender` and extract it to the `local` directory. Along with any add-ons in the `shared/artifacts/extensions` folder.

It will finally launch the extracted Blender.

Note that the script will only update the files in the `local` directory if the installed files differs from the ones hosted in the `shared` directory.

If they match, it will simply launch Blender.

## rollback_blender.py

If the `update_blender.py` script was used to download the Blender archive files, then you can use `rollback_blender.py` to switch the "current" version hosted in `shared/artifacts/blender` to one the older downloads.

This is intended to be used to rollback to an older version in case of bugs in newer downloaded versions.

## install_desktop_file.sh

This is a Linux only script file.

It installs a `.desktop` entry for the current user so they can easily launch `run_blender.py` from their application launcher.
