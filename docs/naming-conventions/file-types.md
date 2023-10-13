# File Naming

## Characters

**Location:** `{project root}/pro/assets/char/{char subfolder}/{type}-{char name}-{task}.blend`

A character asset is a collection which contains shaded geometry, rigs, rigging objects such as mesh deformers and lattices. All of these are needed to give animators control over their movement and make up the final rendered representation of the character in the movie

## Props

**Location:** `{project root}/pro/assets/prop/{prop subfolder}/{prop name}.blend`

A prop in real life is a rigged, animatable object which characters interact with or can be constrained to. An environment library asset can sometimes be turned into a prop (e.g. Autumn picks up a branch from the ground and breaks it into pieces).


## Sets

**Location:** `{project root}/pro/assets/set/{set subfolder}/{set name}.blend`

Sets are more tricky to define, since they can differ even on a shot level. In practice they are formed by a ground plane and dressed with environment assets. They can also contain individually created assets (*Spring* example: `riverbed.blend` contained two non-library trees which were modelled and shaded uniquely in this set). Sets can be connected together to build a larger world if necessary. Sets are contained in a main collection which has sub-collections for visibility management)

## Shots

**Location:** `{project root}/pro/**/**shots**/**{sequence number}**/**{shot identifier}/{shot identifier}.{task identifier}.blend`

## Textures and maps

**Location:** 

- `{project root}/pro/assets/maps/` for general textures which are used across the entire project
- `{asset folder}/maps/` for specific textures related to an asset



Example: `prop-dresser_wood.faded-modeling.png`

- As for all other files, format the entire name in lowercase, separated by `_` instead of spaces.
- Textures which are specific to a prop should include the name of the prop and THEN the name (if it's a label, or tex type such as metal or wood e.g.)
- If there's more than one type, Textures should also include the type (col, bump, nor, disp, spec) LAST in the filename (separated by a dot)
- make sure to clean up texture file names coming from the Blender Cloud according to these conventions. Sometimes there can be a .png.png at the end or files can have an uppercase first letter.