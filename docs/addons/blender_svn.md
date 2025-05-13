# Blender SVN
This add-on allows you to interact with the Subversion version control system from within Blender.

[Blender-SVN Demo Video](https://studio.blender.org/films/charge/gallery/?asset=5999)

## Installation
Find installation instructions [here](https://studio.blender.org/tools/addons/overview).

Make sure you have an SVN client installed, such that typing `svn` in the command line gives a result. Just Google "how to install SVN on Windows".

## Features
### SVN Operations
- Download updates, commit changes, resolve conflicts, all from within Blender.
- You can also add repositories in the add-on preferences UI.
- SVN Operations happen in a background process, so you can continue using Blender. The exception is cases where you are updating the file that is currently open. In that case, Blender will freeze it loads the newly updated file.

### Live File Statuses
- A list shows all files in the repository that are outdated, modified, newly added, replaced, conflicted, etc, with the relevant available operations next to them. The currently opened .blend file is always shown in the list.
- The file statuses automatically update every few seconds. If you do an SVN operation, the file statuses update immediately.
- Searching for a file name will also show files that aren't modified.
- You can right click on a file in the SVN file list to open it or the folder containing it.

### File History Overview
- SVN Log is saved to disk, so a full log is always available and searchable, and you can easily open the older version of a .blend file.
- You can search by author, date, commit message, revision number, anything.
- Toggle between a full SVN log of the entire repository, or just the history of a selected file.

### Blender-specific features
- When opening a .blend file that is in a repository, it is automatically detected. If that repository is already in your list of repositories, it will become the active one. Otherwise, you are prompted to enter your SVN credentials.
- If you're working in an outdated file, Blender will show a constant, very aggressive warning, since this could result in wasted work.

## Notes
- SVN Checkout is not supported due to limitations with giving progress feedback in the UI for such a long process. Do your checkouts via the command line.
- The speed at which your SVN server can answer requests will greatly affect your experience using the add-on, or any other SVN interface.
