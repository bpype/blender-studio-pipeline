## 1.1.3

## CHANGED

- rename and relink brushstroke layer objects according to the new surface object when copying from one object to another [#416](https://projects.blender.org/studio/blender-studio-tools/pulls/416)

## FIXED

- Fix issue when multiple windows and scenes by getting rid of `bpy.context` in multiple places [#420](https://projects.blender.org/studio/blender-studio-tools/pulls/420)

## 1.1.2 - 2025-07-04

### CHANGED

- link brushstrokes to same collections as surface object rather than the active collection [#390](https://projects.blender.org/studio/blender-studio-tools/pulls/390)
- operator to copy over resources shows now also on minor version bumps [#405](https://projects.blender.org/studio/blender-studio-tools/pulls/405)
- auto-updating the resources now only happens when no explicit resource directory is specified [#405](https://projects.blender.org/studio/blender-studio-tools/pulls/405)

### FIXED

- fix color sampling from curves under deformation [#391](https://projects.blender.org/studio/blender-studio-tools/pulls/391)
- fix Eevee tile brushstroke sampling [#404](https://projects.blender.org/studio/blender-studio-tools/pulls/404)

## 1.1.1 - 2025-01-17

### FIXED

- fix losing brushstroke context material on new preset initialization ([#365](https://projects.blender.org/studio/blender-studio-tools/pulls/365))
- fix accumulation of default brush style datablocks ([#366](https://projects.blender.org/studio/blender-studio-tools/pulls/366))
- fix handling of incremental suffix on brush style datablocks ([#366](https://projects.blender.org/studio/blender-studio-tools/pulls/366))

## 1.1.0 - 2025-01-14

### ADDED
- subpanel compatibility in preparation for Blender 4.4 ([#347](https://projects.blender.org/studio/blender-studio-tools/pulls/347))
- add operator to install brush style packs ([#348](https://projects.blender.org/studio/blender-studio-tools/pulls/348))
- change brush style selection to dialog with name, category and type filtering ([#348](https://projects.blender.org/studio/blender-studio-tools/pulls/348))
- extended documentation for custom brush style creation ([Link](https://studio.blender.org/tools/addons/brushstroke_tools#additional-brush-styles))
- track `brush_stroke.curve_parameter` attribute on original curves for draw layers ([#349](https://projects.blender.org/studio/blender-studio-tools/pulls/349))
- add `Taper Shift` parameter to draw layers ([#349](https://projects.blender.org/studio/blender-studio-tools/pulls/349))
- warnings when toggling deformable (mirrored surface/grease pencil) ([#357](https://projects.blender.org/studio/blender-studio-tools/pulls/357))
- add more advanced color variation interface with more nuanced control ([#362](https://projects.blender.org/studio/blender-studio-tools/pulls/362))
- add `Upgrade Resources` operator in advanced panel to upgrade all resources in the file to library the version ([#362](https://projects.blender.org/studio/blender-studio-tools/pulls/362))

### CHANGED

- change resource directory structure and to allow auto-updates while preserving user data ([#362](https://projects.blender.org/studio/blender-studio-tools/pulls/362))

### FIXED
- fix row count connection in stroke mapping node-group for custom brush style creation ([e301a56b4bb0](https://projects.blender.org/SimonThommes/blender-studio-tools/commit/e301a56b4bb016d37291030bd35c1f88ff2b1487))
- fix error when appending brush style that contains already packed images ([#348](https://projects.blender.org/studio/blender-studio-tools/pulls/348))
- fix issue with property type mismatch by implicit type casting ([#361](https://projects.blender.org/studio/blender-studio-tools/pulls/361))
- fix incorrect length matching behavior ([#362](https://projects.blender.org/studio/blender-studio-tools/pulls/362))
- fix registry error when un- and reregistering add-on ([#363](https://projects.blender.org/studio/blender-studio-tools/pulls/363))

## 1.0.4 - 2024-11-11

### FIXED
- fix incorrect path use for material import ([#346](https://projects.blender.org/studio/blender-studio-tools/pulls/346))
- fix registry issue by not importing brushstrokes on addon registry ([#346](https://projects.blender.org/studio/blender-studio-tools/pulls/346))
- add nullcheck for no context material ([#346](https://projects.blender.org/studio/blender-studio-tools/pulls/346))

## 1.0.3 - 2024-11-11 

### FIXED
- use pathlib for cross-platform compatibility ([#344](https://projects.blender.org/studio/blender-studio-tools/pulls/344))

## 1.0.2 - 2024-11-07 

### FIXED
- fix manifest ([#341](https://projects.blender.org/studio/blender-studio-tools/pulls/341))

## 1.0.1 - 2024-11

### ADDED
- Initial Version ([#328](https://projects.blender.org/studio/blender-studio-tools/pulls/328))
