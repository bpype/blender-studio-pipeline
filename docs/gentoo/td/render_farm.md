# Render Farm

This page contains instructions on how to update the [Flamenco](https://flamenco.blender.org/) render farm deployed at the Blender Studio. Most if not all studio computers will run Gentoo. The "Non Gentoo" computer section is for computers not managed directly by the studio.

::: info Note
This assumes that you are on the same local network as the other computers on the render farm.
:::

## Non Gentoo workstation computers

To update Flamenco, you will need to run the `deploy.sh` on the Flamenco Manager.
This will update the manager, worker, and add-on on the non Gentoo computers. 
After the `deploy.sh` has finished, you need to restart the workers from the manager webUI.

::: warning Extra credentials needed
Note to complete the following steps you need the correct SSH key to access the Flamenco Manager. 
Contact your Flamenco administrator to retrieve the SSH key.
:::

### Workers


1. Run the `deploy.sh` script from the Flamenco [git repo](https://projects.blender.org/studio/flamenco) on the Flamenco Manager
2. Go to the manager [webui](http://flamenco.farm.blender/app/workers)
3. Select the workers you want to restart.
4. Choose one of the "Restart" options in the menu, and press Apply.
5. The workers are configured to automatically start again after they've been shut down from the web interface.

<details><summary>If that doesn't work, click here for an alternative method</summary>

::: info How to restart the worker without the manager 
1. ssh into the computer that is having issues restarting the worker
2. Run the following command: `sudo systemctl restart flamenco-worker`
3. Keep an eye on the Flamenco Manager web interface. It should show the worker is offline, and then it should become available again.
:::
</details>

### Add-on

The Blender add-on also needs to be reloaded, make sure that Blender is restarted on the affected computers.

## Gentoo workstations

This section will only provide a quick rundown of how to update the Flamenco package that is part of the Render Farm setup.

For more details and how to update other packages, see the [Maintenance](/gentoo/td/maintaince) page.

::: info Note
The Flamenco package should already have the correct [USE flags](https://wiki.gentoo.org/wiki/Handbook:AMD64/Working/USE) configured.
However if you want to inspect what USE flags the current install has, you can use `eix flamenco`.
This should tell you if the manager, worker, and/or add-on is included in the package deployment.
:::

### How to update the Flamenco package

To update the workers on the workstations, you need to:

1. SSH to the build server `ssh user@build-server-addr`
2. Use `su` to login as root directly
3. Run `emerge --oneshot flamenco` to update the [Flamenco](https://flamenco.blender.org/) worker/add-on
4. Run `~/signal_updates.sh` to signal to all workstations that there are updates available

### Workers

You need to manually restart the workers from the webui after the Flamenco package has been updated

1. Go to the manager [webui](http://flamenco.farm.blender/app/workers)
2. Select the workers you want to restart.
3. Choose one of the "Restart" options in the menu, and press Apply.
4. The workers are configured to automatically start again after they've been shut down from the web interface.

<details><summary>If that doesn't work, click here for an alternative method</summary>

::: info How to restart the worker without the manager 
1. ssh into the computer that is having issues restarting the worker and become root
2. Run the following command: `rc-service flamenco-worker -s restart`
3. Keep an eye on the Flamenco Manager web interface. It should show the worker is offline, and then it should become available again.
:::
</details>

### Manager

If any of the Gentoo computers is running the manager, it can be restarted on that computer with:

`rc-service flamenco-manager -s restart`

Note that the manager is not deployed by default. It is only deployed if `manager` [USE flag](https://wiki.gentoo.org/wiki/Handbook:AMD64/Working/USE) has been turned on.

### Add-on

The Blender add-on also needs to be reloaded, make sure that Blender is restarted on the affected computers.
