# Constraint Relinking

When working with CloudRig, you generally don't have to define individual constraints yourself - after all, the whole point of [rig components](cloudrig-types) is to generate the bones and constraints for you.

But unique characters have unique needs, where you may want to **add additional constraints** on specific bones that were generated.
The easiest way to do this is by relying on Constraint Relinking, which is what CloudRig will do with constraints found on the metarig's bones.
- If you simply add a constraint to the metarig bone of an [FK Chain](cloudrig-types#chain-fk) component, that constraint will be moved to the corresponding FK control of the generated rig. You can set the constraint's target object to the generated rig, this won't cause any problems. Drivers on constraint properties will be transferred too.
- If you want the constraint to be moved to a bone with a different prefix than `FK`, you can add that prefix to the constraint name. For example, `IK-Limit Distance` will be moved to the IK bone (the rest of the bone name has to be the same as the metarig bone).
- If you want to move a constraint to the final STR control of a toon chain, you can prefix the constraint name with `TAIL-`.
- If you want to add a constraint to an arbitrary bone in the generated rig that doesn't have an obvious corresponding bone in the metarig, this system is not applicable, and you should instead use the [Tweak Bone](cloudrig-types#tweak-bone) component, or the [post-generation script](generator-parameters#post-generation-script).
- If you don't want to reference the generated rig in the constraint, you can instead also specify the constraint's target after an `@` symbol. For example, `TAIL-Copy Rotation@MyControlBone` will result in this constraint being moved to the last STR bone of a Toon Chain, and its target to be set to "MyControlBone" in the generated rig. In this case, the metarig constraint doesn't need a target to be specified at all. There is no strong reason to do this, it's just up to your preference.

Here is a video showing some of these behaviours.
<video src="/media/addons/cloudrig/constraint_relinking.mp4" controls></video>