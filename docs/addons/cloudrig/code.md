# Contribute
This project has grown large enough that external contributors would be fairly welcome. Just [get in contact with Demeter](https://blender.chat/direct/mets) before you start coding. You can also [open an issue](https://projects.blender.org/Mets/CloudRig/issues) to discuss design and functionality before you start coding.

### Adding a new Component/Parameter
The implementation of CloudRig's [Component Types](cloudrig-types) are found in the `rig_components` folder of the repository. Here, you will also find `external_components/my_component.py`, which is a template for you to create your own component types. Simply un-comment the last line of this file and Reload Scripts in Blender, to see it show up as a component type option. Generating it will create a bone and a constraint.

To start making your own component types, just copy this folder, and rename some things:
- The file name should be unique, as it defines the namespace for the parameters in Blender's RNA. So it might be a good idea to prefix all your files with some identifier.
- Change the class's `ui_name` property to something unique to show in the UI. Preferably stick to Title Case.
- See the template code and comments for further details.

### Conventions
- Do as I say, not as I do.
- All functions inside rig components should be "private", ie. start with `__` OR, if they are overridden or called by child classes, use a prefix separated by `__` that signifies the root class. Eg., `def fk_chain__make_root_bone()` signifies that this function was originally defined in the fk_chain component, and is overridden by at least one child class.
- Avoid code comments that instruct linters and auto-formatters.
- Use PEP 585 or even more modern type annotations. Avoid older styles like PEP 484.
- Don't abbreviate too much. Avoid one-letter variable names completely.
- Use `self.add_log()` to create entries in the Generation Log interface to warn riggers about any suspiciously mis-configured things.
- Functions should be defined top to bottom in roughly the order they run.
- Functions that override an inherited one should specify in the docstring what they are overriding from. (And once Blender's Python version supports the @override decorator, use that.)
- Follow CloudRig's bone naming style
    - Bone names should be derived from adding prefixes to metarig bone names, to ensure uniqueness.
    - As few prefixes as possible, but as many as needed. For animator-facing controls, I really advise limiting to 1 short prefix.
    - Avoid using the same prefix for different purposes; search the codebase before adding new ones.
    - Do not hard-code some bone to be called "Torso" or anything else, because then you can't have more than 1 instance of this component in the rig. 
    - Don not alter suffixes (".L"/".R"), so avoid adding .001. Instead, see `increment_name()`.

## Modules
Below are descriptions of each python module in CloudRig.

<details>
<summary> generation </summary>

- #### cloud_generator.py
This module holds the generation operator, and the top level of the generation process.

- #### actions_component.py
The [Actions](actions) generator feature is implemented here. UI is implemented in ui/actions_ui.py.

- #### naming.py
String operators useful in creating and mirroring bone names. `CloudNameManager` is instantiated by the generator. Component types have a `self.naming` shorthand to this.

- #### test_animation.py
The "Generate Test Action" feature is implemented here. This is drawn in the Generation tab of a metarig, and it works with FK Chain components to save you time in creating an animation where you rotate all the joints to test deformations.

- #### troubleshooting.py

- The drawing, storage and functionality of the Generation Log UI seen on metarigs.
- The `CloudLogManager` class which is instantiated by the generator (`self.logger`). Components have wrapper functions to auto-fill some parameters, those being `self.add_log()` and `self.raise_generation_error()`. These functions add entries to the log UI.
- All Quick Fix operators that help quickly fix minor problems.
- Bug reporting and stack tracing functions.

- #### cloudrig.py
This is the file that gets loaded with all generated rigs. This script is not procedurally generated. Instead, a nested dictionary is written to a custom property during generation, called `ui_data`. This is mostly created by calls to `utils/ui.py/add_ui_data()`, and then used by cloudrig.py to draw the sidebar for animators, containing settings like IK/FK switching, parent switching, snapping and baking, and custom properties.

</details>

<details>
<summary> metarigs & versioning </summary>

The `__init__.py` here implements the metarigs and component samples UI lists that appear in the Object->Add->Armature UI. Metarigs and Samples are technically the same thing, and both are loaded from MetaRigs.blend.

**versioning.py**

Metarig versioning.

All metarigs store a version number, and this module adds an app handler that runs on .blend file load, to check for metarigs whose version is lower than the metarig version of the add-on. If it finds any, it will automatically do its best to upgrade the metarig's component types and parameters to the latest correct names and values.

For example, the `cloud_copy` and `cloud_tweak` bone types used to be a single component type with an enum to switch between the two behaviours. When that split was implemented, the old enum value was still accessible, and was used to assign the new correct component type, so users didn't have to do anything.

Be careful that versioning multiple changes to a single property should be done with care, or not at all, since if the versioning code is trying to write to a property that no longer exists, it will fail.

</details>


<details>
<summary> operators </summary>
Operators to help with authoring metarigs and speed up workflow.

- **better_bone_extrude**: Binds to the E key, overwriting Blender's default bone extrude operator. Extruding a bone named "Bone1" will result in a bone named "Bone2" rather than "Bone1.001".
- **bone_selection_pie_ops**: Operators for the bone selection pie menu, bound to Alt+D in armature pose/edit/weight paint modes.
- **bone_selection_pie_ui**: UI elements for said pie menu.
- **copy_mirror_components**: Operators for copying and mirroring metarig component parameters. Found in the CloudRig header menu in the 3D View.
- **edit_widget**: An operator bound to Ctrl+Alt+E to toggle edit mode on a bone's widget.
- **flatten_chain**: Flatten a bone chain along a plane, useful for straightening limbs for good IK behaviour. Drawn in the IK Chain component's UI.
- **pie_bone_parenting**: Pie menu bound to the P key for bone parenting, even in pose mode.
- **pie_bone_specials**: Pie menu bound to the X key for deletion and symmetry in armature pose/edit modes.
- **symmetrize**: The improved symmetrize functionality found in the above pie menu.
- **toggle_action_constraints**: Useful in Action-based rigging workflow, button is drawn in the Action editor header.
- **toggle_metarig**: Toggle between metarig and generated rig (visibility, object mode, bone collections, bone selection). Default shortcut: Shift+T.

</details>


<details>
<summary> rig_component_features </summary>

- #### widgets/__init__.py
Like metarigs, most widgets are appended from a Widgets.blend file. This is used

- #### bone_gizmos.py
Bone Gizmos is an experimental/abandoned add-on of mine, and this module allows components to interface with this add-on.

- #### animation.py
Functions used by [cloud_fk_chain](cloudrig-types#cloud_fk_chain) and the [Generate Test Animation](generator-parameters) feature.

- #### bone_set.py
CloudRig's bone organization system that takes care of creating sets of parameters to customize the collection and color assignment of bones. All BoneInfo instances created during generation should be created with my_bone_set.new(), to ensure that every bone can be organized by the rigger.

- #### bone.py
Abstraction layer for bones, constraints and drivers, which are used all over CloudRig. These avoid a lot of headaches that come with interacting with real Blender data directly (in exchange for other, smaller headaches!).

Existing bones are loaded into BoneInfo instances in `load_metarig_bone_infos()`, which are then turned back into real bones in `write_edit_data()` and `write_pose_data()`.

- #### mechanism.py
Houses the CloudMechanismMixin mix-in class which is inherited by all component types and provides generic utilities to manipulate bones, constraints and drivers.

- #### custom_props.py
Implements the shared parameters of all component types relating to storing and displaying custom properties in the rig UI.

- #### object.py
Houses CloudObjectUtilitiesMixin which is inherited by all component types and provides generic utilities to control actual Blender objects, such as making things visible, assigning things to collections, transform locks, etc.

- #### parent_switching.py
UI for the [Parent Switching shared parameters](cloudrig-types#shared-parameters). This just means creating certain UI data, drivers and constraints, which cloudrig.py will use for displaying parent switching sliders and operators. Those operators are implemented in cloudrig.py.

- #### ui.py
Houses CloudUIMixin which is inherited by all component types and provides utilities for drawing the UI of parameters as well as storing UI data. The `add_ui_data()` function is used to store data in the rig's `ui_data` custom property, which will be later read by cloudrig.py in `draw_rig_settings()` to draw the rig's UI.

</details>


<details>
<summary> rig_components </summary>

All the [component types](cloudrig-types) in the feature set.
Also has cloud_template which is the base I use when starting a new component type.

All component types inherit from cloud_base.py/Component_Base.
Entry points are of course `__init__()` and `create_bone_infos()`.

</details>


<details>
<summary> ui </summary>

- **actions_ui**: UI for the Action system.
- **cloudrig_dropdown_menu**: The "CloudRig" editor header menu in armature pose/edit mode.
- **cloudrig_main_panel**: The "CloudRig" panel and "Generation" sub-panel in the Properties editor on armatures.
- **rig_component_list**: The "Component List" sub-panel in the Properties->Armature editor.
- **rig_component_subpanels**: The parameter sub-panels in the Properties->Bone editor.
- **rig_component_ui**: The parameter main panel in the Properties->Bone editor.

</details>


<details>
<summary> utils </summary>

- **curve.py**: Utility functions used by curve-based components, particularly to help with curve symmetry.
- **lattice.py**: Some utilities used by the `cloud_lattice` component, taken from my Lattice Magic add-on.
- **maths.py**: Any pure math, even if it is only used in one place, goes here. That means this module should never import anything from any other part of CloudRig.
- **misc.py**: Code that hasn't been organized yet. Ideally this module shouldn't exist, since it's not clear what is in it.
- **post_gen.py**: Code that could be useful to run from post-generation scripts. Not actually used anywhere in the add-on.

</details>

<details>
<summary> Repo root </summary>

**`__init__.py`**
Where the add-on registers itself into Blender's RNA system. I implement a pattern where each sub-folder's `__init__.py` should import its contents and put them in a "modules" list. The listed modules will be traversed recursively here, and any registerable classes they might store in a "registry" list will be registered, and their register() and unregister() functions will be called as appropriate.

**manual.py**

Makes sure right clicking on CloudRig properties and then clicking on Open Manual goes to the relevant page on this wiki.

</details>
