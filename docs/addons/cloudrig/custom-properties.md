
::: warning Legacy Documentation
This is a legacy document and set of features. They are under construction as of 30/May/2024 to be replaced with a better system that will implement a customizable UI with nestable properties.
:::

# Custom Properties

CloudRig provides a way to display [custom properties](https://docs.blender.org/manual/en/latest/files/data_blocks.html#files-data-blocks-custom-properties) of your character with a nice UI.

The Cloud Basic Human metarig provides an in-depth example. Generate the rig and find the Character panel under **Sidebar(N panel)->CloudRig**:

![](/media/addons/cloudrig/custom_properties_01.png)

## Character Properties

To understand where these properties are coming from, unhide the last bone collection on the metarig and find the "_Properties_Character_Human_" bone. The UI script will expect to find the character's custom properties on a bone whose name starts with exactly **"Properties_Character_"**. There should only be one such bone. The properties of this bone are always shown in the UI.

Note that the reason this bone gets created on the generated rig in the first place is because it has a [Bone Copy](cloudrig-types#bone-copy) component assigned to it.

Now, let's take a look at its custom properties:

![](/media/addons/cloudrig/custom_properties_03.png)

Supported types are float, int and vector. Floats and Ints will always display as sliders, while vectors will display based on their subtype.

### Custom Strings for Integers
Notice the properties whose names start with a dollar sign($). There is one for each integer property. They are not required, but they allow you to specify a list of strings that should be displayed in the UI based on the current value of the matching integer property.

![](/media/addons/cloudrig/custom_properties_04.png)

## Outfit Properties

Beside the Character bone, you can also have any number of bones that define Outfits. These must be named such that they start with **"Properties_Outfit_"**. In the case of Cloud Basic Human, they define the "Default" and "Comfy" outfits.
If you have any outfit, an outfit selector will be shown in the UI. Outfits can have their own properties, which are only displayed when that outfit is selected. However, they can also apply presets to the character properties.

![](/media/addons/cloudrig/custom_properties_05.png)

Here are the custom properties of "_Properties_Outfit_Default_". Notice the properties whose names start with underscore(_). These properties should never change, as they are only responsible for switching the character property of the same name to the specified value. For example, whenever you switch to the "Default" outfit, the "Hairstyle" value will be set to 1.

Outfit Properties whose names don't start with an underscore are unique to this outfit, and will only be displayed in the rig UI when this outfit is selected.

### Hierarchy
This is an advanced feature, for when you want certain properties to act as the children of other properties in the interface. The example in the metarig shows this: There is a Pants property, with the options "Jeans" and "Shorts". When it is set to "Jeans", the "Belt" child property is visible, but when it is set to "Shorts", the "Belt" property is hidden.
This behaviour is defined in a special property that must be named exactly **prop_hierarchy**. This is a Python dictionary where the keys are the parent properties, and the value is a list of child properties.
Here are some example values for the prop_hierarchy property and what they would mean:
- "Belt" property only visible in the UI when the value of "Pants" is 1:
    `{'Pants-1' : ['Belt']}`
- "Belt" visible when the value of "Pants" is either 1 or 3:
    `{'Pants-13' : ['Belt']}`
- "Belt" visible when the value of "Pants" is greater than 0:
    `{'Pants' : ['Belt']}`

Notes:
- The values of the dictionary are a list, so you could add multiple children to 'Pants'.
- Properties mentioned in prop_hierarchy are drawn before other properties.
- You can put a property in prop_hierarchy without any children, just to define its order in the UI.

### Using the properties
These custom properties of course, do nothing on their own. All CloudRig does for you is copy the properties from the metarig, and display them in the UI in a fancy manner. It's up to you to hook them up to your character and make them do what you want using drivers.
