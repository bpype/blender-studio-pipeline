# Animation Testing

## General requirements

To start with the animation testing we need **the initial version of the character rigs**. For that, the character design needs to be approved, with sculpts expression of the facials, that later will be applied to the pose library and some heroe poses for the body, that will guide the animation posing marking some do and don’ts.

## Goal of the task

The goal of the animation testing is to:
- Test the rig weight painting and deformations, having feedback sessions with rigging and modeling until it moves correctly
- Develop an animation style with the help of the sculpts and heroe poses
- Create clear guidelines for both art style and animation style

The steps to follow are the next:
* Test the character rigs
* Feedback with rigging and modeling
* Create selection sets
* Create animation design guides and pose libraries
* Animation tests

## Test the character rigs

This is what we call **stress testing** the character: basically we start doing simple transformations on the controllers to see if they behave how we expect, seeing if there are any flaws on the weight painting or the behavior of the controllers, also we check if more controllers are needed on the rig. 

### Feedback with rigging/modeling

In case we find any problems with the rig, we have feedback with rigging. They will decide if they can fix it or if it is needed to have some modeling tweaks in the geometry, this process of the feedback can be repeated as many times as needed.

### Create selection sets

This step is made by the animators but translated to the rigger: he will add them to the character blend file so the selection sets will be by default every time the rig is linked. 

The process we use is to create a selection of controllers we are gonna need for certain parts, for example the face of the character, and like this it is really easy to select them any time we want.

For parts like the arms/legs, we just make the selection sets from one side of the body and flip the selection when we want to select the opposite side, like this we keep the pop up selection sets menu cleaner.

## Create animation design guide and pose libraries

We will create the animation design guide based on the sculpts and heroe poses modeling will provide, this is basically a do & don'ts in terms of animation. Some benefits of this is giving all the animators a common reference point making poses and expressions more consistent, will give the new animators an easier jumping onboard and adjusting to the animation style and will shorten the time needed for feedback and revisions resulting in a faster animation output.

Next to that, creating an animation poselib will make all the process even faster because everybody will share the same approved poses, being easier to keep the character on model.

Animation poselibs will be created at least for facials and hands, being this the more complex part to pose.

## Animation test

We will do this **to find the animation style and personality of the characters**.

We will start mostly with some kind of walkcycle, because is the easiest way to find personality in motion, and later we will start to do more complex animation test, body mechanics and later lipsyncs if needed, until we find the correct personality and animation style ( level of cartoon/realism, be on 1s or 2s, etc).