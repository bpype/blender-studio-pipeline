# Introduction: Workstations 

<!--- Feedback from Julien
- Who is the "Introduction" addressed to? Who is the user? 
  - Still feels like it is addressed at a TD or IT developer
- Could be reworded to state the advantages of the current system instead of starting with the failures of our previous unnamed one
-->

<!--- Juliens suggestions for pages of the User section
- Collect notes from all artists at the studio on how they tend to customize the system and common shortcuts. Give some general pointers at system settings in a new section. Examples:
   - Disable greying by opening sub-windows
   - Multiple cursor issues with Wayland
   - Behavior customization of Super-Key and `Alt Tab`
- Recommend some more general purpose software packages we use like beeRef, dolphin, nomacs, mpv, OBS, spectacle
- Ask typical non-Linux users at the studio to read some sections and see if she understands anything. 
  Good stress for missing basic information.
-->

## Why we installed Gentoo at the studio

- The old infrastructure we used were not easily scalable, maintainable, and easy to re-deploy.
- Previously, we had no way to push up updates consistently to computers in the studio. All updates had to be done by the artists themselves.
- With the new system we can easily deploy fixes for program other than Blender. Before this our artists could be stuck with issues that had already been fixed for up to a half a year because we couldn’t update or roll out the fixes ourselves.

## Main principles

Stay true to and expand on “The freedom to create” mantra with the following principles:

- We should ensure that we have a free (as in freedom) ecosystem that other studios can use.
- The solutions we develop should be shareable and easily deployable elsewhere.
- It should be easy to collaborate with other software projects to solve issues. (Easy to modify and deploy software, including Blender, with custom patches)
- No central point of failure. IE no: “The login server is down, so I can’t log in to my computer today”.

## Limitations

- While the system is very flexible, we can’t cater to everyone. So while it would be possible to support very exotic setups that some users want, we can’t realistically spend time on it.
- More planning and communication is needed when deploying new software solutions at the studio. (Should make things more structured and organized though…)
- Training and documentation is needed for people to be able to use the system.


## Useful Links
[The Gentoo handbook](https://wiki.gentoo.org/wiki/Handbook:AMD64)
