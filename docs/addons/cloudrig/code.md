# Contribute
This project has grown large enough that external contributors would be fairly welcome. Just [get in contact with Demeter](https://blender.chat/direct/mets) before you start coding. You can also [open an issue](https://projects.blender.org/Mets/CloudRig/issues) to discuss design and functionality before you start coding.

### Adding a new Component/Parameter
The implementation of CloudRig's [Component Types](cloudrig-types) are found in the `rig_components` folder of the repository. [Here](https://projects.blender.org/Mets/CloudRig/src/branch/master/CloudRig/rig_components/external_components/minimal_component.py), you will also find `external_components/minimal_component.py`, which is a template for you to create your own component types. Simply un-comment the last line of this file and [Reload Scripts](https://docs.blender.org/manual/en/5.0/advanced/operators.html#bpy-ops-script-reload) in Blender, to see it show up as a component type option. Generating it will create a bone and a constraint.

To start making your own component types, just copy this folder, and rename some things:
- The file name should be unique, as it defines the namespace for the parameters in Blender's RNA. So it might be a good idea to prefix all your files with some identifier.
- Change the class's `ui_name` property to something unique to show in the UI. Preferably stick to Title Case.
- See the template code and comments for further details.

### Conventions
- Functions inside rig components should be "non-public", ie. start with `__` OR, if they are overridden or called by child classes, use a prefix separated by `__` that signifies the root class. Eg., `def fk_chain__make_root_bone()` signifies that this function was originally defined in the fk_chain component, and is overridden by at least one child class. (Starting with Blender 5.1, we may want to start using Python 3.13's [@override](https://peps.python.org/pep-0698/) with strict mode, though I'm quite bothered by the fact that it doesn't allow specifying a base class.)
- Avoid code comments that instruct linters and auto-formatters.
- Use [PEP 585](https://peps.python.org/pep-0585/#abstract) or even more modern type annotations. Avoid older styles like [Generics](https://peps.python.org/pep-0484/#generics).
- Don't abbreviate too much. Avoid one-letter variable names completely.
- Use `self.add_log()` to create entries in the Generation Log interface to warn riggers about any suspiciously mis-configured things.
- Functions should be defined top to bottom in roughly the order they run.
- Follow CloudRig's bone naming style
    - Bone names should be derived from adding prefixes to metarig bone names, to ensure uniqueness.
    - As few prefixes as possible, but as many as needed. For animator-facing controls, I really advise limiting to 1 short prefix.
    - Avoid using the same prefix for different purposes; search the codebase before adding new ones.
    - Do not hard-code some bone to be called "Torso" or anything else, because then you can't have more than 1 instance of this component in the rig. 
    - Avoid .001 suffixes by using `increment_name()` function for nice clean name increments.

## Modules
Below are descriptions of each python module in CloudRig.

<details>
<summary> Repo root </summary>

#### \_\_init\_\_.py
Where CloudRig registers itself into Blender. We use a pattern where each sub-folder's `__init__.py` should import its contents and put them in a `modules` list. The listed modules will be traversed recursively, and any registerable classes they contain in a `registry` list will be registered, and their `register()` and `unregister()` functions will be called as appropriate.

---

#### manual_mapping.py
Makes sure right clicking on CloudRig properties and then clicking on Open Manual goes to the relevant page on this wiki.

---

#### prefs.py
The add-on preferences properties and root UI code. Saving preferences to file is inherited from `bs_utils`, as is hotkey drawing.

---

#### properties.py
Registration and definition of main generation-related PropertyGroups, ie. `Object.cloudrig` and `PoseBone.cloudrig_component`.

</details>

---

<details>
<summary> bs_utils </summary>

This is a [git sub-module](https://projects.blender.org/Mets/blender_studio_utils) of code shared with some of our other tools; Saving preferences to disk, hotkey registration, some UI utilities, custom property management, etc.

</details>

---

<details>
<summary> generation </summary>

#### actions_component.py
The [Actions](actions) generator feature is implemented here. UI is implemented in ui/actions_ui.py.

---

#### cloud_generator.py
The Generate Rig operator, and the top level of the generation process.

---

#### cloudrig.py
This is the file that gets loaded with all generated rigs and implements the [Rig UI](rig-ui). This script is not procedurally generated. Instead, a nested dictionary is written to a custom property during generation, called `ui_data`. This is mostly created by calls to `utils/ui.py/add_ui_data()`, and then used by `cloudrig.py` to draw the sidebar for animators, containing settings like IK/FK switching, parent switching, snapping and baking, and custom properties.

---

#### generate_test_animation.py
Implements "[Generate Action](generator-parameters#generate-action)" feature. Drawn in the Generation tab of a metarig.

---

#### naming.py
String utility functions used in creating and mirroring bone names.

---

#### troubleshooting.py
- The drawing, storage and functionality of the [Generation Log UI](troubleshooting) seen on metarigs.
- The `CloudLogManager` class which is instantiated by the generator (`self.logger`). Components have wrapper functions to auto-fill some parameters, those being `self.add_log()` and `self.raise_generation_error()`. These functions add entries to the log UI.
- Implements all "Quick Fix" operators that help riggers deal with minor problems quickly.
- Implements bug reporting and stack tracing functions.

</details>

---

<details>
<summary> metarigs </summary>

`__init__.py` implements the UI for adding Metarigs and Component Samples via the Object->Add->Armature Menu. Metarigs and Samples are technically the same thing, and both are loaded from `MetaRigs.blend`.

---

#### versioning.py

Metarig versioning.

All metarigs store a version number, and this module adds an app handler that runs on .blend file load, to check for metarigs whose version is lower than the currently installed CloudRig's metarig version. If it finds any, it will automatically do its best to upgrade the metarig's component types and parameters to the latest correct names and values.

For example, the `cloud_copy` and `cloud_tweak` bone types used to be a single component type with an enum to switch between the two behaviours. When that split was implemented, the old enum value was still accessible, and was used to assign the new correct component type, so users didn't have to do anything.

Be careful that versioning multiple changes to a single property should be done with care, or not at all, since if the versioning code is trying to write to a property that no longer exists, it will fail.

</details>

---

<details>
<summary> operators </summary>
Operators to help with authoring metarigs and speed up workflow. Each entry here links to the documentation of the functionality it implements.

- **[apply_bone_color_preset](organizing-bones#bone-colors)**
- **[better_bone_extrude](workflow-enhancements#better-duplicate-extrude)**
- **[copy_mirror_components](cloudrig-types#copy-mirror-components)**
- **[flatten_chain](cloudrig-types#flatten-bone-chain)**
- **[pie_bone_parenting](workflow-enhancements#bone-parenting-pie-p)**
- **[pie_bone_selection_ops & pie_bone_selection_ui](workflow-enhancements#bone-selection-pie-alt-d)**
- **[pie_bone_specials & symmetrize](workflow-enhancements#bone-specials-pie-x)**
- **[pie_custom_shapes](workflow-enhancements#edit-custom-shapes-pie-ctrl-alt-e)**
- **[toggle_action_constraints](actions#iterating)**
- **[toggle_metarig](workflow-enhancements#metarig-swapping-generation)**

</details>

---

<details>
<summary> rig_component_features </summary>

#### widgets/widgets.py
Implements loading custom shapes, either from the Widgets.blend file, or a file provided by the user via the preferences, or the currently opened .blend file. Also some other custom shape-related utilities.

---

#### widgets/widgets_pre_save.py
Used by `Widgets.blend` to do automatic housekeeping: Sorting widget geometry topology, which is required for dashed overlay drawing.

---

#### bone_gizmos.py
[Bone Gizmos](https://projects.blender.org/studio/blender-studio-tools/src/branch/main/docs/addons/bone_gizmos.md) is/was an experimental/abandoned add-on of mine, and this module allows components to interface with it. Currently dead code, but might make a return one day.

---

#### bone_info.py
Abstraction layer for bones, constraints and drivers, which are used all over CloudRig. These avoid a lot of headaches that come with interacting with real Blender data directly (in exchange for other, smaller headaches!).

Existing bones are loaded into BoneInfo instances in `load_metarig_bone_infos()`, which are then turned back into real bones in `write_edit_data()` and `write_pose_data()`.

---

#### bone_set.py
CloudRig's [bone organization](organizing-bones) system that takes care of creating sets of parameters to customize the collection and color assignment of bones. All BoneInfo instances created during generation should be created with my_bone_set.new(), to ensure that every bone can be organized by the rigger.

---

#### custom_props.py
Implements the [shared parameters](cloudrig-types#shared-features) for to storing and displaying custom properties in the rig UI.

---

#### generate_animation.py
Functions used by [cloud_fk_chain](cloudrig-types#cloud_fk_chain) and the [Generate Action](generator-parameters) feature.

---

#### mechanism.py
Houses the CloudMechanismMixin mix-in class which is inherited by all component types and provides generic utilities to manipulate bones, constraints and drivers.

---

#### object.py
Houses CloudObjectUtilitiesMixin which is inherited by all component types and provides generic utilities to control actual Blender objects, such as making things visible, assigning things to collections, transform locks, etc.

---

#### overlay_painter.py
Manages overlay drawing for component types, useful for getting live feedback on certain properties without having to re-generate the entire rig. Any component type can implement a very simple `draw_overlay` function, which will receive an instance of `OverlayPainter`, which abstracts away a lot of boilerplate code so that component types can focus on high level implementation and object-space transformations.

---

#### params_ui_utils.py
Implements UI drawing utilities for drawing parameters of [Component Types](cloudrig-types).

---

#### parenting.py
UI for the [Parent Switching shared parameters](cloudrig-types#shared-features). This just means creating certain UI data, drivers and constraints, which cloudrig.py will use for displaying parent switching sliders and operators. Those operators are implemented in cloudrig.py.

---

#### properties_ui.py
Implements the [UI Editor](properties-ui#ui-editing-workflow).

</details>

---

<details>
<summary> rig_components </summary>

All the [component types](cloudrig-types) in CloudRig.

All component types inherit from `cloud_base.py/Component_Base`.
Entry points are of course `__init__()` and `create_bone_infos()`.

---

#### external_components
Example code of how you can [implement your own components](#adding-a-new-component-parameter), showing both an ultra-minimal case, and one showing off some of CloudRig's features.

</details>

---

<details>
<summary> ui </summary>

- **actions_ui**: UI for the [Action system](actions).
- **cloudrig_main_panel**: The "CloudRig" panel and "General" sub-panel in `Properties->Armature->CloudRig`.
- **component_list**: The "Component List" sub-panel in `Properties->Armature->CloudRig`.
- **component_param_panels**: The parameter sub-panels in `Properties->Bone->CloudRig Component`.
- **menu_3dview**: The "CloudRig" header menu in the 3D Viewport while in Armature Pose/Edit mode.

</details>

---

<details>
<summary> utils </summary>

- **curve.py**: Utility functions used by curve-based components, particularly to help with curve symmetry.
- **lattice.py**: Some utilities used by the `cloud_lattice` component, taken from my [Lattice Magic](https://extensions.blender.org/add-ons/latticemagic/) add-on.
- **maths.py**: Any pure math, even if it is only used in one place, goes here. That means this module should never import anything from any other part of CloudRig.
- **misc.py**: Code that hasn't been organized yet. Ideally this module shouldn't exist, since it's not clear what is in it.
- **post_gen.py**: Code that could be useful to run from post-generation scripts. Not actually used anywhere in CloudRig's code.
- **rig.py**: Armature related maths.

</details>

---

<details>
<summary> tests </summary>

Implements tests. [This task](https://projects.blender.org/Mets/CloudRig/issues/242) keeps track of what features do and don't have tests implemented, and the [ReadMe](https://projects.blender.org/Mets/CloudRig/src/branch/master/tests#how-to-run-tests) explains how to run the tests yourself locally.

</details>