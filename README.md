## What?

Bring your Redshift and Maya light-setup from Maya to Houdini with the click of a button! (two buttons actually) 
## Why?

At the moment is FBX the standard format to transfer scenes between different software. The problem is that FBX does not recognize a plugin data and just throws it away.
It is handy to have exactly the same light-setup in both the software-packages.
Otherwise the simulation's will not align  when brought together.
## How?

Inside Maya, copy the content of the script in the 'Script Editor'. Click 'Add to shelf' to keep it when restarting.
Run the script and select all the lights you want to export. ** Light types supported for export: **
RedshiftDomeLight
RedshiftPhysicalLight
directionalLight
pointLight
spotLight

** If a selected light is not supported you will receive a warning and the plugin will exit. **

Click the upper button. The script wil detect if selected lights are parented to controllers. 
It will duplicate them outside of the parent and bakes it into the world.

Select the baked **duplicate** lights and any other light that had no parent.
Click the lower button and choose a path to export the .json file with all the light-attributes inside.

Open Houdini > source editor and run  **houdini_transformer.py**
There is a boolean at the top of the script to Toggle between importing the lights as either Redshift lights or houdini lights (Mantra)

To import as mantra lights:
*** use_redshift_lights = False *** 

To import as redshift lights:
*** use_redshift_lights = True *** 

Select the .json and see the magic! 

![0ff36ec841eb3d64d4298753de060f3f](https://user-images.githubusercontent.com/44348300/47940627-8bdd0a00-deeb-11e8-89af-e0f9c20ff044.png)


### what does not work?

In earlier versions of Redshift there is a bug, take the latest and greatest.
Path select with ``$HIP/Desktop/`` in Houdini does not work.
Just insert ``C:/Users/Desktop/`` as path.

