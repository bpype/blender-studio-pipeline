Welcome to the CloudRig wiki!

This page aims to give you a brief overview of CloudRig's features, with links for further diving into each topic.

# Accessing this wiki from Blender
You can right click on most CloudRig UI elements and click on Online Manual to bring up the relevant page on this wiki.

# General workflow
The rig generation workflow with CloudRig revolves around inputting parameters on a simple **Metarig**, which is then used to generate the **Control Rig**, which is what you will actually use to control your character. The Control Rig can be re-generated based on new Metarig parameters or proportions as many times as needed, until you get exactly what you want.  
- Create a skeleton outlining the proportions of your character. This is your Metarig.
- Assign a Rig Component to specific bones that define the features that you want in your rig, such as a spine, arms, and legs.
- Customize the components using their parameters to change the available features and have the level of complexity you need.
- Generate the rig.

The simplicity of this workflow allows for fast iteration. If you want to add or remove a feature from the rig, there's no need for copy-pasting and renaming of hundreds of bones, or worse, manually making changes to dozens of bones, constraints and drivers just to make a slight change to how the rig behaves. You just tick or untick a checkbox and hit Regenerate.  

So how is it done?

# Getting Started
Spawn the Cloud Basic Human preset metarig via **Add->Armature->CloudRig Metarigs->Cloud Human**.  
Now try selecting the "UpperArm.L" bone in pose mode. Then go to **Properties->Bone->CloudRig Component**.

<img src="/media/addons/cloudrig/cloudrig_component.png" width=400>  

As you can see here, this bone is assigned the "Limb: Generic" Component Type, and you can see all of its parameters in this panel. This Component Type and these parameters determine the behaviour of the control rig that will be generated when you press the Generate CloudRig button.

CloudRig aims to cover a wide and ever expanding variety of needs with its component types. This is facilitated by the fact that it is being used in production at the Blender Studio. Whatever weird character (or prop!) those crazy guys come up with, CloudRig has to be able to generate a rig for it.

The [CloudRig Types](CloudRig-Types) page covers all the available component types included in CloudRig.


# Starting From Scratch
If you want to start from a fresh armature, all you need to do is enable CloudRig under **Properties->Data->CloudRig**. Here you will also find the [Generation Parameters](Generator-Parameters), which are a few high level pieces of data used for the generation process. The Rig Components sub-panel shows you a hierarchical list of bones which have components assigned to them. You'll also find some other panels, which are mentioned below.


# Actions & Face Rigging
If you want to rig faces with CloudRig, you will probably want to use a combnination of component types such as [Bone Copy](CloudRig-Types#bone-copy), [Chain: Eyelid](CloudRig-Types#chain-eyelid) and [Aim](CloudRig-Types#aim). But the real magic will happen in the [Action system](Actions). You can get an example of this by playing with the included Sintel metarig.


# Generation Log
There are many ways to make mistakes while using CloudRig, also while rigging in general. CloudRig will NEVER automatically fix your mistakes, but it will try to detect them and give you suggestions or even one-button solutions to fix them.
After generating your rig, you will find a list of potential issues here, in the Generation Log panel. Some of these issues will have a tailor-fitted button to fix the issue. This is all handled by the [Troubleshooting](Troubleshooting) module.


# Rig UI
Once generated, select your generated rig, and press the N key to bring up the Sidebar. You should see a CloudRig tab, which contains the rig UI. This is where the animators will be able to find rig settings and a collection selector.  
<img src="/media/addons/cloudrig/rig_ui.png" width=400>  


# Custom Properties
CloudRig provides a way to present arbitrary custom properties to the rig's user. This can be useful for allowing animators to customize a character's outfits, materials, etc, with a nice and clean UI. Check out the [Custom Properties](Custom-Properties) page to see how that works.

