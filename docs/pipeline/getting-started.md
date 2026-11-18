# Getting Started

The Blender Studio Pipeline is a collection of open-source software centered around Blender. It brings together the tools a small team needs to produce an animated film. Follow the guides below to set up the complete Blender Studio Pipeline, or learn more about our tools and infrastructure and use them as building blocks for your own pipeline.

## Quick Start

Our design principles of an editorial-centric workflow, review and approval, and no caching are implemented in the Expo Project Manager:

- [**Expo Project Manager**](../addons/blender_kitsu.md)

It's a Blender extension for building and managing production files using a [Kitsu server](https://kitsu.cg-wire.com/) for task management. It supports our [project workflow](/pipeline/project-workflow/project-usage.md).


## Set Up Your Own Studio Pipeline

At Blender Studio, we want to share what we know about making animated films. This page provides an overview of our studio setup and the tools and infrastructure we use. Read the full [step-by-step guide](/studio-setup/introduction.md) to set up your own studio!

- **Workstations**: Choosing the right computer is important. [Review Blender's minimum and recommended specs](https://www.blender.org/download/requirements/) to choose the right hardware. Blender runs on many operating systems, so you can choose the one that works for you. We have a guide to compile [Gentoo Linux](/gentoo/td/overview.md), which is what we run at Blender Studio.

- **Launching Blender**: It's important to ensure everyone on the team is running the same version of Blender. You may choose to use an [LTS release from a package manager](https://www.blender.org/download/lts/) for automatic updates. We use [Project Tools](/tools/scripts/project-tools/overview.md) to distribute Blender to our workstations and launch it in an isolated "production environment", and control the exact version of Blender the production is using.

- **Project Manager**: We use [Expo Project Manager](/addons/expo_project_manager.md), a Blender extension for building and managing production files with a [Kitsu server](https://kitsu.cg-wire.com/) for task management. It supports our [project workflow](/pipeline/project-workflow/project-usage.md).

- **Version Control**: We use [Git](/studio-setup/git-setup.md) to store all of our project files in a version-controlled manner. This ensures that all revisions are snapshotted and makes it easy to restore any file you need.

- **File Sync**: Some files, such as renders, should not be stored in Git. We store these files in a folder called `shared`, as described in our folder conventions. For remote workstations, [Syncthing](/studio-setup/syncthing-setup.md) is a free and open-source file-sync solution.

- **Folders and Naming**: Choosing a folder structure is fundamental. The Expo Manager lets you customize your folder structure. We have detailed guides about how we designed our folder structure and naming conventions.

- **Python**: Sometimes you need to run scripts outside of Blender. Having the right [Python](/studio-setup/python.md) installed on all your machines is important.

- **Rendering**: We use [Flamenco](/studio-setup/flamenco_setup.md) as our render-farm solution. It runs on all our workstations, allowing them to form a distributed render farm within the studio. If you choose, you can also render locally using [Expo Project Manager](/addons/expo_project_manager.md).

