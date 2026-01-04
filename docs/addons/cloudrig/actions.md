# Actions

<details>
<summary> This page goes over the workflow of rigging a character's face with CloudRig and Action Constraints. To understand how this works, first you must be familiar with the <a href="https://docs.blender.org/manual/en/latest/animation/constraints/relationship/action.html#action-constraint">Action constraint</a>. </summary>

TL;DR: Action constraints allow you to move bones into a predetermined pose using a control bone. For example, you can pose your character smiling, save that pose into an Action, then set up constraints so that you can move a controller that will blend the bones into that smiling pose.
</details>

## The Problem
If you've ever rigged a character with Action constraints though, you've probably run into the tedium of having to set up those constraints. Each bone affected by an action needs to have an Action constraint set up on it. Even with the Copy Attributes addon that lets you copy constraints, iterating on the setup is tedious. When trying to make a symmetrical setup, it's even worse, since you have to do a copy operation for each side, and control bones along the center of the rig need to have both constraints with half influence. It is a painful workflow.

## The Solution: Action Set-ups
*Note: Previously called Action Slots, before Blender introduced a concept with the same name.*  
You can find Action Set-ups when selecting a CloudRig metarig and then going to **Properties->Object Data->CloudRig->Actions**:
<img src="/media/addons/cloudrig/cloudrig_actions.png" width=450>

You can add a slot, select an Action, and input all the information about when this action will activate. This is very similar to setting up an individual Action constraint.

These are the steps one might take to set up a blinking and eye opening action:
- On the metarig, create bones named "Blink.L" and "Blink.R" and assign the [Bone Copy](cloudrig-types#bone-copy) component type. Assign colors, widgets, etc as you wish.
- Generate the rig.
- On the generated rig, pose and keyframe your blink pose on frame 20.
- Then, select all the bones you keyed, reset their transforms, and insert a key on frame 10.
- Optionally, you can pose and key an eye open pose on frame 0.
- I highly recommend to select all your keys, press T and set the key interpolation types to Linear.
- Include both left and right eyes in the poses.
- On the Metarig, add an Action Set-up.
- Select the action you've just created. (Give it a descriptive name!)
- Select "Blink.L" as the control bone.
- Set the Transform Channel to which axis of movement you want to activate the blink.
- Symmetry is enabled by default. The UI should indicate that it found "Blink.R" as the opposite side control.
- Input the activation parameters. The frame range should be 1-20, and you can leave the transform min/max default for now

<img src="/media/addons/cloudrig/blink_action.png" width=450>


Regenerate the rig. When you move the Blink control, the action should activate and the character should blink with one eye for each control.

<video src="/media/addons/cloudrig/sintel_blink.mp4" title="" controls></video>


## Iterating
As previously explained, this works by creating Action constraints on each affected bone, which causes them to be transformed to the keyed pose when the control bone is moved. But now what if you want to edit the pose that you keyed? You can simply assign the Action to the generated rig in an Action Editor Dope Sheet, and scrub the timeline as normal. But, if you do that, and then also move the control, the pose will be applied double; Once by the active Action selected on the timeline, and once by the Action Constraints. If you find this annoying, you can disable all the constraints of a given Action, using the Enable/Disable Constraints button that CloudRig adds into the Action Editor's Header:

<img src="/media/addons/cloudrig/disable_action_constraints.png" width=1200>

## Symmetry
This option becomes available if the bone name can be identified as belonging to the left or right side. In parantheses you will see what the opposite side bone name is expected to be. If a bone with that name doesn't exist, the Symmetry option will be grayed out.

When enabled, each bone that is affected by the action will also be checked for a bone name that can be identified as belonging to the left or right side. Left-side bones will be controlled by the left-side control, and right-side bones by the right side control.
In the above example, we have a "Blink" action. This contains the keyframes for BOTH the left and right eyes of your character. Then, when we select either "Blink.L" or "Blink.R" bones as our control bone (it doesn't matter which, as long as they both exist), the Symmetry option should appear, and you can enable it. Now, the left-side bones will be controlled by "Blink.L" and the right-side bones by "Blink.R".

Not all bones that were keyframed in an action have to be identifiable as belonging to the left or right side. This is expected to only happen for bones which are in the center of the character. In this case, two Action constraints will be created on that bone; One for the left and one for the right side. And they will both have an influence of 0.5. You can imagine setting up actions for raising the eyebrows. You will have left and right eyebrows, but both of them will affect the center of the forehead by 50% each.

## Corrective Actions
When rigging a face, chances are your actions will only work nicely on their own at first.
For example, you might have a LipsWide action and a LipsUp action, but when both of them are activated, the result is probably a disaster. That's where a Corrective Action comes in.
The idea is exactly the same as a Corrective Shape Key: A corrective action activates when exactly two other actions are also activating. This lets your shapes combine correctly.

To set up a corrective action:
0. Make sure you already have two actions fully set up and working. Let's stick with the "LipsUp" and "LipsWide" example.
1. Create a new action. Naming it something like Lips_Up+Wide would make sense.
2. On the generated rig, pose your controls so that both LipsWide and LipsUp are being activated.
3. Pose and keyframe the necessary corrections in the Lips_Up+Wide action. As with a normal action set-up, you need the center frame of your frame range to be keyframed to the default pose.
4. Go back to your Metarig, add a new Action Set-up, select Lips_Up+Wide, then enable the Corrective checkbox.
5. Select the two trigger actions in the selection boxes that appear.
5. The eye icon next to the selection box lets you double-check the trigger action's set-up. If you notice something wrong there and want to fix it, you can use the jump button next to the eye, to jump to that action set-up.
6. In the Actions list, actions that either correct or are corrected by the currently active one will be marked with a link icon.
7. Now just set your Frame Start/End values and then hit Generate.

Note: It doesn't matter where corrective actions are placed in the list. To achieve correct transform mixing, they will be created above the first trigger in the constraint stack.

## Shape Keys
For any shape key of any object that is parented to the generated rig, if the shape key is named the same as one of the Actions in CloudRig's Action Set-ups, it will be driven. For symmetrical actions, you can put .L/.R at the end of the shape key's name.
So, if you have a symmetrical blink action set-up like in the first example, and your action was called "Blink", you could create shape keys named "Blink.L" and "Blink.R" on the head mesh. As long as the head mesh is parented to the generated rig, when you re-generate, the shape keys will gain drivers so that they are activated by your blink controls the same way your Action Constraints are.
