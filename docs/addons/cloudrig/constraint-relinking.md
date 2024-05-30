# Constraint Relinking

When working with CloudRig, you generally don't have to define individual constraints yourself - after all, the whole point of [rig components](cloudrig-types) is to generate the bones and constraints for you.  

But unique characters have unique needs, where you may want to **add additional constraints** on specific bones that were generated.
So, if you want to tweak a generated rig by adding a constraint, you have a few options:
- Create a [Tweak Bone](cloudrig-types#tweak-bone) with the name of the bone you want to add the constraint to, and add the constraint. This can make your metarig messy with the addition of many bones.
- Implement adding your constraint in the [post-generation script](generator-parameters#post-generation-script). This is the most flexible solution, but these scripts can also get bloated and messy, and they are a bit secretive. Plus, not everybody knows how to code.
- Your third option is to use Constraint Relinking.

You can do this when you want to add constraints to the primary controls of a rig component, such as the `STR-` controls of a [Toon Chain](cloudrig-types#chain-toon) component, or the `FK-` controls of an [FK Chain](cloudrig-types#chain-fk) component.

All you have to do is add a constraint on the corresponding metarig bone. You can let the constraint target the generated rig if you want, but if you want to avoid that, you can also use a naming convention where you put the target bone's name as the constraint name, separated by an `@` character. See the video below.
<video src="/media/addons/cloudrig/constraint_relinking.mp4" controls></video>