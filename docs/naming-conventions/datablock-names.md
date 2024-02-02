# Datablock names

Naming conventions for datablocks are important for library override stability, organization clarity, and the ability to easily create fully local and editable demo files at the end of production.

These conventions aren't needed for things you make just for yourself, like sketches, backups, etc. But make sure that such data can always be deleted without affecting render results.

## Case & Separators
We use lower_underscore_case, with all caps prefixes and suffixes.

`_` : Used instead of spacebar, has no special significance.
`-` : Separate the prefix and parts of the base name from each other. Can be used to indicate a hierarchy.  
`.` : Separates suffixes for symmetry sides, eg. `GEO-esprite-eye.L`, as well as asset variants, see below.  

## Namespace Identifier

All datablocks in a production must have a unique name. To achieve this, each asset's name should be present in all datablock names of that asset. This should be enforced by add-ons wherever possible. For example, the character "Elder Sprite" would have the unique identifier `elder_sprite`.
If the length is an annoyance, a shortened identifier can also be used, as long as it's still unique, eg. `esprite`.

For non-asset datablocks like poselib poses and shared node groups, use the file name.

The identifier can also have underscores and numbers in it, which may be the case for library assets. For example, if you have to name several similar trees, they can be `LI-tree_birch_001` and etc.

## Asset Hierarchy & Prefixes
Here's what an asset's collection hierarchy might look like:
![Collection Hierarchy Naming Example](/media/naming-conventions/collection_hierarchy_naming_example.png)

The root collection of assets should be an asset type prefix, and then the full name, eg. `CH-elder_sprite`, `LI-rock_large_013`

List of prefixes:
- `CH` : Character
- `PR` : Rigged Prop
- `LI` : Library/Environment Asset
- `SE` : Set
- `LG` : Light Rig
- `CA` : Camera Rig

The immediate sub-collections of the root collection should be named according to the Task Layers configured in our Asset Pipeline add-on. Collections nested beyond this only need to start with the namespace identifier, but can otherwise be named freely by the owner of the task layer.

## Object Prefixes
Object names (not just in Assets) must start with a prefix indicating their purpose:

- `LGT` : Light objects and mesh-lights, also shadow casters
- `ENV` : Matte paintings, sky-domes, fog volume objects
- `GEO` : Geometry, meshes, curves that contribute to the rendered appearance of an asset
- `RIG` : Armatures of an asset
- `GPL` : Grease pencil stroke objects (need to differentiate from GEO because can not be rendered on the farm)
- `WGT` : Bone shapes
- `HLP` : Empties and other helper objects that are not rendered
- `TMP` : Objects that should be replaced with final assets over the course of the production.

## Base Names
![Indicating Hierarchy in names](/media/naming-conventions/hierarchy_name_example.png)

- Use lower case and `_` instead of spacebar.
- `-` can be used to indicate a hierarchy among objects.
- Mesh & Shape Keys to be named same as the containing object. (Soon to be automated)
- `.00x` suffixes should be replaced with `_00x` to technically become part of the base name. This is enforced by the Asset Pipeline add-on.
- When there's too many objects to manually name, use **Batch Rename Datablocks Operator** to name all the objects, then replace the `.` in with an `_`. (This is important for safe Library Overrides.)

## Variants
Use `.` for indicating variants, which is when an asset has multiple states or versions in the production that need to be swapped between.
The variant indicator can be placed anywhere in the name hierarchy:
`GEO-wardrobe.burned-shelf-book` indicates that the whole wardrobe has a burned variant. Maybe there is a house fire in the film.
`GEO-wardrobe-shelf-book.burned` indicates that only the book is burned. Maybe a candle fell over in the film.

## Symmetry Suffixes
Use exactly `.L`/`.R` suffixes for objects that belong to one side and are symmetrical.
On the other hand, avoid using `.L`/`.R` when similar objects exist on each side of an asset but aren't meant to be symmetrical, and use a different side indicator if necessary, such as `_left`.

## Node Trees
Node Trees (aka Node Groups) in Blender are unfortunately all stored in one location, which is inconvenient when trying to browse them, which we frequently do. To remedy this, node groups should be prefixed with what type of node group they are.
```
`GN` : Geometry Nodes
`SH` : Shading Nodes
`CM` : Compositing Nodes
```

And as always, the namespace identifier must be included, eg. `GN-esprite-procedural_beard`.

## Temporary Art
Placeholder art should be prefixed with `TMP`, whether it is collections or objects in assets or shots.

## Actions

### Pose Library

Pose Library actions also need a namespace identifier. Other than that, stick to lowercase and underscores.

Examples:
```
rex-hand_fist
rex-hand_splayed
rex-face_happy
rex-face_surprised
rex-eyes_blink
rex-eyes_surprised
```

### Rig Actions
Rigs may use Actions for Action Constraint based control set-ups. Since these are datablocks and part of the character asset, they must include the namespace identifier.
Corrective Actions are ones which are meant to activate when two other actions activate. These should use the name of the two trigger actions, separated by a "+".

Examples: 
```
RIG-esprite-mouth_open
RIG-esprite-lips_wide
RIG-esprite-mouth_open+lips_wide
```

### Animations of Shots
Actions of shots/layout/cycles/samples should be named `ANI-{namespace_identifier}-{anim_name}-{version}`.
- `namespace_identifier`: Identifier of the asset being animated.
- `anim_name`: Name of the motion, usually the name of the file you're in. (Can be a shot, layout, re-usable thing like a walk cycle, etc.)
- `version`: Set by the animator as they iterate, in the format `v001`, `v002`, etc.

Examples:
```
ANI-esprite-060_scratch_layout-v001
ANI-esprite-110_0100_A-v001
ANI-rex-walk_cycle-v001
```

### Bone Names
The main goal when naming bones is to make the rig easy to learn and intuitive.
- Every bone name should be named properly (never `Bone.023`)
- Avoid ugly number suffixes
- Avoid unnecessary padding in numbers.
- Avoid tech info in artist-facing names.
- Avoid stacking several name prefixes.
- Avoid wasting the best names on mechanism bones.
- Start numbering at 1, not 0.
- Indicate symmetry with `.L`/`.R`.

Examples:
```
Bad: STR-TIP-Finger_04_003.L
Good: STR-Finger_Pinky_4.L

Bad: IK-MSTR-Wrist.L
Good: IK-Wrist.L
```

Some prefixes and their meaning:
- `IK` : Control body parts in Inverse Kinematics mode
- `FK` : Control body parts in Forward Kinematics mode
- `STR` : Squash and stretch body parts
- `ROOT` : Control a cohesive area of the rig (often detachable)
- `TGT` : Control the target of a Look-At rig set-up
- `P` : Parent of another control
