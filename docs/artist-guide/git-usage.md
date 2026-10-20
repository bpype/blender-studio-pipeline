# Using Git

Your Git repository will be the central source of truth for your project. You can host it remotely using a third-party/self-hosted server ([Forgejo](https://codeberg.org/forgejo/forgejo) [Gitea](http://about.gitea.com/), [GitLab](https://about.gitlab.com/)), or in a local network folder. When an artist works, they make a local copy of the repository, add or modify files, then commit and push those changes to the shared repository. We host our films on a self-hosted Forgejo server.


## Prerequisites
First, make sure your project is set up on your workstation using the [Git setup guide](/td-guide/git-setup.md).


## Before you work

Before you start working, pull the latest changes your colleagues have pushed to the repository.

1. Select the "down arrow" Pull Changes icon from the top bar.
2. Under "Local Changes" make sure to enable "Stash & Re-apply" to keep any changes in your local repository.

![Pull Changes](/media/git-setup/sourcegit-pull_changes.jpg)

Once your repository is up to date, open your project file and make your changes.

## After Your Work

Commit and push your changes to add them to the shared repository's history.

1. Select the Local Changes tab from the sidebar.
2. Review your list of changes, click the "Down Arrow" icon to "stage" these changes.
3. Write a commit message describing your changes.
4. Select Commit & Push to submit your changes to the shared repository.

![Git Commit](/media/git-setup/sourcegit-commit.jpg)
