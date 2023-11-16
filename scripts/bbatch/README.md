# bbatch
`bbatch` is a command line tools to crawl directories for .blend files and execute a provied script.
## Table of Contents
- [Prerequisite](#prerequisite)
- [Installation](#installation)
- [How to get started](#how-to-get-started)

## Prerequisite
In order to use this tool you need:
- Python 3.5+

## Run 
This folder contains a command line tool that doesn't require installation to use properly. This tool doesn't require installation to be run. To run `bbatch` without installation follow the steps below.
1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. Run `cd blender-studio-pipeline/scripts/bbatch` to enter directory
3. Run program with `python bbatch /my-folder/` 


## Installation (OPTIONAL)
Download or clone this repository. This repository is a command line tool that can be installed with the python packaging manager. Installation is an optional step only intended for advanced users.
This script does the following (follow this if you want to do this manually or on another platform):

1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. Run `cd blender-studio-pipeline/scripts/bbatch` to enter directory
3. Install with `pip install .`
4. Run with `bbatch /my-folder/`
5. Get help with `bbatch -h`

## How to get started
Run directly out of repo folder or follow above installation instructions. Give `bbatch` a path to a .blend file or a folder as first argument, The detected blend files will be opened in the background, the python script will be executed, and the file closes. If blender is not installed at the default location of your computer, you need to provide a blender executable using the --exec flag.

If a script is provided, `bbatch` will automatically save after execution of the script, without saving any backups aka [save versions](https://docs.blender.org/manual/en/latest/editors/preferences/save_load.html#:~:text=of%20using%20characters.-,Save%20Versions,-Number%20of%20versions). If you already have saving logic in your provided script, skip this step using the "--nosave" flag.

| Command      | Description |
| ----------- | ----------- |
| --script| Path to blender python script(s) to execute inside .blend files during crawl.|
|  -n, --nosave|Don't save .blend after script execution.|
| -r, --recursive| If provided in combination with a folder path will perform recursive crawl|
| -f  --filter| Provide a string to filter the found .blend files|
| -a, --ask| If provided there will be a prompt for confirmation before running script on .blend files.|
| -p, --purge| Run 'built-in function to purge data-blocks from all .blend files found in crawl, and saves them.|
| --exec| If provided user must provide blender executable path, OS default blender will not be used if found.|
| -h, --help| show the above help message and exit|


## Usage Examples

| Action | Command |
| ----------- | ----------- |
|Prints the names of .blends in Current Directory  | `bbatch ./` |
|Print the names of .blends Recursively | `bbatch /my-folder/ --recursive` | 
|Print only the names of .blends matching a provided string |`bbatch /my-folder/ --find string`|
|Run default 'Purge' script on .blends in Current Directory |`bbatch /my-folder/ --purge`|
|Run custom script on all .blends in Current Directory |`bbatch /my-folder/ --script /my-directory/my-script.py`|
|Ask/Prompt before script execution|`bbatch /my-folder/ --script /my-directory/my-script.py --ask`|
|Run script on .blends without saving |`bbatch /my-folder/ --script /my-directory/my-script.py --nosave` |
|Run with a custom blender executable|`bbatch /my-folder/ --exec /path-to-blender-executable/blender`|

