
# Set Blender Add-On Preferences

## Blender Kitsu Add-On Preferences

 1. Open Blender and Select `Edit>Preferences>Add-Ons`
 2. Search the 'Blender Kitsu' and use the checkbox to Enable the Add-On
 3. Set the following settings in the add-on preferences
    - Login  
        - Host: `{my_kitsu_server_url}` *Set during [Kitsu Server Setup](/td-guide/kitsu_server)*
        - Username: `{username@studio.org}`
        - Password: `{user_password}`
    - Project Settings
        - Select Production: Choose the current Production
        - Project Root Directory: `data/your_project_name/svn`
    - Animation Tools
        - Playblast directory: `data/your_project_name/shared/editorial/footage/pro/`
        - Frames Directory: `data/your_project_name/shared/editorial/footage/post/`
    - Editorial Export Directory (Optional)
        - `data/your_project_name/shared/editorial/export/`
<!--
TODO Replace Image
-->
![Blender Kitsu Preferences](/media/td-guide/kitsu_pref.jpg)

## Render Review Add-On Preferences
 1. Open Blender and Select `Edit>Preferences>Add-Ons`
 2. Search the 'Render Review' and use the checkbox to Enable the Add-On
 3. Set the following settings in the add-on preferences
    - Ensure `Enable Blender Kitsu` is Enabled
    - Render Farm: `data/your_project_name/render/`
    - Shot Frames: `data/your_project_name/shared/editorial/footage/post/`
    - Shot Previews: `data/your_project_name/shared/editorial/footage/pro/`

![Render Review Preferences](/media/td-guide/render_review_pref.jpg)