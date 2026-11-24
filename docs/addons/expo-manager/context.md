# Context

![Context Panel](/media/addons/expo_manager/context_panel.jpg)

The Context panel defines the relationship between a Task or Entity on Kitsu and a blend file.

Expo detects context using the `dir` and `file` values in the configured [file patterns](configuration.md#file-patterns). The `lowercase_entities` [naming setting](configuration.md#naming) affects how entity names appear in those paths.

### **Refresh Context**
Context is detected automatically when you open a file. You can always click the "Refresh" icon in the context panel to ensure your context is set correctly for the current file.

### **Set Context**
Use the wrench icon to switch between Task Types or Entities without leaving the current file. **Warning:** Adjusting context is not recommended in a production environment. A malformed context can cause errors when syncing [frame range](shot.md#frame-range) and [publishing](shot.md#publishing).

-----

The tools available depend on the Task Type or Entity associated with the current file.
