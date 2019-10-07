# 7 Days to Die Mapper
## Overview
Takes in the biomes.png, splat3.png, and prefabs.xml documents created during world generation and combines them into a labeled map showing desired points of interest.

## Details
This is a python script that produces a labeled and unlabeled composite map that shows the roads (highways, local roads, country roads) and the biome at a particular place. The maps are 1-to-1 with the game world, meaning one pixel on the map is one block in the game. 

In addition to overlaying the road map onto the biome map, it also takes in the data from prefab_lookup.csv to decide which points of interest (POIs) to label on the map. It then sorts the POIs by their "pretty" name, numbers them, and produces a legend text file so you know what is where without cluttering the map to unreadability.

If a particular POI only has one instance, the legend will also include the in-game coordinates (e.g., xxxN xxxW) so you don't have to hunt over a huge map for a particular POI (I'm looking at you traders and skyscrapers!)

## Example Maps
The "Fallout" "OldSchool", and "TheFrozenNorth" folders show example outputs for 8k maps.

## Technical Details
### Dependencies
This script depends on the following libraries (current versions as of April 16, 2019)
* sys
* logging (0.5.1.2)
* xml.ElementTree (1.3.0)
* Pillow (6.0.0)
* os
### Technical Overview
During the process of world generation, the game generates three files: biomes.png (shows what biomes are where), splat3.png (shows all roads), and prefabs.xml (an xml listing of every POI and its location). 7DTD_Mapper can be run from a batch file (if on windows) or a bash script (if on linux, usually server admins) and takes arguments in the form of a space-delimited list of folder names (the sample folders require quotes). At the moment, it can take any number of folders as arguments. If run with no arguments, it will scan any folders in the current directory and attempt to create maps from the files in those folders. The script produces three files and places them in the same folder as their source data: two maps (one with labels, one without), and a legend file that tells you what the number labels mean.

### Folder Structure
The script requires that all three of the required files be in the folder you want to generate a map of. The mapper script, font file (LSANSD.ttf), and prefab lookup (prefab_lookup.csv) should be in the root folder. See below for a diagram.
```
  7DTD Mapper\
    7DTD_Mapper.py
    LSANSD.TTF
    prefab_lookup.csv
    South Pudume County\
      biomes.png
      splat3.png
      prefabs.xml
    Zuhehi Territory\
      biomes.png
      splat3.png
      prefabs.xml
```
### Editing prefab_lookup.csv
prefab_lookup.csv is a comma-separated value file, that matches the internal name of a prefab (first column) with the "pretty" name (second column; I have taken a couple liberties with naming). To modify this file, you can simply delete lines if you don't want that POI marked on the map. If you want to add POIs that are not on the list, you can navigate to your 7 Days prefab directory (steamapps/common/7 Days to Die/Data/Prefabs) and examine the images (jpg) to find the desired POI. Once found, add the name of the file without file extension to a new line in prefab_lookup.csv (order doesn't matter) and the "pretty" name you want displayed in the legend.

## To-Do List
* Add output of complete POI listing with in-game coordinates (intersection of desired POIs and POIs that are present)
