# Modules
Here are descriptions of each python module (file) in CloudRig.


<details>
<summary> generation </summary>

#### cloud_generator.py
This module holds the generation operator, which is an important code entry point. From there, you can walk through the entire generation process.

#### actions_component.py
The [Actions](Actions) generator feature is implemented here. UI is implemented in ui/actions_ui.py.

#### naming.py
Houses CloudNameManager, which is instantiated by the generator and referenced from all rigs via self.naming, and provides string operators useful in creating and mirroring bone names.

#### test_animation.py
The "Generate Test Action" feature is implemented here. This is drawn in the Generation tab of a metarig, and it works with FK Chain components to save you time in creating an animation where you rotate all the joints to test deformations.

#### troubleshooting.py
All troubleshooting features:
- The drawing, storage and functionality of the Generation Log UI seen on metarigs.
- The CloudLogManager class which is instantiated by the generator as self.logger. Components have wrapper functions to auto-fill some parameters, those being `self.add_log()` and `self.raise_generation_error()`. These functions add entries to the log storage.
- All Quick Fix operators that help quickly troubleshoot various problems.
- Bug and stack trace reporting functions (opening the Issues page on this repo and pre-filling it with useful information)

#### cloudrig.py
This is the file that gets loaded with all generated rigs. This script is not procedurally generated. Instead, a nested dictionary is written to a custom property during generation, called 'ui_data'. This is mostly created in `utils/ui.py/add_ui_data()`, and then used by cloudrig.py to draw all the UI elements.

These UI elements are in the sidebar under the CloudRig panel, and contain settings like custom properties, IK/FK switching, parent switching, snapping and baking.

</details>


<details>
<summary> metarigs </summary>
The `__init__.py` here implements the metarigs and component samples UI lists that appear in the Object->Add->Armature UI. Metarigs and Samples are technically the same thing, and both are loaded from MetaRigs.blend.

</details>


<details>
<summary> operators </summary>
Operators to help with authoring metarigs and speed up workflow.

- better_bone_extrude: Binds to the E key, overwriting Blender's default bone extrude operator. Extruding a bone named "Bone1" will result in a bone named "Bone2" rather than "Bone1.001".
- bone_selection_pie_ops: Operators for the bone selection pie menu, bound to Alt+D in armature pose/edit/weight paint modes.
- bone_selection_pie_ui: UI elements for said pie menu.
- copy_mirror_components: Operators for copying and mirroring metarig component parameters. Found in the CloudRig header menu in the 3D View.
- edit_widget: An operator bound to Ctrl+Alt+E to toggle edit mode on a bone's widget.
- flatten_chain: Flatten a bone chain along a plane, useful for straightening limbs for good IK behaviour. Drawn in the IK Chain component's UI.
- pie_bone_parenting: Pie menu bound to the P key for bone parenting, even in pose mode.
- pie_bone_specials: Pie menu bound to the X key for deletion and symmetry in armature pose/edit modes.
- symmetrize: The improved symmetrize functionality found in the above pie menu.
- toggle_action_constraints: Useful in Action-based rigging workflow, button is drawn in the Action editor header.
- toggle_metarig: Toggle between metarig and generated rig (visibility, object mode, bone collections, bone selection). Default shortcut: Shift+T.

</details>


<details>
<summary> rig_component_features </summary>

#### widgets/__init__.py
Like metarigs, most widgets are appended from a Widgets.blend file. This is used

#### bone_gizmos.py
Bone Gizmos is an experimental/abandoned addon of mine, and this module allows components to interface with this addon.

