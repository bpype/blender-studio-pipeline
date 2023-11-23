# Datablock names

Naming objects in a Blender production can be quite non-trivial when trying to achieve stability, clarity, and the ability to easily make shot files fully local at the end of production, to create fully interactive demo files that can be shared with the world.

## Separators
We try keep their meaning consistent across conventions:
`-` : Separates prefixes (including the Namespace Identifier) from each other and from the rest of the name, eg. `GEO-esprite-head`. Also should be used for naming objects in a hierarchical way when possible, see "Indicating a hierarchy" below.
`.` : Separates suffixes for symmetry sides, eg. `GEO-esprite-eye.L`, as well as asset variants, see below.
`_` : Used to separate parts of the base name, eg. `wooden_wardrobe_032`. The base name of an ID never has any technical significance.

## Namespace Identifier

All datablocks across the entire production must have a unique name. To faciliate this, each asset's name, or a shortened version of it, should be present in all datablock names of that asset. This should be enforced by add-ons wherever possible. For example, the character "Elder Sprite" might have a full-length unique identifier of `elder_sprite`, along with an optional shortened (but still unique) version, eg. `esprite`. You should use the short version most of the time, eg. `GEO-esprite-head`, but the longer version when the name doesn't have a lot of other information, eg. the asset's root collection (`CH-elder_sprite`) or the rig object (`RIG-elder_sprite`).

This also applies to datablocks which are not part of an asset, for example pose library poses and shared node groups that get linked into assets. Their namespace identifier should simply be the name of the .blend file that they're in, or a shortened version of it.

This identifier will be present among the prefixes in the names of datablocks, to make sure all names are unique, not just in a single file, but across the whole production. This is necessary because Blender's Library Override system relies on making local copies of linked object hierarchies, meaning all assets need to be able to exist in the same namespace without name collisions.

The identifier can also have underscores and numbers in it, which may be the case for library assets, eg. `LI-tree_birch_001`.

## Asset Collection Hierarchy

We use prefixes for the root collections (and only the root) of assets to help distinguish different types of assets in the Outliner of a complex shot file. The name of the asset itself should be lowercase.

- `CH` : Character
- `PR` : Rigged Prop
- `LI` : Library/Environment Asset
- `SE` : Set
- `LG` : Light Rig
- `CA`: Camera Rig

Example root collection names: `CH-elder_sprite`, `LI-rock_large_013`

Note that there's no technical distinction between different types of assets. This is purely for organizational purposes and comfort.

The immediate sub-collections of the root collection should be named according to the Task Layers configured in our Asset Pipeline add-on, but this is not strictly required. Task Layers are the different data layers that make up an asset, such as Modeling, Rigging, and Shading. Collections nested beyond this can be named freely, as long as they still start with the namespace identifier.

So, here's what an asset's collection hierarchy might look like:
![Collection Hierarchy Naming Example](/media/naming-conventions/collection_hierarchy_naming_example.png)


## Name Prefixes
All Object names (not just in Assets) must start with a prefix describing the object's purpose:

- `LGT` : Light objects and mesh-lights, also shadow casters
- `ENV` : Matte paintings, sky-domes, fog volume objects
- `GEO` : Geometry, meshes, curves that contribute to the rendered appearance of an asset
- `RIG` : Armatures of an asset
- `GPL` : Grease pencil stroke objects (need to differentiate from GEO because can not be rendered on the farm)
- `WGT` : Bone shapes
- `HLP` : Empties and other helper objects that are not rendered
- `TMP` : Any object used in pre-viz that should be replaced with final assets over the course of the production.

All local datablocks of an asset (Object, Mesh, Material, Action, etc.) must also include either the asset's shortened or full name. Eg., `RIG-elder_sprite` or `GEO-esprite-eye.L`. This is enforced by the Asset Pipeline add-on.

## Base Names
- Object Data and Shape Keys should be named the same as the containing Object. This is automated by the Asset Pipeline add-on.
- Words in all base names should be lower-case and separated by `_`.
- All datablock names must not end with a `.00x` suffix. This is enforced by the Asset Pipeline add-on.
    - When there's too many objects to manually name, like when building a house out of a hundred wooden plank objects, the **Batch Rename Datablocks Operator** should be used to give groups of objects the same name. Then replace the `.` in the `.00x` suffixes with an `_` instead, so `GEO-house-wooden_plank.023` becomes `GEO-house-wooden_plank_023`, making the number a part of the base name for the purposes of Library Overrides and duplication.
    - This makes it so that when an asset is duplicated in a shot, every object in the same copy of the asset will have the same number suffix. The first copy will have no suffix, the second copy will have .001, etc. Without this step, this object would instead end up getting named `GEO-house-wooden_plank.024`, which would mean the suffix number has no correlation with which overridden copy of the asset this object belongs to. This could break Library Overrides.

## Indicating Hierarchy
For complex assets, try to use dashes to indicate a nested hierarchy of objects, eg:
![Indicating Hierarchy in names](/media/naming-conventions/hierarchy_name_example.png)


## Indicating Asset Variants
The `.` is also used for indicating asset variants, which is when an asset has multiple states or versions in the production.
The variant indicator can be placed anywhere in the name hierarchy:
`GEO-wardrobe.burned-shelf-book` indicates that the whole wardrobe has a burned variant. Perhaps there was a house fire in the film.
`GEO-wardrobe-shelf-book.burned` indicates that only the book is burned, perhaps because a candle fell over in the film.


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
Actions created for shots should be named `ANI-{namespace_identifier}-{scene_name}-{version}`

Examples:
```
ANI-esprite-060_scratch_layout-v001
ANI-esprite-110_0100_A-v001
ANI-rex-140_0020_A-v001
```

### Bone Names
Making rigs as easy to learn and work with as possible is the most important thing when naming bones.
Every bone name should be named properly (never `Bone.023`), avoid ugly number suffixes, and avoid unnecessary padding in numbers.
Controls that are exposed to animators should ideally have max one prefix, with an intuitive acronym.
Examples:
```
Bad: STR-TIP-Finger_04_003.L
Good: STR-Finger_Pinky_4.L
```

Numbering should start from 1, but if a bone gets inserted at the start of the chain, it's better to just number it 0 rather than change all the pre-existing bones' names, to not break any existing animations.

Symmetry sides should be indicated by `.L`/`.R`.

Other prefixes and their meaning:
- `IK` : Control body parts in Inverse Kinematics mode
- `FK` : Control body parts in Forward Kinematics mode
- `STR` : Squash and stretch body parts
- `ROOT` : Control a cohesive area of the rig (often detachable)
- `TGT` : Control the target of a Look-At rig set-up
- `P` : Parent of another control