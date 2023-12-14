# Blender Kitsu
blender-kitsu is a Blender Add-on to interact with Kitsu from within Blender. It also has features that are not directly related to Kitsu but support certain aspects of the Blender Studio Pipeline. [Blender-Kitsu blogpost](https://studio.blender.org/blog/kitsu-addon-for-blender/)

<!-- TOC -->

- [Blender Kitsu](#blender-kitsu)
    - [Table of Contents](#table-of-contents)
    - [Installation](#installation)
    - [How to get started](#how-to-get-started)
    - [Features](#features)
        - [Sequence Editor](#sequence-editor)
            - [Metadata](#metadata)
            - [Push](#push)
            - [Pull](#pull)
            - [Multi Edit](#multi-edit)
            - [Shot as Image Sequence](#shot-as-image-sequence)
            - [General Sequence Editor Tools](#general-sequence-editor-tools)
        - [Context](#context)
            - [Animation Tools](#animation-tools)
            - [Lookdev Tools](#lookdev-tools)
            - [Error System](#error-system)
    - [Shot Builder](#shot-builder)
    - [Development](#development)
        - [Update Dependencies](#update-dependencies)
    - [Troubleshoot](#troubleshoot)
    - [Credits](#credits)

<!-- /TOC -->
blender-kitsu is a Blender Add-on to interact with Kitsu from within Blender. It also has features that are not directly related to Kitsu but support certain aspects of the Blender Studio Pipeline. 

[Blender-Kitsu blogpost](https://studio.blender.org/blog/kitsu-addon-for-blender/)

## Table of Contents


## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Add-ons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 
## How to get started
After installing you need to setup the add-on preferences to fit your environment.
In order to be able to log in to Kitsu you need a server that runs the Kitsu production management suite.
Information on how to set up Kitsu can be found [here](https://zou.cg-wire.com/).

If Kitsu is up and running and you can successfully log in via the web interface you have to setup the `addon preferences`.

> **_NOTE:_**  If you want to get started quickly you only need to setup login data and active project

###### **Setup Login Data**

![image info](/media/addons/blender_kitsu/prefs_login.jpg)

>**Host**: The web address of your kitsu server (e.G https://kitsu.mydomain.com)<br/>
**Email**: The email you use to log in to kitsu<br/>
**Password**: The password you use to log in to kitsu<br/>

Press the login button. If the login was successful, the next step is..

###### **Setup Project Settings**

![image info](/media/addons/blender_kitsu/prefs_project.jpg)

>**Project Root Directory**: Path to the root of your project. Will later be used to configure the addon on a per project basis<br/>


###### **Setup Animation Tools**


![image info](/media/addons/blender_kitsu/prefs_anim_tools.jpg)


>**Playblast Root Directory**: Path to a directory in which playblasts will be saved to<br/>
**Open Web browser after Playblast**: Open default browser after playblast which points to shot on kitsu<br/>
**Open Video Sequence Editor after Playblast**: Open a new scene with Sequence Editor and playback playblast after playblast creation<br/>


###### **Setup Lookdev Tools**

![image info](/media/addons/blender_kitsu/prefs_lookdev.jpg)

>**Render Presets Directory**: Path to a directory in which you can save .py files that will be displayed in render preset dropdown. More info in: How to use render presets.<br/>

###### **Setup Media Search Paths**

![image info](/media/addons/blender_kitsu/prefs_outdated_media.jpg)

>**Path List**: List of paths to top level directory. Only media that is a child (recursive) of one of these directories will be scanned for outdated media.<br/>

###### **Setup Miscellaneous**

![image info](/media/addons/blender_kitsu/prefs_misc.jpg)

>**Thumbnail Directory**: Directory where thumbnails will be saved before uploading them to kitsu. Cannot be edited.<br/>
**Sequence Editor Render Directory**: Directory where sequence editor renderings will be saved before uploading them to kitsu. Cannot be edited<br/>
**Enable Debug Operators**: Enables extra debug operators in the sequence editors Kitsu tab.<br/>
**Advanced Settings**: Advanced settings that changes how certain operators work.<br/>

After setting up the addon preferences you can make use of all the features of blender-kitsu

## Features
blender-kitsu has many feature and in this documentation they are divided in different sections.

#### Sequence Editor
---
blender-kitsu sequence editor tools were constructed with the idea in mind to have a relationship between sequence strips and shots on Kitsu. This connection enables the exchange of metadata between the edit and the shots on Kitsu. Some examples are frame ranges of shots can be directly updated from the edit or thumbnails can be rendered and uploaded to Kitsu with a click of a button and many more which you will find out in this section:

##### Metastrips
Metastrips are regular Movie Strips that can be linked to a shot in kitsu. It is a good idea to create a separate meta strip in a separate channel that represents the shot. That gives you the freedom to assemble a shot out of multiple elements, like multiple storyboard pictures, and still have one metastrip that contains the full shot range.

![image info](/media/addons/blender_kitsu/metastrip.001.jpg)

>**Good to know**: A metastrip can have 3 states. It can be **initialized** but **not** linked yet. That means the movie strips knows I am a metastrip but I don't have a relationship to a shot on Kitsu yet. It can be **linked**, which means the strip is already initialized and is linked to a sequence_id and shot_id on Kitsu. Only if a strip is linked you can exchange metadata, push thumbnails etc. The last state is **uninitialized** which basically means it's a regular movie strips and has nothing to do with kitsu.

###### Create a Metastrip
1. Select a sequence strip for which you want to create a metastrip and execute the `Create Metastrip` operator.
This will import a metastrip.mp4 (1000 frame black video) file which is saved in the add-ons repository. The metastrip will be placed one channel above the selected strips. Make sure there is enough space otherwise the metastrip will not be created.

###### Initialize a Shot
1. Select a metastrip and open the `Kitsu` tab in the sidebar of the sequence editor. You will find multiple ways on how to initialize your strip.
![image info](/media/addons/blender_kitsu/sqe_init_shot.jpg)

2. Case A: Shot does **already exist** on Kitsu

    2.1 Execute the `Link Shot` operator and a pop up will appear that lets you select the sequence and the shot to link to

    2.2 Alternatively you can also link a shot by pasting the URL. (e.G: https://kitsu.yourdomain.com/productions/fc77c0b9-bb76-41c3-b843-c9b156f9b3ec/shots/e7e6be02-5574-4764-9077-965d57b1ec12) <br/>

    ![image info](/media/addons/blender_kitsu/sqe_link_shot.jpg)

3. Case B: Shot **does not exist** on Kitsu yet

    3.1 Execute the `Initialize Shot` Operator.

    3.2 Link this strip to a sequence with the `Link Sequence` operator or create a new sequence with the `Submit New Sequence` operator.

    3.3 Type in the name of the new shot in the `Shot` field

    3.4 Execute the `Submit New Shot` operator in the `Push` Panel (Will warn you if the shot already exists on Kitsu). This operator can optionally populate each 'Shot' with a task set to the project's default task status.

>**Note**: Most of the operator are selection sensitive. So you can do these operations for a batch of sequence strips. If you have nothing selected it will usually try to operate on all strips in the sequence editor. <br/>
![image info](/media/addons/blender_kitsu/sqe_init_selection.jpg)

##### Metadata
If you select a single linked strip you will see a `Metadata` panel that shows you the information that is related to the sequence and shot the strip is linking to.

![image info](/media/addons/blender_kitsu/sqe_metadata.jpg)

The frame range will be updated by using the Blender editing tools on the strip. (trimming, sliding, etc.). <br/>
If you execute the `Initialize Shot Start Frame` operator (refresh icon) the current in point of the strip will be remapped so the shot starts at 101 in the current editing state. <br/>
You can reassign the shot to another sequence by executing the `Link Sequence` Operator, change the shot name or the sequence color. <br/>

If you linked in a sequence that has no `["data"]["color"]` attribute on Kitsu yet the gpu overlay line will be white. In order to add a new sequence color execute the `Add Sequence Color` operator. <br/>

![image info](/media/addons/blender_kitsu/sqe_sequence_color_init.jpg)


All this information and more can be `pushed` to kitsu which bring us to the next panel. <br/>

##### Push

In the `Push` panel you will find all the operators that push data to Kitsu. <br/>

![image info](/media/addons/blender_kitsu/sqe_push.jpg)

>**Metadata**: Pushes metadata of shot: sequence, shot name, frame range, sequence_color
>>**Note**:  Global edit frame range will be saved in `"frame_in"` `"frame_out"` kitsu shot attribute <br/>
The actual shot frame range (starting at 101) will be saved in `["data"]["3d_start"]` kitsu shot attribute <br/>

>**Thumbnails**: Renders a thumbnail of the selected shots (will be saved to the `Thumbnail Directory` -> see addon preferences) and uploads it to Kitsu. Thumbnails are linked to a task in Kitsu. So you can select the Task Type for which you want to upload the thumbnail with the `Set Thumbnail Task Type` operator. <br/>
If you select multiple metastrips it will always use the middle frame to create the thumbnail. If you have only one selected it will use the frame which is under the cursor (it curser is inside shot range). <br/>
**Render**: Renders the shot range out of the sequence editor, saves it to disk and uploads it to Kitsu. Works very similar to the `Push Thumbnail` operator.

##### Pull
In the `Pull` panel you will find all the operators that pull data from Kitsu to a metastrip. <br/>

![image info](/media/addons/blender_kitsu/sqe_pull.jpg)

>**Metadata**: Pulls metadata of shot: sequence, shot name, shot description and updates the strip name to match the shot name.
>>**Note**:  Frame ranges will **never** be updated when pulling data from Kitsu. They belong to the edit and will only be pushed to Kitsu.<br/>

If you have not sequence selected the `Pull Entire Edit` Operator will appear in the `Pull` panel.<br/>

![image info](/media/addons/blender_kitsu/sqe_pull_entire_edit.jpg)

After you selected the channel it will go through all shots on Kitsu, create a metastrip which will be linked to the respective shot and pulls all metadata. <br/>
It will use te `frame_in` and `frame_out` attribute on Kitsu to determine the in and out points in the edit. So make sure these are up to date and don't overlap. <br/>

As a result a bigger edit with nice sequence_colors can look pretty cool:

![image info](/media/addons/blender_kitsu/sqe_sequence_colors.jpg)


##### Multi Edit

The `Multi Edit` panel only appears when you select multiple metastrips that are all `initialized` but not `linked` yet. <br/>

![image info](/media/addons/blender_kitsu/sqe_multi_edit.jpg)

It is meant to be way to quickly setup lots of shots if they don't exist on Kitsu yet. You specify the sequence all shots should belong to and adjust the `Shot Counter Start` value. In the preview property you can see how all shots will be named when you execute the `Multi Edit Strip` operator. <br/>

##### Shot as Image Sequence
The `Shot as Image Sequence` Operator will replace a playblast from your Playblast Root directory with an image sequence located in the Frames Root directory. The Shots Directory and the Frames Directory should have matching folder structures. Typically the format is `/{sequence_name}/{shot_name}/{shot_name}-{shot_task}/`

![Shot as Image Sequence](/media/addons/blender_kitsu/Shot_as_Image_Sequence.jpg)

Use this operator to replace playblasts with image sequences that have been approved via the [Render Review Add-On](/addons/render_review) Image Sequences can be loaded as either `EXR` or `JPG` sequences.

###### Advanced Settings
If you check the `Advanced` checkbox next to the counter value, you have access to advance settings to customize the operator even more.

![image info](/media/addons/blender_kitsu/sqe_multi_edit_advanced.jpg)

You can adjust the number of counter digits, the increment size and also the `Pattern` it will use to generate the shot name. <br/>
>**Pattern**: supports 3 wildcards. `<Sequence>`, `<Counter>`, `<Project>` that can be used multiple times in any order. <br/>
**Custom Sequence Variable**: specify a custom string that should be used in the `<Sequence>` wildcard instead of the sequence name. <br/>
**Custom Project Variable**: specify a custom string that should be used in the `<Project>` wildcard instead of the project name. <br/>

##### General Sequence Editor Tools
In the general tab you can find some tools that don't directly relate to Kitsu but are useful for editing.

![image info](/media/addons/blender_kitsu/sqe_outdated_scan.jpg)

`Scan for outdated media` will scan the selected / all sequence strips for their source media file. It searches for a later version in the same directory as the source media. If the current media file is outdated it will highlight that strip with a red line in the sequence editor:

![image info](/media/addons/blender_kitsu/sqe_outdated_overlay.jpg)

To update the outdated strips you can select them individually and by clicking the `Arrow Up` or `Arrow Down` you cycle through the available versions on disk. You will be prompted with an information if you reached the latest or oldest version.

![image info](/media/addons/blender_kitsu/sqe_outdated_update.jpg)


>**Note**: The operator searches for a version string e.G `v001` and checks files that are named the same but have a different version. <br/>

#### Context
---
blender-kitsu context features were constructed with the idea in mind to create a relationship between a certain task on Kitsu and a blend file. <br/>

To create 'context' you can find the `Context Browser` in the `Kitsu` panel in the sidebar of the 3D Viewport. <br/>

![image info](/media/addons/blender_kitsu/context_browser.jpg)

By selecting the different drop down menus you can browse through the Kitsu file structure and set e.G the active sequence, active shot and task type you want to work on. <br/>

The `Detect Context` operator tries to look at the filepath of the blend file and figure out the context automatically. <br/>

Depending on which `Task Type` you select different tool sets will be available.

##### Animation Tools

The animation tools will show up when you selected a `Task Type` with the name `Animation`. <br/>


![image info](/media/addons/blender_kitsu/context_animation_tools.jpg)

>**Create Playblast**: Will create a openGL viewport render of the viewport from which the operator was executed and uploads it to Kitsu. The `+` button increments the version of the playblast. If you would override an older version you will see a warning before the filepath. The `directory` button will open a file browser in the playblast directory. The playblast will be uploaded to the `Animation` Task Type of the active shot that was set in the `Context Browser`. The web browser will be opened after the playblast and should point to the respective shot on Kitsu. <br/>
**Push Frame Start**: Will Push the current scene's frame start to Kitsu. This will set the `['data']['3d_start]` attribute of the Kitsu shot.
**Pull Frame Range**: Will pull the frame range of the active shot from Kitsu and apply it to the scene. It will use read `['data']['3d_start]` attribute of the Kitsu shot. <br/>
**Update Output Collection**: Blender Studio Pipeline specific operator. <br/>
**Duplicate Collection**: Blender Studio Pipeline specific operator. <br/>
**Check Action Names**: Blender Studio Pipeline specific operator. <br/>

##### Lookdev Tools
The lookdev tools will show up when you selected a `Task Type` with the name `Lighting` | `Rendering` | `Compositing`. <br/>

![image info](/media/addons/blender_kitsu/context_lookdev_tools.jpg)

>**Apply Render Preset**: Consists of a dropdown menu that displays all `.py` files which are present in the `Render Presets Directory` (defined in the add-on preferences). Select the `.py` file you want to execute. When you hit the `Play` button the `main()` function of the python file will be executed. Very useful to quickly switch between different render settings.

##### Error System

blender-kitsu has different checks that are performed during file load or during editing. If it detects an error that prevents other operators to run it will display an error in the ui. <br/>


![image info](/media/addons/blender_kitsu/error_animation.jpg)

 ## Shot Builder
Shot Builder is an Add-on that helps studios to work with task specific
Blend-files. The shot builder is part of the shot-tools repository. The main functionalities are

* Build blend files for a specific task and shot.
* Sync data back from work files to places like kitsu, or `edit.blend`.

### Design Principles

The main design principles are:

* The core-tool can be installed as an add-on, but the (production specific)
  configuration should be part of the production repository.
* The configuration files are a collection of python files. The API between
  the configuration files and the add-on should be easy to use as pipeline
  TDs working on the production should be able to work with it.
* TDs/artists should be able to handle issues during building without looking
  at how the add-on is structured.
* The tool contains connectors that can be configured to read/write data
  from the system/file that is the main location of the data. For example
  The start and end time of a shot could be stored in an external production tracking application.

### Connectors

Connectors are components that can be used to read or write to files or
systems. The connectors will add flexibility to the add-on so it could be used
in multiple productions or studios.

In the configuration files the TD can setup the connectors that are used for
the production. Possible connectors would be:

* Connector for text based config files (json/yaml).
* Connector for kitsu (https://www.cg-wire.com/en/kitsu.html).
* Connector for blend files.

### Layering & Hooks

The configuration of the tool is layered. When building a work file for a sequence
there are multiple ways to change the configuration.

* Configuration for the production.
* Configuration for the asset that is needed.
* Configuration for the asset type of the loaded asset.
* Configuration for the sequence.
* Configuration for the shot.
* Configuration for the task type.

For any combination of these configurations hooks can be defined.

```
@shot_tools.hook(match_asset_name='Spring', match_shot_code='02_020A')
def hook_Spring_02_020A(asset: shot_tools.Asset, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides when Spring is loaded in 02_020A.
    """

@shot_tools.hook(match_task_type='anim')
def hook_task_anim(task: shot_tools.Task, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides for any animation task.
    """
```

#### Data

All hooks must have Python’s `**kwargs` parameter. The `kwargs` contains
the context at the moment the hook is invoked. The context can contain the
following items.

* `production`: `shot_tools.Production`: Include the name of the production
  and the location on the filesystem.
* `task`: `shot_tools.Task`: The task (combination of task_type and shot)
* `task_type`: `shot_tools.TaskType`: Is part of the `task`.
* `sequence`: `shot_tools.Sequence`: Is part of `shot`.
* `shot`: `shot_tools.Shot` Is part of `task`.
* `asset`: `shot_tools.Asset`: Only available during asset loading phase.
* `asset_type`: `shot_tools.AssetType`: Only available during asset loading phase.

#### Execution Order

The add-on will internally create a list containing the hooks that needs to be
executed for the command in a sensible order. It will then execute them in that
order.

By default the next order will be used:

* Production wide hooks
* Asset Type hooks
* Asset hooks
* Sequence hooks
* Shot hooks
* Task type hooks

A hook with a single ‘match’ rule will be run in the corresponding phase. A hook with
multiple ‘match’ rules will be run in the last matching phase. For example, a hook with
‘asset’ and ‘task type’ match rules will be run in the ‘task type’ phase.

###### Events

Order of execution can be customized by adding the optional `run_before`
or `run_after` parameters.

```
@shot_tools.hook(match_task_type='anim',
                 requires={shot_tools.events.AssetsLoaded, hook_task_other_anim},
                 is_required_by={shot_tools.events.ShotOverrides})
def hook_task_anim(task: shot_tools.Task, shot: shot_tools.Shot, **kwargs) -> None:
    """
    Specific overrides for any animation task run after all assets have been loaded.
    """
```

Events could be:

* `shot_tools.events.BuildStart`
* `shot_tools.events.ProductionSettingsLoaded`
* `shot_tools.events.AssetsLoaded`
* `shot_tools.events.AssetTypeOverrides`
* `shot_tools.events.SequenceOverrides`
* `shot_tools.events.ShotOverrides`
* `shot_tools.events.TaskTypeOverrides`
* `shot_tools.events.BuildFinished`
* `shot_tools.events.HookStart`
* `shot_tools.events.HookEnd`

During usage we should see which one of these or other events are needed.

`shot_tools.events.BuildStart`, `shot_tools.events.ProductionSettingsLoaded`
and `shot_tools.events.HookStart` can only be used in the `run_after`
parameter. `shot_tools.events.BuildFinished`, `shot_tools.events.HookFinished`
can only be used in the `run_before` parameter.


### API

The shot builder has an API between the add-on and the configuration files. This
API contains convenience functions and classes to hide complexity and makes
sure that the configuration files are easy to maintain.

```
register_task_type(task_type="anim")
register_task_type(task_type="lighting")
```

```
# shot_tool/characters.py
class Asset(shot_tool.some_module.Asset):
    asset_file = "/{asset_type}/{name}/{name}.blend"
    collection = “{class_name}”
    name = “{class_name}”

class Character(Asset):
    asset_type = ‘char’


class Ellie(Character):
    collection = “{class_name}-{variant_name}”
    variants = {‘default’, ‘short_hair’}

class Victoria(Character): pass
class Rex(Character): pass

# shot_tool/shots.py
class Shot_01_020_A(shot_tool.some_module.Shot):
    shot_id = ‘01_020_A’
    assets = {
        characters.Ellie(variant=”short_hair”),
        characters.Rex,
        sets.LogOverChasm,
    }

class AllHumansShot(shot_tool.some_module.Shot):
    assets = {
        characters.Ellie(variant=”short_hair”),
        characters.Rex,
        characters.Victoria,
    }

class Shot_01_035_A(AllHumansShot):
    assets = {
        sets.Camp,
    }

```

This API is structured/implemented in a way that it keeps track of what
is being done. This will be used when an error occurs so a descriptive
error message can be generated that would help the TD to solve the issue more
quickly. The goal would be that the error messages are descriptive enough to
direct the TD into the direction where the actual cause is. And when possible
propose several solutions to fix it.

### Setting up the tool

The artist/TD can configure their current local project directory in the add-on preferences. 
This can then be used for new blend files. The project associated with an opened (so existing)
blend file can be found automatically by iterating over parent directories until a Shot Builder
configuration file is found. Project-specific settings are not configured/stored in the add-on,
but in this configuration file.

The add-on will look in the root of the production repository to locate the
main configuration file `/project_root_directory/pro/shot-builder/config.py`. This file contains general
settings about the production, including:

* The name of the production for reporting back to the user when needed.
* Naming standards to test against when reporting deviations.
* Location of other configuration (`tasks.py`, `assets.py`) relative to the `shot-builder` directory of the production.
* Configuration of the needed connectors.

#### Directory Layout
``` bash
└── project-name/ # Project Root Directory
    └── pro/
        ├── assets/
        ├── shot-builder/
        │   ├── assets.py
        │   ├── config.py
        │   ├── hooks.py
        │   └── shots.py
        └── shots/
```

### Usage

Any artist can open a shot file via the `File` menu. A modal panel appears
where the user can select the task type and sequence/shot. When the file
already exists, it will be opened. When the file doesn't exist, the file
will be built.

In the future other use cases will also be accessible, such as:

* Syncing data back from a work file to the source of the data.
* Report of errors/differences between the shot file and the configuration.

### Open Issues

#### Security

* Security keys needed by connectors need to be stored somewhere. The easy
  place is to place inside the production repository, but that isn't secure
  Anyone with access to the repository could misuse the keys to access the
  connector. Other solution might be to use the OS key store or retrieve the
  keys from an online service authenticated by the blender cloud add-on.

  We could use `keyring` to access OS key stores.

## Development
### Update Dependencies
To update the dependencies of `Blender_Kitsu` please follow these steps.
 1. `cd scripts-blender/addons/blender_kitsu/wheels` To enter the directory of dependant modules
 2. `rm -r *.whl` To remove any existing packages (or manually remove .whl files if you are on windows)
 3. `pip download gazu` to get the latest gazu and it's dependencies as wheels
 4. `rm certifi* charset_normalizer* idna* requests* urllib3* websocket_client*` to remove the modules that are already included in blender

## Troubleshoot
blender-kitsu makes good use of logging and status reports. Most of the operators report information in the blender info bar. More detailed logs can be found in the blender system console. If you feel like anything went wrong, consider opening a console and check the logs.

## Credits
This project uses gazu as a submodule to interact with the gazu data base. Gazu is written by CG Wire, a company based in France.
- gazu repo: https://github.com/cgwire/gazu
- gazu doc : https://gazu.cg-wire.com/

The file at ./blender_kitsu/sqe/draw.py is copied and modified from the blender-cloud-addon (https://projects.blender.org/archive/blender-cloud-addon).
Original author of this file is: Sybren A. Stuevel.


