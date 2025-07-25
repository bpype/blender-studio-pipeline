# Project Tools

This is a collection of scripts to help creating and maintaining a movie production folder skeleton.

These are meant to help with getting smaller Blender productions up and running with the only requirement
of having a shared network folder available to all participants.
This shared folder can be read-only as it is used to ensure that all participants has the same Blender
version and add-ons.

You can use the assistant scripts to get running quickly! Below the assistant scripts the core scripts themselves will be explained in the order one needs to execute them to setup everything correctly manually.

Let's get going! :)

# Assistant Scripts

## setup_assistant.py

`setup_assistant.py` is a friendly helper that sets up everything you need to start a new Blender Studio project. Think of it like a wizard that asks you questions and then builds all the folders and files you need, connects to your Kitsu server, and gets your project ready for you.

### What happens when you run the script?

1. **It asks for information**  
   The script will ask you for the address of your Kitsu server, your username, your password, and where you want your new project folder to be. You can also give these as command-line arguments if you want to skip the questions. If you make a mistake, it will ask again until you get it right.

2. **It checks your Kitsu login**  
   The script tries to connect to the Kitsu server with your details. If it can't log in, it will let you know and ask you to try again.

3. **It lets you pick your project**  
   Once you're logged in, it shows you a list of projects from Kitsu and lets you pick which one you want to set up.

4. **It creates your project folder**  
   The script makes a new folder for your project in the place you chose. If the folder can't be made (maybe it already exists or the path is wrong), it will ask you for a new place. Calls `init_folder_structure()` from `init_project_folder_structure.py` to create the standard folder skeleton for the project, including the main, `svn`, and `shared` directories, using predefined JSON templates.

5. **It builds all the folders you need**  
   Inside your new project folder, it creates all the special folders and files that Blender Studio needs to work together with your team.

6. **It asks which Blender version you want**  
   The script shows you a list of Blender versions and lets you pick which one you want to use for your project.

7. **It sets up Blender for you**  
   It updates the settings so that the right Blender version will be downloaded and used for your project.

8. **It downloads Blender and add-ons**  
   The script automatically downloads the Blender version you picked and any extra tools or add-ons you need.  Runs the `update_blender.py` and `update_extensions.py` scripts to download the correct Blender version and any required extensions into the project folders.

9. **It saves your project settings**  
   Finally, it writes down all the important settings (like your Kitsu info and folder paths) into a file so everything is ready for you when running `deployment_assistant.py`

10. **All done!**  
    When it's finished, your project is all set up and ready to go.

## Arguments

- `-u`, `--url`  
  The Kitsu server URL (e.g., `http://localhost/api`).  
- `-e`, `--user`  
  Your Kitsu username or email.  
- `-p`, `--password`  
  Your Kitsu password.  
- `-r`, `--root`  
  The folder where your new project will be created.  

You can give these as arguments, or just run the script and answer the questions.

## Example usage

```sh
./setup_assistant.py --url http://localhost/api --user admin@example.com --password mysecretpassword --root /mnt/projects
```

If you make a mistake, the script will help you fix it by asking again.

## deployment_assistant.py

`deployment_assistant.py` is the script you run after setting up your project with `setup_assistant.py`. Its job is to finish preparing your Blender Studio project for artists to use.

When you run this script, it does the following:

1. **Reads your project settings**  
   It looks for a file called `project_config.json` in the current folder. This file was created earlier by `setup_assistant.py` and contains all the important information about your project, like where your folders are and how to connect to Kitsu.

2. **Starts Blender and sets up preferences**  
   The script launches Blender in the background and runs another script called `set_blender_kitsu_prefs.py`.  
   This helper script:
   - Reads your `project_config.json` file.
   - Enables the Blender Kitsu add-on.
   - Sets up all the folder paths and preferences for your project inside Blender.
   - Prompts you to log in to Kitsu as an artist, so your Blender is ready to connect to the project.
   - Saves your Blender preferences and closes Blender.

3. **Creates a desktop shortcut (Linux only)**  
   If you're on Linux, the script will also create a desktop shortcut so you can easily launch Blender for this project from your application menu.

When it's done, your Blender is fully configured for the project, and you can start working right away!

--------------------------------------------------------------------------------------

# Core Scripts

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
