# Git Setup
The Blender Studio Pipeline relies on Git to version-control all `.blend` files used in production. This guide explains how to set up a repository and install Git and Git LFS on your workstation.

Your Git repository will be the central source of truth for your project. You can host it remotely using a third-party/self-hosted server ([Forgejo](https://codeberg.org/forgejo/forgejo) [Gitea](http://about.gitea.com/), [GitLab](https://about.gitlab.com/)), or in a local network folder. When an artist works, they make a local copy of the repository, add or modify files, then commit and push those changes to the shared repository. We host our films on a self-hosted Forgejo server.


# Prerequisites

To follow this guide, make sure Git and Git-LFS are installed on your system.

- Install Git using the [official documentation](https://git-scm.com/install/) for your workstation's OS.
- Install Git-LFS using [GitHub's documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage) or the [official Git-LFS documentation](https://git-lfs.com/).

:::info Pre Receive Hooks
It is recommended to implement a [pre-recieve hook](https://projects.blender.org/infrastructure/gitea-custom/src/branch/main/hooks/deny_binary) on your git server to prevent users from pushing raw binary files, in the cases where they are not yet tracked by Git-LFS.
:::

## Create a Remote Repository
If you have a Git server, set up your repository first. It will be cloned to each workstation using the steps in the following sections. For more information, see the official [Git documentation](http://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository). Your repository URL should look something like this:
```bash
git@git.server.org:projects/my-project.git
```

::: info Storage Limits
If you use a Git hosting service such as GitHub, Gitea, or GitLab, check its storage limits for your project.
:::

## Create a Network Folder Repository
You can create a repository in a shared network folder without using a Git hosting service. To get started, run the following command.

```bash
git init --bare -b main --shared=group //server/share/projects/my-project.git

# This path will act as your repository url
//server/share/projects/my-repo.git
```

## Initializing your Repository
Next, add the initial configuration files to your local repository, commit them, and push the commit to the shared repository. Follow the workstation setup instructions for your operating system to make sure Git and Git LFS are installed.

```bash
mkdir /data/my_project && cd /data/my_project # Create and enter project folder
git clone {repo url} # Clone project to local repository
```

Now that your project is set up, add the initial Git configuration files.

Add the following `.gitignore` file to your repository:

```
/local
/shared

# Tempfiles
*.blend[0-9]
__pycache__

# Thumbnail files from Mac/Windows
Thumbs.db
ehthumbs.db
Desktop.ini
.DS_Store
```


Once saved, return to your Bash shell.

```bash
# Tell Git LFS what filetypes are "large files"
git lfs track '*.hdr' '*.png' '*.blend' '*.jpg' '*.exr'

# Commit and push to the shared repository
git add .gitattributes
git add .gitignore

git commit -m "Initial Commit"
git push -u origin main
```

## Set Up Workstations
1. Install Git using the [official documentation](https://git-scm.com/install/) for your workstation's OS.
2. Install Git LFS using [GitHub's documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage) or the [official Git LFS documentation](https://git-lfs.com/).
3. Install SourceGit from the [releases page](https://github.com/sourcegit-scm/sourcegit/releases).
4. Clone the repository using SourceGit.

 ![sourcegit repo setup](/media/git-setup/sourcegit_setup_repo.jpg)
