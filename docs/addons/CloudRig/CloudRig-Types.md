
# Overview

<img src="/media/addons/cloudrig/component_hierarchy.png">    
 
These are CloudRig's component types. Most component types are built on top of others, meaning they inherit each other's functionalities. The image above and the table of contents below shows this inheritance hierarchy.

- [Shared Parameters](#shared-parameters)
    - [Chain: Toon](#chain-toon)
        - [Chain: Face Grid](#chain-face-grid)
            - [Chain: Eyelid](#chain-eyelid)
        - [Chain: FK](#chain-fk)
            - [Chain: Physics](#chain-physics)
            - [Feather](#feather)
            - [Spine: IK/FK](#spine-ikfk)
            - [Spine: Squashy](#spine-squashy)
            - [Shoulder](#shoulder)
            - [Chain: IK](#chain-ik)
                - [Chain: Finger](#chain-finger)
                - [Limb: Generic](#limb-generic)
                    - [Limb: Biped Leg](#limb-biped-leg)
    - [Curve: With Hooks](#curve-with-hooks)
        - [Curve: Spline IK](#curve-spline-ik)
    - [Lattice](#lattice)
    - [Aim](#aim)
    - [Bone Copy](#bone-copy)
        - [Chain Intersection](#chain-intersection)
    - [Bone Tweak](#bone-tweak)

# Assigning Components
You can assign a component to a bone in the metarig. For chain components, the connected children will be part of the same component, as long as they aren't assigned a component of their own. You can assign components to bones in two places in the UI: 
- Properties -> Armature -> CloudRig -> Rig Components (Hit the + button to assign a component to the active bone.)
- Properties -> Bone -> CloudRig Component -> Component Type (Only appears when 'CloudRig' is enabled on the armature.)

<img src="/media/addons/cloudrig/assigning_components.png" width=800>  

# Component Samples
Each component type comes with a sample so you can get something up and running quickly and start playing around with it.  
You can add these in the 3D View via Add (Shift+A)->Armature->CloudRig Samples:  
<img src="/media/addons/cloudrig/add_sample.png" width=500>  

# Component Types
## Shared Parameters
All CloudRig component types share some basic functionality, like letting you choose a parent for the component's root, and even specify a parent switching set-up for it.


<details>
<summary> Details & Parameters </summary>

<img src="/media/addons/cloudrig/shared_parameters.png" width=600>

- #### Advanced Mode
    This is technically a user preference, but it relates to component parameters. Some component parameters are rarely necessary or only if you want to really fine tune stuff. So, these options are hidden until this option is enabled, to ease the new user experience.  
- #### [Constraint Relinking](Constraint-Relinking)
    On any component, you can add constraints to the metarig bones. On generation, these constraints will be moved to the generated bones that make the most sense for a given component type. This is just to allow you to add some constraints when needed, without using Bone Tweak components.  
    For example, you can add Copy Rotation constraints to the metarig bones of an FK Chain component. That constraint can target the generated rig's bones, even though it's a different armature object. During generation, that constraint will be moved to the corresponding FK control.

- #### Root Parent
    If specified, parent the root of this component to the chosen bone. You're choosing from the generated rig's bones here.  
    If the chosen bone is a bendy bone, additional options appear:
        - Use an Armature constraint instead of normal parenting: This constraint takes bendy bone curvature into account, but it also means the parenting transforms will affect the bone's local matrix. If you want to use the bone's local transformations to drive something, you essentially won't be able to.
        - Create parent helper bone: This fixes the local matrix issue by creating a parent helper bone for the aforementioned Armature constraint.
- #### Parent Switching
    This option lets you create a parent switcher by entering the UI names of each parent on the left side, and the corresponding parent bone on the right side. The bone names are chosen from the generated rig.  
    The chosen bones will be the available parents for this component's root bone, and a selector will be added to the rig UI.  
    Different component types may implement parent switching differently. The specific behaviour is explained underneath the checkbox when it is enabled.  
- #### Custom Property Storage
    This setting will appear for components that need to create custom properties. Custom Properties are used for things like IK/FK switching.  
    - "Default": A bone named "Properties" will be created to store custom properties.  
    - "Custom": If you want to store the custom properties on an arbitrary bone, this option lets you select one. The selected bone has to be higher in the metarig hierarchy than this component, else you'll get a warning.
    - "Generated": Component types implement their own behaviours for creating a custom property storage bone in a place that makes most sense for that component type. For example, the Biped Leg component will put the properties bone behind the foot control.

- #### Bone Sets
    Components organize their bones using parameters called Bone Sets. These live under the Bone Organization sub-panel, which is only visible when Advanced Mode is enabled. Bone Sets are further explained on the [Organizing Bones](Organizing-Bones#organizing-bones) page.

</details>


## Chain: Toon
The most basic bone chain, consisting of independent controls connected by stretchy bendy bones. Can be useful for long, soft props, like a scarf on the floor, or soft circular things like a car tire.

Scaling the stretch controls uniformally gives the connected bendy bones more volume. Scaling them only on their local Y axis affects only the curvature of the chain.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/cloud_chain_toon.gif" width=500>  
<img src="/media/addons/cloudrig/cloud_chain_veejay.gif" width=500> 

- #### Stretch Segments
    Number of sub-controls for each bone in the meta chain.
- #### Tip Control
    Whether there should be a control at the tip of this chain.

- #### B-Bone Density
    B-Bone segments will be distributed equally along the chain. As long as this value is >0, each bone will have at least 2 b-bone segments. A high density will not have a severe impact on performance.
- #### Sharp Sections
    Bendy bones will not affect the curvature of their neighbours, unless their shared stretch control is scaled up on its local Y axis.
- #### Smooth Spline
    Bendy bones will have a wider effect on the curvature of their neighbours, to easily get smoother curves. Works best when Deform Segments is 1, but that is not a requirement. Works fine with Sharp Sections, but it will only take effect once a stretch control is scaled up along its local Y axis.
- #### Preserve Volume
    When enabled, deform bones will become fatter when squashed, and slimmer when stretched.
- #### Create Shape Key Helpers
    Create helper bones that can be used to read the rotational difference between deform bones. Useful for driving corrective shape keys. These helpers will be prefixed "SKH" for "Shape Key Helper".
- #### Create Deform Controls
    Create controls that allow you to translate and scale deform bones by disconnecting them from their neighbours.

</details>


## Chain: Face Grid
Extends the functionality of the Toon Chain with functionality to create intersection controls in locations where multiple chains intersect. Can be used to create a grid of bendy bone chains. Can be useful for faces, but I personally no longer recommend this workflow. As cool as it looks, it's difficult and unintuitive to control small areas, and difficult to set up.


<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/cloud_face_grid.gif" width=500>

- #### Merge Controls
    Create controls for points where multiple Face Grid chains intersect. If a [Chain Intersection](#chain-intersection) component is found at that intersection, that will be used instead of generating one from scratch.

</details>


## Chain: Eyelid
This component should be parented to an Aim component, presumed to be an eyeball. The rotation of that Aim component (eyeball) will affect this eyelid component. The strength of this effect can be adjusted by animators in the rig UI under a Face Settings panel.
This can give a decent fleshy eyelid set-up very quickly, but for a main character, I advise instead to create Action Set-Ups to connect the eyeball's up-down and left-right rotations to hand-crafted eyelid poses. This will allow you to hand craft the way the eyelids react to the eyes in great detail.


## Chain: FK
Extends the functionality of the Toon Chain. In addition to stretch controls, this also creates FK controls, which are parented to each other in a hierarchy. Useful for fingers, tails, hair, appendages, a vast array of things.

<details>
<summary> Parameters </summary>

- #### Create Root
    Create a root control for this rig component. This is required for the Hinge Toggle.
- #### Hinge
    Set up a hinge toggle. This will add an option to the rig UI. When FK Hinge is enabled, the FK chain doesn't inherit rotation from its parent.
- #### Position Along Bone
    How far (0-1) the FK control should be along the length of the bones. A value of 0.5 can make it easier to create smooth curves.
- #### Inherit Scale
    Sets the scale inheritance type for FK controls.
- #### Rotation Mode
    Rotation Mode for the FK controls.
- #### Duplicate First FK
    Create an extra parent control for the first FK control.
- #### Display FK in Center
    Display the FK controls in the center of the bone rather than at the head of the bone. Only affects display, no functional difference. Purely up to preference.


<img src="/media/addons/cloudrig/test_animation.gif" width=500>  

- #### Test Animation
    This panel will only show when the ["Generate Action" Generator Parameter](Generator-Parameters) is enabled.
    When this option is enabled, this component will add keyframes into the generated action which can be used to test character deformations.
- #### Rotation Range
    The negative and positive rotation amount in degrees to use for the aforementioned test animation.
- #### Rotation Axes
    Which axes you want tested in the test animation. For example for fingers, you probably only need one axis.

</details>


## Chain: Physics
Extends the functionality of the FK Chain component with a physics setup that utilizes Blender's built-in cloth simulation (for better or worse). The FK controls are constrained to a cloth mesh, and can't be posed. However, optional Physics controls can be created to deform the cloth mesh. The simulation is applied on top of this deformation. This can be useful for achieving a video-gamey physics sim for things like a character's ponytail or any other appendage.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/physics_chain.gif" width=500>  

- #### Cloth Object
    The cloth object that the FK chain will be constrained to with Damped Track constraints. The object should have vertex groups named "PSX-<FK control name>". You can leave this unspecified at first and a simple object will be generated for you, which you can later modify.
- #### Force Re-Generate
    If you intend to modify the cloth mesh, make sure to disable this option since otherwise re-generating the rig will also re-generate the cloth mesh. Enabling this is useful however when you are still iterating on the shape of the bone chain, in which case you want to re-generate the mesh every time.
- #### Pin Falloff
    Type of the vertex weight falloff curve for the chain of vertices making up the cloth mesh.
- #### Pin Falloff Offset
    Stretch factor for the pin falloff curve. Increasing this will make the cloth more stiff.
- #### Create Physics Controls
    When enabled, this will create a PSX control chain which lets you control the cloth simulation. This will only work on pinned vertices - vertices with a pin weight of 0 will only be affected by the cloth simulation, while a weight of 1 means being fully affected by the armature.
</details>


## Feather
Some small tweaks to the FK Chain component to work a bit better for an individual feather of a bird. Requires a single bone.  

This component type comes with no additional parameters.

## Spine: IK/FK
Builds on the FK Chain component with additional option for creating an IK-like set-up for a spine.

<details>
<summary> Parameters </summary>

- #### Create IK Setup
    Create an IK-like setup inspired by [BlenRig](https://gitlab.com/jpbouza/BlenRig). This will also add an IK/FK and IK Stretch setting to the rig UI.
- #### Duplicate Controls
    Make duplicates of the main spine controls.
- #### World-Align Controls
    Align the torso and hips controls fully with the world.

</details>


## Shoulder
A very simple extension of the FK Chain component, essentially just changes the bone shape.

<details>
<summary> Parameters </summary>
- #### Up Axis
    Rotate the bone shape to align with this axis of the bone.
</details>


## Chain: IK
Extends the FK Chain component with IK functionality. The default direction of the pole target is determined based on the curvature of the bone chain. This requires at least 2 bones.
This rig adds IK/FK switching and snapping and IK Stretch settings to the rig UI.

<details>
<summary> Parameters </summary>

- #### Create IK Pole
    Whether the IK constraint should use a pole target control, and whether such bone should even be created.
- #### IK At Tail
    Put the IK control at the tail of the last bone, rather than at its head.
- #### World-Aligned IK Master
    Align the IK master control with the nearest world axis. Not recommended for arms when your resting pose is an A-pose.
- #### Flatten Bone Chain
    Although not a parameter, this button will flatten your chain along a plane with as little changes as possible, to ensure predictable IK behaviour.

</details>


## Chain: Finger
Changes the IK Chain component with some specific behaviours useful for fingers. The fingers should bend in their local +X axis.
The IK settings of finger rigs are organized into a sub-sub-panel in the rig UI, because there are usually a lot of fingers, resulting in a lot of UI sliders.

<details>
<summary> Parameters </summary>

- #### Create IK Switch Control
    Instead of using a UI slider for FK/IK switching, create a control in the viewport for the switching.
    Whether the IK constraint should use a pole target control, and whether such bone should even be created.

</details>



## Limb: Generic
Extends the IK Chain component with cartoony rubber-hose functionality. This requires a chain of exactly 3 bones.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/rubber_hose.gif" width=500>

- #### Duplicate IK Master
    Create an extra child control for the IK master.
- #### Rubber Hose
    This option is only available when Smooth Chain is enabled and Deform Segments is greater than 1.
    When this option is enabled, a slider is added to a rig UI which lets you have an automatic cartoony rubber hose limb effect.
- #### With Control
    Instead of a UI slider, create a control bone that can be scaled to control the strength of the automatic rubber hose effect.
- #### Type
    There are two ways to achieve the rubber hose deformation. One results in lengthening the limbs, while the other results in shortening them. It's a question of which style you prefer.

</details>


## Limb: Biped Leg
Extends the functionality of the Generic Limb component with footroll. This requires a chain of exactly 4 bones.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/cloud_leg.gif" width=500>  

- #### Foot Roll
    Whether to create a foot roll setup.
- #### Heel Pivot
    If you are using foot roll, you can specify a bone whose location will be used as the pivot point for when the foot is rolled backwards.

</details>


## Curve: With Hooks
Create hook controls for an existing Curve object. Multiple splines within a single curve object are supported. Each spline will have its own root control.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/curve.gif" width=500>  

- #### Curve
    The target curve object to be hooked up to bone controls. Must be chosen!
- #### Custom Name
    String to use to name the bones. If not specified, use the base bone's name.
- #### Inherit Scale
    Scale inheritance setting of the curve hook and spline root controls.
- #### X Axis Symmetry
    Controls will be named with .L/.R suffixes based on their X position. A curve object that is symmetrical around its own X 0 point is expected, otherwise results may be unexpected.
- #### Controls for Handles
    For every curve point hook control, create two children that separately control the handles of that curve point.
- #### Rotatable Handles
    Set up the handle controls in a way where they can be rotated. Note that they will still allow translation, but if you translate them, rotating them afterwards will be unpredictable.
- #### Separate Radius Control
    Instead of using the hook control's size to control the curve point's radius, create a separate child control to do so.
    
</details>


## Curve: Spline IK
Extends the functionality of the Curve With Hooks component, where instead of adding bones to control an existing curve object, it creates a new curve object along a chain of bones and creates a Spline IK constraint setup. The curve is always re-generated along with the rig. The curve parameter is grayed out, since it will be created for you. You cannot specify a custom curve. Instead, if you want to change the shape of distribution of the curve, simply make those changes in the bone chain. This can contain more information.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/spline_ik.gif" width=500>  

- #### Curve Handle Length
    A multiplier on curve handle length. 1.0 means the curve handle is long enough to reach the neighbour curve point.
- #### Deform Setup
    How this component should behave with Armature modifiers:
    - None: Don't create deformation bones. Then this component cannot be used with Armature modifiers.
    - Preserve: Preserve the Deform checkbox of the bones as set in the metarig.
    - Create: Create DEF- bones that are a separate chain with the Deform checkbox enabled.
- #### Subdivide Bones
    When Deform Setup is set to Create, this value defines how many deforming bones to generate along each original bone in the metarig. More bones results in a smoother curvature. However, the Spline IK constraint only supports a chain of up to 255 bones.
- #### Match Controls to Bones
    When enabled, control bones will be created at the locations of the meta chain's bones. When disabled, control bones will be distributed an equal distance from each other along the chain.
- #### Number of Hooks
    When the above setting is disabled, this specifies how many controls should be placed along the chain.
    
</details>


## Lattice
Creates a lattice with a root and a hook control. The hook control deforms the inside of the lattice using a spherical vertex group that gets generated. You can manually add Lattice modifiers to objects that you want to be deformed by the created lattice. This is a very performant and very flexible way to slightly nudge or bulge things. Every rig should have a few of these lattice set-ups scattered around, particularly clothing and faces. You never know when it might come in handy, but it often does.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/lattice.gif" width=500>  

- #### Lattice
    The lattice object that will be generated. If empty, one will be created.
- #### Regenerate
    Whether the lattice should be re-generated from scratch or not. Disable this if you want to customize the lattice, otherwise any changes beside the object's name, will be lost when you re-generate the rig.
    
</details>


## Aim
This rig creates an aim control for a single bone. Can be useful for cameras, eyes, or anything that needs to aim at a target.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/aim.gif" width=500>  

- #### Aim Group
    Aim rigs belonging to the same Aim Group will have a shared master control generated for them.
- #### Target Distance
    Distance of the aim target from the base bone. This value is not in Blender units, but is a value relative to the scale of the rig.
- #### Flatten X
    Discard the X component of the eye vector when placing the target control. Useful for eyes that have significant default rotation. This can result in the eye becoming cross-eyed in the default pose, but it prevents the eye targets from crossing each other or being too far from each other.
- #### Create Deform
    Create a deform bone for this rig. May not be always needed, for example if you just want to object-parent something to the aim rig, like a camera.
- #### Create Root
    Create a root bone for this rig.
- #### Create Sub-Control
    Create a secondary control and deform bone attached to the aim control. Useful for fake eye highlights.

</details>


## Bone Copy
This component type lets you copy a connected chain of bones over to the generated rig. Often used just to copy a single bone. Useful for face controls or any other arbitrary control you want to add.

Constraints will be [relinked](Constraint-Relinking) to the copied bone.

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/cloud_bone_parameters.png" width=500>  

- #### Create Custom Pivot
    Create a parent control whose local translation is not propagated to the main control, but its rotation and scale are.
- #### Create Deform Bone
    Create a second bone with the DEF- prefix and the Deform property enabled, so you can use it as a deform bone.
- #### Ensure Free Transformation
    If this bone has any constraints, move them to a parent bone prefixed with "CON", unless the constraint name starts with "KEEP".

- #### Custom Properties: UI Sub-panel
    Choose which sub-panel the custom properties should be displayed in. If empty, the properties won't appear in the rig UI.
- #### Custom Properties: UI Label
    Choose which label the custom properties should be displayed under. If empty, the properties will display at the top of the subpanel.

</details>


## Chain Intersection
This component is an extension of Bone Copy with a special interaction with Face Grid components.

<details>
<summary> Details </summary>

When a Chain Intersection is placed at the same location as one or more Face Grid bones, the Chain Intersection will be used as the intersection control, rather than automatically creating that intersection control.
This can be useful because the automatically generated intersection controls have unwieldy bone names, and their orientation may also need to be customized.

<img src="/media/addons/cloudrig/cloud_chain_anchor.gif" width=500>

This component has no additional parameters.

</details>

## Bone Tweak
This component type lets you tweak aspects of a single bone that is expected to exist in the generated rig. 

<details>
<summary> Parameters </summary>

<img src="/media/addons/cloudrig/cloud_tweak_parameters.png" width=500>  

- #### Additive Constraints
    If true, the constraints on this bone will be added on top of the target bone's already existing constraints, and then [relinked](Constraint-Relinking). Otherwise, the original constraints will be overwritten.
- #### Tweak Parameters
    The bone's properties are split into these categories:
    - Transforms
    - Locks
    - Rotation Mode
    - Bone Shape
    - Color Palette
    - Collections
    - Custom Properties
    - IK Settings
    - B-Bone Settings
    Each of these can be chosen to be copied over to the target bone or not. For example if you just want to add some extra constraints to a bone, you probably don't want to overwrite its transforms, bone shape, etc, so you would leave all of those unticked, and they will remain untouched.

</details>
