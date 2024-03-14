# Shot Builder Template Files

# Description
Template files are used to implement custom UI when building new shots. Templates are custom .blend files named after the corresponding task type on the Kitsu Server for a given project. Workspaces from the template files are loaded into newly built shot files. 
## Creating a Template Files
1. Save a new .blend file in the directory `your_project_name/svn/pro/config/shot_builder/templates`
2. Name the .blend file after a task type in Kitsu (e.g. Animation, Layout, Compositing), name must match exactly the [task type](https://kitsu.cg-wire.com/customization-pipeline/#task-type) name on Kitsu Server.
3. Customize Workspaces to create custom UI for the task type, and save the file.


## Limitations
Template files are only used for custom UI, other data like scene settings, collections and objects will not be loaded.