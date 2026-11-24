# Backups

Also known as "disk versions," this feature is intended for small productions or project development. For reliable backups of production files, set up a version control system such as [Git](/pipeline/operations/git-usage.md).

When `version_backups` is enabled in your [project settings](configuration.md#project-settings), Expo saves a backup `.blend1` file to a folder called `version_backups` when you:

- Create a [Publish](shot.md#publishing), such as with the `Publish Preview` operator
- Manually save a backup version using the `Save Backup Version` operator.

![Backups Panel](/media/addons/expo_manager/disk_version_backups.jpg)

### Save Backup Version
Save a backup without creating a playblast. This creates an incremental version; for example, if the latest is `v004`, the new version is `v004_001`.


### Open Backups Folder
Open the `version_backups` folder for the current Entity or Task in your system's file browser. You can browse and manage backup files there. Backups must be restored manually.

When using disk version backups, your entity's folder structure looks like this:

```
shots/
└── 010/
│ └── 010_0010/
│     ├── 010_0010-anim.blend  (main file)
│     └── version_backups/
│         ├── 010_0010-anim-v001.blend1
│         ├── 010_0010-anim-v002.blend1
│         ├── 010_0010-anim-v002_001.blend1
│         ├── 010_0010-anim-v003.blend1
│         └── ...
```
