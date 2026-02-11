Pipeline release is a script to package all addons into a single zip on the pipeline repository.

## Prerequisite
In order to use this tool you need:
- GIT & GIT LFS installed
- Python 3.11+
- [Requests Module](https://requests.readthedocs.io/en/latest/)

## Generate Token
A Gitea API token is required to generate a pipeline release.
1. Navigate to https://projects.blender.org/user/settings/applications while logged in
2. Under Select Permissions, Set `repository` and `package` scopes to "Read & Write"
3. Save the provided API key in the root of the pipeline-release directory with the name `api_token.env`

## Run 
This folder contains a command line tool that doesn't require installation to use properly. To run `pipeline_release` without installation follow the steps below.
1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-tools.git`
2. Run `cd blender-studio-tools/scripts/pipeline_release` to enter directory
3. Run program with `python -m pipeline_release`

## Options
- `--local`: Create addon zip in the `dist/` directory instead of uploading to the release server.

