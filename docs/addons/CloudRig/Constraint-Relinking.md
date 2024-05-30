When working with CloudRig, you generally don't have to define individual constraints yourself - after all, the whole point of rig components is to generate the bones and constraints for you.  

But unique characters have unique needs, where you may want to **add additional constraints** on specific bones that were generated.
You could do this using the [Tweak Bone]("CloudRig-Types#bone-tweak") component, but that can quickly make your metarig messy with the addition of many bones.

Constraint Relinking gives you a shortcut for moving constraints from the metarig bones to the generated controls. In order to make this as useful and efficient as possible, some specific behaviours are implemented:  

### Component Types
Different component types will move constraints to different generated bones.
For example, the [Toon Chain]("CloudRig-Types#chain-toon") component will move constraints to its STR controls, while the [FK Chain]("CloudRig-Types#chain-fk") component will move them to the FK controls.

### Constraint target
Most constraints require a target bone to function. There are two ways to specify this:
- Simply select your generated rig and your target bone as normal. This is the recommended method.
- Alternatively, if you don't want your metarig to be constrained to your generated rig, you can specify the constraint target bone in the constraint name using an "@" symbol. The Armature constraint supports multiple subtargets, eg. a constraint named "Armature@DEF-Head@DEF-Jaw" will fill in those two bone names to the first and second subtarget of the constraint.