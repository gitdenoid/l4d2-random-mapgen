**Modified by Denoid**

This a Python-built L4D2 Random Level Generator. It's built by Mc$core and (currently) entirely uses prefabs (the tiles folder) in order to generate it.
I have updated the code so it works with Python 3, and if I decide to make any other changes, I'll push them.

Feel free to fork/suggest; I'll get to it when I can!

## Prerequisites
1. Python knowledge (a lot if you plan to edit the code)
2. Python is installed
3. Left 4 Dead 2 & its Authoring Tools
4. Console is enabled
5. You know Valve Hammer Editor exists

# Installation
NOTE: As there is currently no implemented CFG file, you'll need to change code if you make any changes to these instructions.
1. Install and place within its own folder within your sdk_content folder in your Left 4 Dead 2 directory. EX: `/Left 4 Dead 2/sdk_content/mapgen/`
2. That's it. That's the installation!

## Usage
**combiner.py** is the main file, so you'll have to run it via a terminal in order to generate a map file:

```py combiner.py [seed] [mapname]```

With the two parameters being optional. It will default to the **SEED** variable if you do not specify one.

An uncompiled map file will be generated in an output file (if python errors, you may have to create the folder). If no map name is specified, it will be named "map-[seed].vmf".

In order to compile and play the map, you'll have to compile it in Hammer like so:
1. Open the "Left 4 Dead 2 Authoring Tools" and navigate to "Valve Hammer Editor".
2. Navigate to the output file and open the map you generated.
3. Press "F9" or Navigate to "File -> Run Map..." to open up the compiler. Press "OK".
4. Once the map is compiled, if Left 4 Dead 2 does not automatically open, do so.
5. Open up console (Default: ~) if the map did not automatically launch. Type `map [mapname]` and press "Enter".
6. The map will load! Be sure to look up [a L4D Navigation Mesh tutorial](https://developer.valvesoftware.com/wiki/L4D_Level_Design/Nav_Meshes) so the director/bots can navigate the map.

If you're having trouble getting the Director to recognize where the end of the level is:
1. Type `z_debug 1` in console.
2. Go to the toilet room (or whatever your finale room is set to) and face one of the navigation squares.
3. Type `mark FINALE` in console.
4. Type `nav_save` in console.
5. Restart the map by exiting and reloading the map, or type `mp_restartgame 1` and then `director_start` to restart the director.

## Current Issues
1. The automatic navigation mesh generation does not work.
2. Many seeds won't generate until the toilet finale. I would like the toilet finale.
3. Doubly emphasizing the fact that most seeds won't generate a complete level, meaning you'll have to find ones that do.
4. The generator currently aims for "true randomness" and won't account for styling/themes.
5. Sizing is very picky; note this if you decide to create more prefabs for it to pull from.

There's definitely more that I've missed; these are the most pressing.

----------------------------
*Previous Readme*
# About
This is a proof of concept random map generator for Source Based games.
It is intended to create levels from random map tiles for Left 4 Dead 2.

This project is abandoned. Pick it up, if you like!

Created by Mc$core, ask him for help. Knowledge of Python programming required.

http://www.hehoe.de/mcs
CC BY-SA 3.0

## Usage (depreciated)
* Put the files into the directory "...\Steam\SteamApps\common\left 4 dead 2\sdk_content\mapsrc\mcs"
* Run the python script "combiner.py". The script requires Python 2 and NumPy.
* Open the resulting map source file "combined.vmf" in the Hammer Editor with the appropriate configuration (for L4D2 Hammer is started from the L4D2 Authoring Tools)
* Choose File->Run Map
* Start L4D2 with the console enabled and load the map
* Execute the config file "combined" by entering "exec combined" in the console
* Press the + button on your keypad repeatedly. This will let the game generate the nav mesh. Keep streaking it until the level reloads for the second time and cheats are disabled again.
* Restart L4D2 and start playing!

## Advanced Usage
* Edit combiner.py and change the seed and/or NUMBER_OF_TILES for different maps.
* In case the final map cannot be added, try a different setting or tweak the map in Hammer.
* Create additional tiles or new tile sets (see below)

## Included Features
- Nonlinear levels
- Support for more than one door per direction
- Support for doors in arbitrary position
- Support for overlays and cubemaps
- Checks for different door sizes
- Loop detection and mending with self
- Support for rectangular shaped map tiles of arbitrary size
- Improved map tile collision detection
- Support for more than one ground level

## Missing Features
- proper translation of materials
- fully automated nav mesh generation ("pointer" crosshair is not updated with setpos - player interaction needed)
- to be checked: what else apart from overlays and cubemaps needs IDs to operate
- to be checked: alpha blending on displacements
- Improved layout generation
-- Calculate distances while generating (Dijkstra?), limit dead-end lengths
- Support ladders
-- Improve automatic nav mesh generation

## Map Tiles
A map tile is connected to the next tile with a "portal". To define a portal, create a solid brush within the outmost side of the tile. Apply the material DEV/DEV_BLENDMEASURE (configurable) to the side facing outward only. This markes this exact position to be a "portal". The combiner looks for portals to mend the tiles together. You may place a prop_door_rotating in the vicinity (configurable) of the portal. In case the door leads to nowhere, the combiner will remove the door and leaves the solid in place. In case the door connects to another room, the solid is removed and the door is left in place. A map tile must allow player transit between all portals.
A tile is always translated only, never rotated. Due to the process, all positions will become integers. Angles are unaffected.