#### animation.py
Functions used by [cloud_fk_chain](Cloudrig-Types#cloud_fk_chain) and the [Generate Test Animation](Generator-Parameters) feature.

#### bone_set.py
CloudRig's bone organization system that takes care of creating sets of parameters to customize the collection and color assignment of bones. All BoneInfo instances created during generation should be created with my_bone_set.new(), to ensure that every bone can be organized by the rigger.

#### bone.py
Abstraction layer for bones, constraints and drivers, which are used all over CloudRig. These avoid a lot of headaches that come with interacting with real Blender data directly (in exchange for other, smaller headaches!).

Existing bones are loaded into BoneInfo instances in `load_metarig_bone_infos()`, which are then turned back into real bones in `write_edit_data()` and `write_pose_data()`.

#### mechanism.py
Houses the CloudMechanismMixin mix-in class which is inherited by all component types and provides generic utilities to manipulate bones, constraints and drivers.

#### custom_props.py
Implements the shared parameters of all component types relating to storing and displaying custom properties in the rig UI.

#### object.py
Houses CloudObjectUtilitiesMixin which is inherited by all component types and provides generic utilities to control actual Blender objects, such as making things visible, assigning things to collections, transform locks, etc.

#### parent_switching.py
UI for the [Parent Switching shared parameters](CloudRig-Types#shared-parameters). This just means creating certain UI data, drivers and constraints, which cloudrig.py will use for displaying parent switching sliders and operators. Those operators are implemented in cloudrig.py.

#### ui.py
Houses CloudUIMixin which is inherited by all component types and provides utilities for drawing the UI of parameters as well as storing UI data. The `add_ui_data()` function is used to store data in the rig's `ui_data` custom property, which will be later read by cloudrig.py in `draw_rig_settings()` to draw the rig's UI.

</details>


<details>
<summary> rig_components </summary>
All the [component types](CloudRig-Types) in the feature set.
Also has cloud_template which is the base I use when starting a new component type.

All component types inherit from cloud_base.py/Component_Base.
Entry points are of course `__init__()` and `create_bone_infos()`.

</details>


<details>
<summary> ui </summary>
- actions_ui: UI for the Action system.
- cloudrig_dropdown_menu: The "CloudRig" editor header menu in armature pose/edit mode.
- cloudrig_main_panel: The "CloudRig" panel and "Generation" sub-panel in the Properties editor on armatures.
- rig_component_list: The "Component List" sub-panel in the Properties->Armature editor.
- rig_component_subpanels: The parameter sub-panels in the Properties->Bone editor.
- rig_component_ui: The parameter main panel in the Properties->Bone editor.

</details>


<details>
<summary> utils </summary>

- curve.py: Utility functions used by curve-based components, particularly to help with curve symmetry.
- lattice.py: Some utilities used by cloud_lattice, taken from my Lattice Magic addon.
- maths.py: Any pure math, even if it is only used in one place, goes here. That means this module should never import anything from any other part of CloudRig.
- misc.py: Code that hasn't been organized yet. Ideally this module shouldn't exist, since it's not clear what is in it.
- post_gen.py: Code that could be useful to run from post-generation scripts. Not actually used anywhere in the add-on.

</details>

<details>
<summary> Repo root </summary>

#### __init__.py
Where the add-on registers itself into Blender's RNA system. I implement a pattern where each sub-folder's __init__.py should import its contents and put them in a "modules" list. The listed modules will be traversed recursively here, and any registerable classes they might store in a "registry" list will be registered, and their register() and unregister() functions will be called as appropriate.

#### manual.py
Makes sure right clicking on CloudRig properties and then clicking on Open Manual goes to the relevant page on this wiki.

#### versioning.py
Metarig versioning. 

All metarigs store a version number, and this module adds an app handler that runs whenever a new blend file is loaded, to check for metarigs whose version is lower than the current one. If it finds any, it will automatically do its best to upgrade the metarig's [component types and parameters](CloudRig-Types) to the latest correct names and values.

For example, the cloud_copy and cloud_tweak bone types used to be a single component type with an enum to switch between the two behaviours. When that split was implemented, the old enum value is still accessible, and is used to assign the new correct component type accordingly.

</details>

# Contribute
This project has grown large enough that external contributors would be fairly welcome. Just get in contact with me before you start coding.

### Code Quality
Ideally every file should have fully type annotated functions with clear and verbose docstrings. If you'd like to understand a part of the code but can't, feel free to let me know, as that would give me a motivation boost to improve the code quality in a specific area.

### Conventions
Suggestions for more conventions are welcome, if you find things that could be more consistent. But what's already written down here is unlikely to change.

- All component types start with `cloud_`
- Always use the Troubleshooting module to warn riggers about potential issues, big or small.
- Functions should be defined top to bottom in roughly the order they run.
- Functions that override an inherited one should specify in the docstring what module they are overriding the function from.
- Typing is appreciated. PEP 585 is preferred to the older PEP 484.
- Always be conscious of whether `bpy.data.objects.get()` should receive a `(string, library)` tuple or not.
- Code is formatted with Black.

### Adding a new component type or parameter
If you have an idea for a new component type or parameter, that is welcome. Here are some notes:
- Open an Issue to discuss the design first.
- Consider if the functionality should just be just a parameter on an existing component type or an entire new type on its own. Usually both are possible, but when one functionality requires multiple parameters that don't make sense on any of the current component types, that's when it should be split out into a new component type.
- No redundant or double functionality. If the new functionality is very similar to that of another component type, let's try to find a way to make them share the relevant code. Maybe that means putting in extra work to also make this functionality work with a bunch of other component types, and a new parameter can be added all the way up in cloud_base.
- Provide clear and convincing explanation of why this functionality is useful, ideally showing a character where the functionality was used where no other solution would've worked as well.
- If I can press it, it should do something. If it doesn't do anything, don't let me press it. (see forced_params dictionary in some component classes)

To get started, check out cloud_template.py. This is what I start with when I start implementing a new component type. That is to say, it's the most basic skeleton code of a CloudRig component type. Note that it inherits a lot of shared functionality from Component_Base.

- Implement all the parameters and code. There is a regular __init__() and then the generator will call `create_bone_infos()` as your entry point.
- Add a component sample in MetaRigs.blend, named according to the convention you'll find in there.
- Add documentation in the wiki's Cloudrig-Types page, again sticking to the conventions established there.
