## 0.1.6 - 2024-02-28 
 
### FIXED 
- Fix Sequence Playblast from 3D Viewport UX
- Rename Edit Render to Edit Export (#249)

## 0.1.5 - 2024-02-23 
 
### ADDED 
- Add Import Edit Render Operator for Shots (#236)
- Add Debug Print to Shot Builder
- Add Layout Template to Shot Builder
- Add Edit to context
- Add missing init_cache_variables
- Add Sequence Playblast Support (#176)
- Add 'Shot as Image Sequence' Documentation
- Replace "blender_kitsu" with __package__ so it can be an extension (#195)
- Use New Kitsu Context UI in Shot Builder (#210)
- Check if TV Show based on Production Type (#209)
- Support Multiple Rigs in Check Action Names
- Use Updated Naming Convention when Setting Action Names
- Added New Kitsu Context UI (#187)
- Episode support for playblasts
- Move episode selection to viewport
- Preference labels tweaks
- Refactor Shot Builder (#183)

### FIXED 
- Fix Render Review Metastrips (use new naming convention)
- Fix Kitsu Context in Shot Builder
- Fix Bug Edit Tasks Panel not Appearing in Edit Context
- fix task type filtering for the active project (#216)
- Fix hooks directory path (#219)
- fix pull edit for episodic workflow and shot starting on frame 0 (#211)
- Fix Bug Getting Add-On Preferences in Anim Module
- fix episode's sequence creation (#202)
- Fix Shot Builder crash if saving fails
- Fix typo
- Fix README Table of Contents
- Fix Typo in README Credits
- Fix bug in `is_edit_file()` check
- Set Fake User on all Actions that are Renamed
- Only Rename Actions in Scene Collection & Fix Removing Empty Actions (#239)
- Shot Builder Remove Actions When Building New Shots
- Shot Builder skip output collection for lighting task
- Shot Builder set play head to shot's first frame
- Shot Builder load reference video using "ORIGINAL" fit method
- Update Default Frame Offset Value
- Improve Edit Playblast UX (#225)
- Rename 'Render Thumbnail' to 'Render Still' (#86)
- Shot Builder fix bug if no template is found
- Use Relative Paths in Asset Index JSON File
- Include Episode in Shot Builder Paths & Improve 3d_start (#192)
- Improve Cache (#191)
- Separate context episode selector
- Make kitsu.category entry singular
- Episode support fixes
- Refactor Context panel drawing

### REMOVED 
- Remove `svn` from project root directory (#215)
- Remove duplicated episode selector (#193)
- Remove unused HISTORY.md
- Remove box layout in 3D view
- Remove episode from prefs

## 0.1.4 - 2023-10-31 
 
### ADDED
- Make Frames directory customizable 

### FIXED 
- Fix Drawing Sequence Line (#157)
- Fix Scene Name in Shot Builder Config File
- Fix EXR Colorspace Name
- Fix Bug "3d_start" missing on new shots
- Fix Scene Name in Shot Builder Config File
- Fix Shot Builder example�`assets.py`
- Fix Shot Builder example `shots.py`
- Fix Get Project ID from Kitsu Server in Shot Builder
- Fix Context Override Error in Shot Builder
- Update Shot Builder Hook Example
- Use New Shared Folder Structure

### REMOVED 
- remove "boxed" ui for playblast


## 0.1.3 - 2023-08-02 
 
### ADDED 
- Add Operator to Replace .mp4 with Image Sequences (#132)
- Add Frame Range Pop-up (#128)
- Add option to create tasks during Submit New Shot (#121)
- Add option to Exclude Collections from Output Collection (#120)
- Add Operator to Push Frame Start (#98)

### FIXED 
- Fix Enforce Black Formatting
- Fix Changelog Rendering (#125)
- Fix Gazu Module out of sync (#119)
- Fix typo in Frame Range Calculation
- Fix Frame Range Warning if no context is found
- Fix Shot Builder Frame Range Calculation
- Fix Render Still/Movie from Edit (#97)
- Shot Builder Add Directory Layout to README
- Fix hang when using Kitsu Server is not found during login (#79)

### REMOVED 
- Remove dependence on Editorial Export Path
- Remove Metastrip Filepath (#80)

## 0.1.2 - 2023-06-19 
 
### ADDED 
- Add option to cleanup empty actions (#73)

### FIXED 
- Fix "add_preview_to_comment"
- Fix Keep existing actions during `Check Action Names` (#75)
- Fix bug in frame range calculation (#72)
- Fix line ends from DOS to UNIX (#68)
- Set Custom Thumbnail during Playblast (#77)
- Use Background  Thread for Kitsu Login (#79)
- Rename 'Render Thumbnail' to 'Render Still' (#86)

### REMOVED 
- Remove Metastrip Filepath (#80)


## 0.1.1 - 2023-06-02 
 
### ADDED 
- Add "FX-" to output collection (#59)

### FIXED 
- Fix Addon Install Instructions
- Fix "Update output collection"
- Fix PyGPU Key (#60)
- Fix Addons Spelling and Links (#54)
- Make PyGPU enum backwards compatible
- Fix Frame Start & Frame End Calculation (#46)
- Push Seq - restore gen_output_path() (#45)
- Add Operators to cleanup Animation Files (#38)