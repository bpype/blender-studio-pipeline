# Flamenco
Flamenco is a cross-platform framework to manage a render farm. Blender Studio uses Flamenco for rendering jobs across with a several machines including artist's workstations.

## Flamenco Quickstart Guide
Follow the [Flamenco Quickstart](https://flamenco.blender.org/usage/quickstart/) guide to setup your Flamenco farm. The rest of this page acts as a companion to the Flamenco Quickstart guide, providing additional info relevant for Blender Studio Pipeline users. 

### Shared Storage 
On **Step 2**, you must determine a shared storage path. This path must be accessible by all **workers** in the farm. This path should be outside of your project's directory and must be an absolute path (the same on each machine). 

To learn more about how files are stored on the farm, see the [Shaman Storage System](https://flamenco.blender.org/usage/shared-storage/shaman/) documentation.

### Blender Path
On **Step 3**, your Blender Path MUST be the same on all **workers**. 

::: warning  Warning!
If you followed the [TD Setup Guide](blender_setup) exactly and your project/blender executable is relative to the home folder, you must follow the below instruction.
:::
If you are storing your Blender executable at a path that is different on each computer (e.g. relative to each user's home folder), consider either creating a symlink or storing a copy of Blender in a directory that is the same on each workstation.  

### Distributing Flamenco Add-On
On **Step 6** you will be provided with the Flamenco Add-On. You will need to distribute this Add-On to all machines in each project using the farm.

- Place a copy of the Add-On zip in the `your_project_name/shared/artifacts/addons/` directory. 

::: info  Versioning
You will need to repeat this step for each project using this farm. Only update this add-on when [updating the farm's version](https://flamenco.blender.org/usage/upgrading/). **The Flamenco Add-On is farm-version-dependent, rather than per-project.**
:::

*Advanced users can modify the [`update_addons.py`](https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools/update_addons.py) script which automates the above process. [See Update Add-Ons](addon_setup#modify-update-add-ons-script) guide* 

::: info Gentoo Users
Flamenco is installed and updated by the package manager of your Gentoo workstation. To learn more see [Update Local Add-Ons](/gentoo/td/maintaince#update-local-add-ons) in the Gentoo section.
:::
### Flamenco Workers
After **Step 8**, ensure `flamenco-worker` has been run on each machine you will like to include in your Flamenco farm. These **worker** machines will render jobs once you have submitted a job from Blender to the Flamenco server in **Step 9**.
<!--
This is included because running Flamenco Worker is not mentioned in the quickstart guide, at the time of writing. 
-->