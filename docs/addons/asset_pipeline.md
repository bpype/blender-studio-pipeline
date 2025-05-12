# Asset Pipeline

## Introduction
This add-on was designed to enable simultaneous work on the same asset (eg. a character) by multiple artists. The add-on works by tracking what data each artist contributes to the asset and merges the assets together into a final "Published" asset. 

Checkout the [Asset Pipeline Demo](https://projects.blender.org/studio/blender-studio-tools/pulls/145)


## Key Concepts
**Task Layers** Task Layers are defined in a JSON file that describes the number of layers used to manage the asset. Typically each task layer is given its own file, artists can optionally house multiple task layers inside the same file if required. Each task layer is used to describe a step in the asset making process (e.g."Modeling", "Rigging", "Shading"). The number and content of a task layer is fully configurable by the production. 

**Ownership** Each piece of data in the Asset Pipeline is owned by a task layer, this includes Objects, Task Layer Collections and Transferable Data. The owner of data is the only person who can contribute to that piece of data, including modifying or removing that data. Objects own their object data. Multiple objects referencing the same object data is not supported.

**Asset Collection** Is the top-level collection for a given asset, all relevant objects/sub-collections for the asset are contained within this collection.

**Task Layer Collection** These collections are children of the asset collection, each Task Layer collection is owned by a specific task layer, they are all top-level child collections to the Asset Collection. Children of the Task Layer collections are owned by the Task Layer collection's owner.

**Transferable Data** Is data that a part or associated with an object or mesh, but can be explicitly owned and updated. This is the key concept that allows multiple artists to contribute to an asset. During the Push/Pull process Transferable Data is applied on top of each object, allowing artist A to own an object but artist B to own the vertex groups on that object for example. 

Transferable Data Types:
 - Vertex Groups
 - Modifiers
 - Constraints
 - Custom Properties
 - Materials (including slots, index and the material IDs)
 - ShapeKeys 
 - Attributes
 - Parent Relationships

 **Shared IDs** Shared IDs are data-blocks that can be owned by many 'users'. This data type is limited to Geometry Node Groups and Images. These are pieces of data that need to be explicitly owned by a task layer, and only that task layer may update this data-block, but other task layers may reference this data-block. 


## Example Scenario
In the default configuration of the add-on, a character could be worked on simultaneously by a shading artist and a rigger. Let's say the character is called Bob. The following files can be created:
- Bob.rigging.blend
- Bob.shading.blend
- publish/Bob.v001.blend

The team members can then agree that the rigging file should only be touched by the rigger, and the shading file should only be touched by the shading artist. In the rigging file, the Asset Pipeline add-on is configured to consider this file as the Rigging task layer, and the shading file is of course configured to be the shading task layer. This just means ticking the appropriate checkboxes in each file.
What's considered rigging or shading data is configured in a configuration .json file, which both artists should be referencing. For example, vertex groups will be owned by rigging, and material assignments will be owned by shading. When an artist is done with a piece of work, they push the data they own to the publish, and pull any data they don't own from the publish, to make sure all data is synchronized.


## Creating New Assets
Once the add-on is installed you will be greeted by a new sidebar in the 3D View, titled 'Asset Pipeline'. Under the panel 'Asset Management' you will find a UI to set up a new Asset. The New Asset UI has two modes: "Current File" and "Blank File".

### Current File Mode
"Current File" mode will retain you current .blend file's data and allow you to use its current directory to setup a new Asset. 
To setup an asset using "Current File" mode, please open the file you would like to setup as an asset, then select "Current File" mode in the asset pipeline side panel in the 3D View. 

 1. Select the "Task Layer Preset" you would like to use.
 2. Select the collection to be the Asset Collection, this is the top level collection for your asset.
 3. Select 'Create New Asset'
 4. In the operator pop-up select which task layers will be local to your file, typically artists only select one.
 5. Ensure 'Create Files for Unselected Task Layers' is enabled, otherwise the add-on will not automatically create files for the other task layers.
 6. Press OK to set-up current file/folder as an Asset. The add-on will automatically create a published file, this file will be empty until you push to it. 


### Blank File Mode
"Blank File" mode will create a new blank asset in a new directory named after your asset.

 1. Select the "Task Layer Preset" you would like to use.
 2. Enter the name and prefix desired for your asset
 3. Select 'Create New Asset'
 4. In the operator pop-up select which task layers will be local to your file, typically artists only select one.
 5. Ensure 'Create Files for Unselected Task Layers' is enabled, otherwise the add-on will not automatically create files for the other task layers.
 6. Press OK to set-up current file/folder as an Asset. The add-on will automatically create a published file, this file will be empty until you push to it. 


## Push/Pull 
The Push/Pull process happens in three steps.

### Updating Ownership
When you Push/Pull a file, you will be greeted with an operator dialogue. This dialogue will list any new data that it has found in your file. Pressing OK will assign these new pieces of data to your local task layer, if you have multiple local task layers, you will be able to select which one is the owner of each piece of data. Once completed this information will be used to ensure your work is merged properly with the published file. 

### Save File
The add-on will optionally save your current file plus any unsaved/unpacked images will be saved in a directory relative to your asset (configurable in the add-on preferences). It will always create a back-up of your current file, in the case where the merge process fails, you will be prompted to revert your file back to its pre-merge status.

### Merge with Published File
Push and Pull are merging operations done to/from the published file. When you want to share your updated work to the rest of the team select "Push to Publish" to update the published file with your changes. Push will update any Transferable Data you edited, and update any objects/collections you own with the version in your current file. Transferable Data owned by other artists will be re-applied to your objects.

If another artist then uses the "Pull to Publish" operator the same process will occur, keeping all objects, collections and Transferable Data that is local to their file, and importing any data that was owned externally by other task layers. 

## Surrendering Ownership
In the ownership inspector each Object/Transferable Data item has an option to "surrender" that piece of data. When surrendering this piece of data is now "up for grabs" to all other task layers. After surrendering artists will need to push this update to the published file. The surrendered item's ownership indicator will be replaced by an "Update Surrendered" operator, this operator is available to all task layers except the one that surrendered that data. When another task layer pulls in from the publish, they will be able to run the "Update Surrendered" operator to claim it assigning it to that task layer. 

## Publish New Version
To Publish a new version of an asset select the "Publish New Version" operator. The operator dialogue will require an input on which publish type to create. Publish types are as follows. 

### Active
An active publish is a publish that can be referenced by the production into shot files, multiple version can be published if some shots require an older version of the current asset, but only a single asset will be updated with changes from the push/pull target.

### Staged
A staged asset, is an publish that cannot be referenced by the production, only one staged asset can exist at a time. If a staged publish exists it will replace the active publish as the push/pull target. The staged area exists so artists can collaborate on a new version of an asset that is not ready to be used in production.

### Sandbox
A sandbox publish is simple a way to test out the final published version of your asset. You can create as many sandbox publishes as you want to check your work and ensure the merge process produces results that are expected. Sandbox publish is never used as a push/pull target and is for testing only. 

## Creating Custom Task Layers

Add your own custom Task Layers to the asset pipeline addon. To create a custom task layer, find one of the templates at `/asset_pipeline/task_layer_configs/` copy one of the task layers to your own custom directory. The layout of the JSON file is as follows...


```JSON
{
    // Task Layer Types are formatted as {"Name of Task Layer": "Prefix"}
    "TASK_LAYER_TYPES": { 
        "Modeling": "MOD", 
        "Rigging": "RIG",
        "Shading": "SHD"
    },
    
     // These are the default or preferred owners for each type of transfer data
    "TRANSFER_DATA_DEFAULTS": {
        "GROUP_VERTEX": { // Name of Transfer Data Type (not customizable)
            "default_owner": "Rigging", // Matching one of the Task Layer types above
            "auto_surrender": false // If data type will be surrendered on initialization
        },
        "MODIFIER": {
            "default_owner": "Rigging",
            "auto_surrender": false
        },
        "CONSTRAINT": {
            "default_owner": "Rigging",
            "auto_surrender": false
        },
        "CUSTOM_PROP": {
            "default_owner": "Modeling",
            "auto_surrender": false
        },
        "MATERIAL": {
            "default_owner": "Shading",
            "auto_surrender": true
        },
        "SHAPE_KEY": {
            "default_owner": "Modeling",
            "auto_surrender": false
        },
        "ATTRIBUTE": {
            "default_owner": "Rigging",
            "auto_surrender": false
        },
        "PARENT": {
            "default_owner": "Rigging",
            "auto_surrender": false
        }
    },

    // These are default attributes created by Blender
    "ATTRIBUTE_DEFAULTS": {
        "sharp_face": {
            "default_owner": "Modeling",
            "auto_surrender": true
        },
        "UVMap": {
            "default_owner": "Shading",
            "auto_surrender": true
        }
    }
}

```

## Default Ownership & Auto Surrender
The `default owner` value describes the preferred owner of a given data type. The default owner is used only if the current work file contains that task layer, otherwise a local task layer owner is used. 

The `auto_surrender` value if set to True will automatically surrender the data type when it is initialized when the `default_owner` is not found. This is useful to ensure a task layer  needs to own all instances of a given data type (e.g. Shading Task Layer wants to own all Materials so all other task layers will automatically surrender their Materials). 

If the `default_owner` is not local to the current file and the `auto_surrender` value is set to False, the data type will be owned by the local task layer owner, and will not be surrendered.

## Hooks
Hooks are used to add custom functionality to the asset pipeline. Hooks are optional. The hooks are defined in a python file. There are two types of Hooks, Production Level and Asset Level. Production Hooks are used globally on all assets. Asset Hooks are used only on a specific asset. 

    - Production hooks: `your_project_name/pro/svn/pro/config/asset_pipeline/hooks.py`
    - Asset hooks: `your_project_name/pro/svn/assets/{asset_type}/{asset_name}/hooks.py` 


Hook files can be automatically created using the `Create Production Hook` and `Create Asset Hook` operators, from the tools sub-panel in the asset pipeline side panel. Below is an example of a hook file.

**Example Hook File**
```python
import bpy
from asset_pipeline.hooks import hook

'''

Rules:
    merge_mode: ['pull', 'push'] # Run hook only during pull or push (both if left blank)
    merge_status: ['pre', 'post'] # Run hook either before or after push/pull (both if left blank)

Keyword Arguments:
    asset_col: bpy.types.Collection # Get the top level collection for the current asset
'''

@hook(merge_mode='pull', merge_status="pre")
def prod_pre_pull(asset_col: bpy.types.Collection, **kwargs):
    # Only runs before pull
    print(f"Asset Collection Name '{asset_col.name}'")
    print("PRE PULL production level asset hook running!")


@hook(merge_mode='pull', merge_status="post")
def prod_post_pull(**kwargs):
    # Only runs after pull
    print("POST PULL production level asset hook running!")


@hook(merge_mode='push', merge_status="pre")
def prod_pre_push(**kwargs):
    # Only runs before push
    print("PRE PUSH production level asset hook running!")


@hook(merge_mode='push', merge_status="post")
def prod_post_push(**kwargs):
    # Only runs after push
    print("POST PUSH production level asset hook running!")
```

**Important** Function naming must be unique between the production hooks and asset hooks files.
## Gotchas

### Multi-User Object Data
 - Object Data that is owned by more than one object (like meshes used by multiple objects) are only valid between objects of the same task layer/owner. If you attempt to link externally owned object data from a locally owned object, the object data will be duplicated instead on Push/Pull. 