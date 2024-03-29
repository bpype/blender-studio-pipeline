# Troubleshooting
Troubleshooting for Gentoo Clients

::: info For TDs & Advanced Users
The following actions describe troubleshooting steps that should be performed by a Technical Director or IT Professional. Advanced Users are welcome to follow this guide if they are inclined, but they are not required to do so. Any issue related to System Memory (random crashes/freezes), Changes to the Linux Kernel or Restoring a Users Computer should be referred to the Technical Director or IT Department. 
:::


## Boot into the IPXE menu

#### If you can login to the computer
1. Launch a terminal window and become root
2. Use `cd`  to enter to the computers root directory
3. `./reboot_to_ipxe.sh` will automatically reboot the computer
#### Otherwise boot computer from LIVE USB
1. Check your computer’s manual to open boot menu 
2. Select the USB from the computers boot menu


_If successful, you will be greated with the following screen_
![IPXE Boot Menu](/media/td-guide/workstations/gentoo_boot_menu.png)

## Run MEM Test
1. [Boot into IPXE](/gentoo/td/troubleshooting.md#run-mem-test)
2. Select “Run MemTest”

## Chrooting into the root drive (for recovery)
1. [Boot into IPXE](/gentoo/td/troubleshooting.md#run-mem-test)
2. Select Gentoo Installer (Blender Institute Customized)
3. Wait for Gentoo Installer to boot ![Gentoo Installer](/media/td-guide/workstations/gentoo_installer_boot.png)
4. Use CTR+C to cancel Installer
![Cancel Installer](/media/td-guide/workstations/gentoo_ctrl_c.png)
5. Run  `./manual_chroot.sh` 
6. Select number corrisponding to the Drive labeled `rootfs`![Alt text](/media/td-guide/workstations/gentoo_rootfs.png)


## Recovery/Inspection of Linux Kernel 
1. [Follow steps in Chrooting into the root drive](/gentoo/td/troubleshooting.md#chrooting-into-the-root-drive-for-recovery)
2. Ensure the mount the boot drive is mounted **`mount /boot`**
3. Go into the kernel source dir **`cd /usr/src/linux`**
4. Use `make menuconfig` to enter linux kernel configuration
5. Now you can review/change the kernel configuration options! *For example you can inspect the NVME Drive configuration and compare it to the configuration found in the Gentoo documentation [https://wiki.gentoo.org/wiki/NVMe#Kernel](https://wiki.gentoo.org/wiki/NVMe#Kernel)*
![Alt text](/media/td-guide/workstations/gentoo_kernel_config_start.png)
6. On exit, if your kernel config is not saved you will be prompted to save![On Exit](/media/td-guide/workstations/gentoo_kernel_config_exit.png)
7. Configuration successfully saved ![Config Saved!](/media/td-guide/workstations/gentoo_kernal_config_saved.png)

8. Build New Kernel: `make -j8 && make modules_install && make install` ![Build New Kernel](/media/td-guide/workstations/gentoo_kernal_config_build_new.png)