## 1.0.1 - 2023-08-02 
 
### ADDED 
- Add svn checkout workflow

### FIXED 
- Fix error initializing in a fresh folder
- Fix minor error
- Fix Changelog Rendering (#125)
- Fix Gazu Module out of sync (#119)
- Fix UI error when cancelling a checkout
- Fix some errors when initializing the addon
- Fix process not set is_running=False on error
- Fix line ends from DOS to UNIX (#68)

### UN-CATEGORIZED 
- UX improvements (#136)
- Checkout, Multi-Repo, Optimizations & Clean-up' (#104) from Mets/blender-studio-pipeline:SVN-improvements into main
- autopep8
- Allow downloading repo version in bg
- Improve UX when moving between repositories
- Optimize log filtering
- Massive UI drawing performance boost
- Better msgs on why repo isn't authenticating
- Don't auth if repo non-existent
- Cleanup Add-on Changelogs

## 0.2.1 - 2023-06-02 
 
### ADDED 
- Add a debug UI toggle
- Multi-repository support


### FIXED 
- Fix Addon Install Instructions
- Fix Revert operator not working
- Fix Addons Spelling and Links (#54)
- Fix error in writing credentials to file
- Fix URL reading on linux
- Fix crash in update_file_list()

## CHANGED
- SVN Cleanup now resets background threads
- Allow context menus to open .blend files
- More restructuring, added a ProcessManager.
- Auto-authenticate when add-on is enabled
- Store credentials on disk
- UX improvements
- Restructure add-on

## REMOVED
- Nuke BAT dead code and relevant UI/UX.