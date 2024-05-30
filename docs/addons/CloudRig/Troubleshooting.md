# Generation Log
CloudRig implements a Generation Log, which is a list of potential issues detected during the rig generation process. Each time you re-generate the rig, this list is re-populated. Ideally, you want to keep this list completely empty.

<img src="/media/addons/cloudrig/generation_log.png" width=600>  

If rig generation fails, you will also find the error message here, along with a Bug Report button.

Many issues will have a button to let you fix them as quick as possible.

Feel free to submit suggestions for issues that this system currently doesn't detect.

### Naming
Certain bone naming conventions are reserved for CloudRig's generation process. The following bone naming habits in a metarig **should be avoided**:
- Identifying left/right sides with anything other than a ".L/.R" suffix
- There should be no other dot-separated suffix besides this.
- Any .00x ending on any bone name should be avoided.
- Avoid prefixes that are used by CloudRig: "DEF-", "ORG-", "STR-". These are only allowed in the metarig in the case of a Bone Tweak component.
- For all chain rig types, incrementing bone names should always correspond to parent/child relationships. For example, "Bone2" must be the child of "Bone1". Bones that are named like this should not be siblings, or unrelated to each other.

Such names may result in strange and tricky to identify generation errors.