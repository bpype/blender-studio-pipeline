
# Set Blender Add-On Preferences

## Blender Kitsu Add-On Preferences

1. Open Blender and select `Edit > Preferences > Add-Ons`.
2. Search for 'Blender Kitsu' and use the checkbox to enable the add-on.
3. Set the following options in the add-on preferences:
    - **Login**  
        - Host: `{my_kitsu_server_url}` *Set during [Kitsu Server Setup](/td-guide/kitsu_server)*
        - Username: `{username@studio.org}`
        - Password: `{user_password}`
    - **Project Settings**
        - Select Production: Choose the current production.
        - Project Root Directory: `data/your_project_name`

![Blender Kitsu Preferences](/media/td-guide/kitsu_pref.jpg)

The following settings will be set automatically if they exist. You can set a custom path by entering them manually, or leave them blank to set them automatically.

- **Animation Tools**
    - Sequence Playblasts: `data/your_project_name/shared/editorial/footage/pre/`
    - Shot Playblasts: `data/your_project_name/shared/editorial/footage/pro/`
    - Frames Directory: `data/your_project_name/shared/editorial/footage/post/`
- **Editorial**
    - Export Directory: `data/your_project_name/shared/editorial/export/`
- **Render Review**
    - Farm Output Directory: `data/your_project_name/render/`
- **Advanced**
    - Use Version Control (bool): Indicates if SVN or GIT-LFS is being used for version control. If disabled, local backups of production files will be created when publishing to Kitsu.
