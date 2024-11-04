# Effects

## Requirements
* Usually final animation at this point to ensure no mismatch in contact points, timing, etc. This is important as a lot of the FX are usually custom for the exact file and animation, so any further changes would require them to be redone.
* There Should be at least a basic pass on lighting for most FX to be placed in the right context with the visuals. This depends on the specific production and type of FX though. Preliminary FX can be useful before that, usually we just go with the layout version, or what the animators mock up.
* Different file for each type of FX in the shot, set up in the same way as the lighting file with linked animation data and local collection for the FX

## Workflows 

### Set FX
Sometimes FX don’t need to be made uniquely for a shot but can just be created once in a way that they can be used in all shots that use the asset they belong to (e.g. Charge - Flags outside hut).

### Physics Simulations
The use of physics simulations on a shot level is relatively straight-forward. Small simulations can be cached directly into the FX file. Usually the cache should live outside in a place that is accessible by everyone working on the shot.

### Procedural FX

#### Geometry Nodes/Modifiers
A lot of the time instead of doing an elaborate physics simulation it is simpler and gives more control to fake something with a procedural setup (e.g. Charge - Paint can explosion). This can be very custom solutions on a shot basis or a general setup that is reusable over multiple shots (e.g. Sprite Fright melting).

#### Parametric FX assets
Whenever some FX need to be reused over and over in a generic way that needs some simple adjustments/animation for the shot, we use specific FX assets that usually have a rig with just a few bones for transforms and constraints. Usually those also have parameters to control a Geometry Nodes setup (e.g. [Charge - Bullet Impacts](https://studio.blender.org/films/charge/3b0f29b4825fa2/?asset=6191))

#### Shaders
Some FX need to hook into the shader of an existing asset, like a character (e.g. Charge - Bruised and sweaty face). Usually we make this a part of the asset itself and then expose the controlling parameter in a way that we can control it from outside using custom properties on the object level, so we can control it in the rig.

### Frame by frame

#### Grease Pencil
Some FX are better drawn directly, so Grease Pencil is a great way to do that.

#### 'Keymesh' Style
The same applies for 3D meshes. In some cases it can be easier or better for a few frames to sculpt a mesh frame by frame (e.g. Sprite Fright - Bird Poop Wipe). The currently most reliable way to do that, until Blender has native functionality, is to create a separate object per frame and animate its scale to be 1 on the required frame and 0 on any other

Of course, this technique does not allow for 'proper' motion blur.

## Cache Files
* It's very important that any data that is cached is accessible to the render farm and anyone working on the shot. We work with a cache directory that is centralized on our server that everyone at the studio, including our render farm machines, has mounted on `/render/`.
* Since this directory is outside of our project's file structure, these paths must be absolute to work reliably.
* There are different file formates viable for caching data to disk. Usually it is best to stick to Blender's native caching formats, when possible to make absolutely sure no data is lost.

## Integration into Lighting File
* The FX collection(s) need to be linked back into the lighting file and integrated properly into the view layer setup and comp. **It is important that the collection is directly linked into the lighting scene, not instanced. This allows proper visibility control.**
* For FX that affect the lighting, either by casting additional light (e.g. sparks) or obscuring it, the lighting needs to be adjusted accordingly.