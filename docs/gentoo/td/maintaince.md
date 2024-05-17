# Workstation System Maintenance

## How to Update Build Server & Clients
To update Client Workstations; the Build Server will pull all of the latest changes from the [main gentoo repository](https://wiki.gentoo.org/wiki/Ebuild_repository#:~:text=The%20Gentoo%20ebuild%20repository%20is%20the%20main%20ebuild%20repository%20for,to%20be%20available%20to%20Portage.) and compile a system update. When done, it will ask if you want to push out the compiled changes to the clients. The clients ask for updates to be pushed from the build server every five minutes. If the build server signals that there are updates, the clients will perform a sync, downloading the compiled packages from the build server and installing all updated packages.

1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. `cd` to change directory to the root home folder
4. Run `./update_build_server.sh`

## Update custom package recipes on Build Server
Some applications on Blender Studio workstations are not included in the main Gentoo repository
and are instead sourced from an external repository. To learn more about how external repositories
are used in Gentoo see the [Gentoo Handbook](https://wiki.gentoo.org/wiki/Ebuild_repository#Repository_synchronization). This is known as an overlay repository 
[Blender Studio Overlay Repo](https://projects.blender.org/ZedDB/blender-studio-overlay). To update the recipe for an existing package in an overlay repo follow the steps below. 
1. Commit changes to the package recipes on the [Blender Studio Overlay Repo](https://projects.blender.org/ZedDB/blender-studio-overlay)
2. `ssh user@build-server-addr` connect to your build server via ssh
3. Update the package recipes on the Build Server  `emaint sync --repo blender-studio-overlay`

Once an update of the recipe is complete any affected packages can be installed our updated by following the [Installing Packages on Build Server](/gentoo/td/maintaince#installing-packages-on-build-server) guide.

## Installing Packages on Build Server
Packages need to be compiled on the Build Server and marked with a date to be able to discovered by the workstations. Follow the below steps to install/update a package on the build server.
1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. Run `emerge --oneshot {package-name}` to update a live package.
    - Run `emerge --oneshot blender-studio-tools` to update the studio Add-ons
4. Run `date -R > /var/cache/update_info/timestamp.chk` to mark this update as the latest

::: info Info
The command `emerge --oneshot {package-name}` compiles package, but does not add the packages to the [@world](https://wiki.gentoo.org/wiki/World_set_(Portage)), this means these packages will be removed when running `--depclean`.. We add this because these packages are already pulled in by another set. So we don’t want to add it again to the @world set. To learn more visit the [Gentoo  Handbook](https://wiki.gentoo.org/wiki/Emerge#:~:text=fetchonly%20%2D%2Demptytree%20%40world-,Do%20not%20add%20dependencies%20to%20the%20world%20file,-If%20a%20dependency) 
::: 
## Update Local Add-Ons

Add-Ons are locally stored in the following directories; `/usr/share/flamenco` and `/usr/share/blender_studio_tools`. These are updated by running the following commands. These directories are automatically updated daily by the Gentoo package manager.

Note that the Flamenco package installs and updates the addon, manager, and worker per default.

```bash
emerge -1 blender-studio-tools
emerge -1 flamenco
```




### How to update to specific version?
In some cases, users may want to specify what version of an add-on to deploy. Users can accomplish this using `eclass` variables found in the [Gentoo Devmanual](https://devmanual.gentoo.org/eclass-reference/git-r3.eclass/index.html#:~:text=more%20creative%20ways.-,EGIT_BRANCH,-The%20branch%20name).
- Run `EGIT_COMMIT=<hash> emerge {package-name}` to update to a specific commit 
- Run `EGIT_BRANCH=<branch> emerge {package-name}` to update to a specific branch 
- Run `EGIT_COMMIT=<hash> EGIT_BRANCH=<branch> emerge {package-name}` to update to a specific commit with in a specific branch 
## Wake on LAN
Wake on LAN is used turn on computers from a "low power" or sleeping state so they can be updated. Wake on LAN uses the hardware information provided by the clients to immediately wake up all that are currently offline. The following guide covers how to parse the hardware info sent by client computers and to use that information to wake any sleeping computers via Wake on LAN.

::: info Will Computers Turn Off after updating?
If this is used in combination with a system update, the client computers will turn off after the system update has completed. (Unless any users are logged into the system when the update finishes).
:::

1. `ssh user@build-server-addr` connect to your build server via ssh
2. Use `su` to Login as root or login as root directly
3. `cd` to change directory to the root home folder
4. `mkdir comps` To create a folder to store parsed client hardware info if none exists
5. `parse_output.py /var/studio_scripts/hw_data/* comps/` to parse client hardware info 
6. Run  `./wol_shared_comps.py comps/*` to wake any computers that are asleep
