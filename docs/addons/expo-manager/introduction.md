# Expo Manager

A lightweight, Blender-focused production management tool for individuals and small teams.

::: warning  Beta
This add-on is a **Beta** release. It is the replacement for [Blender-Kitsu](/addons/blender_kitsu.md) Add-On. The last stable version of the Blender-Kitsu add-on is available in the [Blender Studio Tools Blender 5.2 release bundle](https://projects.blender.org/studio/blender-studio-tools/releases/tag/blender-5.2).
:::

Download the [latest release](https://projects.blender.org/studio/expo-manager/releases) from the [Expo Manager repository](https://projects.blender.org/studio/expo-manager).


## Features
- Custom folder paths and automatic file path management.
- Edit your production directly in Blender: manage all your Shots in one place and push timing changes to the production.
- Automatically load Assets into Shots using Kitsu's breakdown feature.

## Quick Start
1. Follow the [official setup](https://kitsu.cg-wire.com/installation/) instructions to set up a Kitsu server and project.
2. Create a project folder and make it available to all artists using your team's [file-sharing solution](/pipeline/workflow.md).
3. Create `my_project/.blender_project/expo_config.toml` using a sample from the Expo Manager source checkout, and adjust it for your project using the [Configuration reference](configuration.md).
4. [Install](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#install) and enable the Expo Manager Add-on on each artist's computer.
5. In the Add-on preferences, set your project path, enter your Kitsu credentials, and start the project session.
6. Use the `Expo` menu at the top of Blender to create and open Shots, Assets, Sequences, and Edits.

See the [Project Workflow](/pipeline/workflow.md) for a step-by-step guide.

**Folder structure for the configuration**

```
my_project/
├── .blender_project/
|   ├── templates # Template files to use in "New File" generation
│   └── expo_config.toml   # Your project settings copy
└── ... # Production files/renders will be populated on demand based on your config
```


## Core concepts
### Entities
* **Sequence files** map to a Sequence and Task Type on the Kitsu server (e.g. `010-Storyboard.blend`).
* **Shot files** map to a parent Sequence, Shot, and Task Type on the Kitsu server (e.g. `010/010_0010-Animation.blend`).
* **Asset files** are named after the Asset on Kitsu and organized by Asset Type (e.g. `Characters/Rain.blend`).
* **Edit files** map to an Edit entity on Kitsu and, for TV shows, an Episode.
### Other File Types
* **Publish files** are movies or images generated from the work files above. The production files themselves are not versioned by the publish workflow.
* **Version backups** are copies of an entity's work file associated with a Publish version. Disable this if the project uses a version control system such as Perforce or Git LFS.



## Project Structure
```bash
my_project/
├── .blender_project/
│   ├── expo_config.toml # Your project's configuration
│   └── templates/ # Templates for new files
├── sequences/ # example of custom project folder layout
│   └── 010/
│       ├── 010-previs.blend
│       └── shots/
│           └── 010_0010/
│               ├── 010_0010-animation.blend
│               └── 010_0010-comp.blend
├── edit/
│   └── my-edit.blend
└── assets/
    └── Characters/
        └── Rain.blend
```

The directories shown here are illustrative; their locations are controlled by the [project configuration](configuration.md). This layout follows the Blender Studio [File & Naming conventions](/pipeline/file-and-naming-conventions/intro).

## Setting Add-on Preferences
The project configuration supplies `kitsu_server` and `kitsu_project_id`; see [Project Settings](configuration.md#project-settings).

1. Navigate to `Preferences > Add-ons > Expo Manager`.
2. Set the `Project Root Directory` value to your project's root.
3. Enter the email address and password for your Kitsu account (defined under People on the Kitsu server).
4. Select `Start Session` to load the project configuration and connect to Kitsu. If the session cannot start, check the preferences and system console for errors.

## Troubleshooting

Operators report errors and warnings in Blender's interface. For more detail, check the Info panel and system console, especially when configuration, media imports, or asset linking fail.
