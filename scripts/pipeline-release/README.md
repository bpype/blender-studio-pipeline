Pipeline release is a script to package addons in the pipeline repo.

# Features
 - Automatically Find Commits since last version for each addon in `scripts-blender/addons/`
 - Appends changelog to existing `CHANGELOG.md` per addon
 - Bump Version on `__init__.py` file
 - Commits `__init__.py` and `CHANGELOG.md` to current branch (user must manually push changes)
 - Creates Archive with Checksum in `dist` folder

## Prerequisite
In order to use this tool you need:
- GIT
- Python 3.11+
- [Requests Module](https://requests.readthedocs.io/en/latest/)

## Generate Token
A Gitea API token is required to generate a pipeline release.
1. Navigate to https://projects.blender.org/user/settings/applications while logged in
2. Under Select Permissions, Set `repository` and `package` scopes to "Read & Write"
3. Save the provided API key in the root of the pipeline-release directory with the name `api_token.env`

## Run 
This folder contains a command line tool that doesn't require installation to use properly. To run `pipeline_release` without installation follow the steps below.
1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. Run `cd blender-studio-pipeline/scripts/pipeline_release` to enter directory
3. Run program with `python -m pipeline_release` 

## How to get started

| Command      | Description |
| ----------- | ----------- |
|  -m, --major|Bump the major version number, otherwise bump minor version|
| -n --name| Name of addon(s) folder to update. All addons will be checked if flag is not provided|
| -c  --commit| Title of commit to consider basis of latest release, otherwise the last commit called 'Version Bump:' will be used|
| -f  --force|Bump version even if no commits are found|
| -t, --test |Test release system by only running locally and skip committing|
| -h, --help| show the above help message and exit|


## Changelog Conventions
|Changelog Title| Commit Prefix|
| ----------- | ----------- |
|ADD |add|
|BUG FIX |fix|
|CHANGED |change|
|REMOVED |remove|
|MERGED |merge|
|DOCUMENTED|doc|
|BREAKING|breaking|


This tool will automatically generate changelog messages based on the "changelog categories" below. Commit's subject line convention is `{Name of Addon}: {category} commit content` for example: 
### Commit Subject Line: 
```
Blender Kitsu: Fix naming conventions
```` 

### Changelog Output:
```
### Fixes
- Fix naming conventions
```

## Example Usage
| Action | Command |
| ----------- | ----------- |
|Create a new minor version if available of all addons|`python -m pipeline_release`|
|Create a new major version if available of all addons|`python -m pipeline_release -m`|
|Create a new version even no new commits are found|`python -m pipeline_release` -f|
|Only check if addon has this name(s) |`python -m pipeline_release -n "blender_kitsu, blender_svn"`|
|Find a commit that matches this message and uses as version basis otherwise the last commit called 'Version Bump:' will be used |`python -m pipeline_release -c "Commit MSG"`|