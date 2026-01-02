# Troubleshooting
CloudRig implements a Generation Log, which shows a list of potential issues detected during the rig generation process. Each time you re-generate the rig, this list is re-populated. Ideally, you want to keep this list completely empty.

<img src="/media/addons/cloudrig/generation_log.png" width=600>

If rig generation fails, you will also find the error message here. Some failures are considered "expected", ie. you did something wrong, and the error message will tell you what it was. Unexpected failures and uncertain cases will show a [Bug Report](https://projects.blender.org/Mets/CloudRig/issues/new/choose) button, which I recommend you use. Fatal errors in the generation code are always fixed in the next version, if reported.

Many issues will have a button to let you fix them as quick as possible.

Feel free to submit suggestions for issues that this system currently doesn't detect and warn about!

### Bone Naming
Certain bone naming conventions are reserved for CloudRig's generation process. Please follow these guidelines to avoid issues that may be difficult to troubleshoot:
- For all Chain component types, incrementing bone names should always correspond to parent/child relationships. For example, "Bone2" must be the child of "Bone1". Bones that are named like this should not be siblings, nor unrelated to each other.
- Identify left/right sides with only exactly ".L/.R" suffixes, nothing else.
- Avoid other dot-separated suffix besides this, including .00x number suffixes.
- Avoid prefixes that are used by CloudRig: "DEF-", "ORG-", "STR-", and more. These are only allowed in the metarig in the case of a Bone Tweak component.
