from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as et
import sys
import logging
import os
import time

logging.basicConfig(level=logging.INFO, filename='mapping.log', filemode='w')


def timeme(method):
    def wrapper(*args, **kw):
        startTime = int(round(time.time() * 1000))
        result = method(*args, **kw)
        endTime = int(round(time.time() * 1000))

        print(endTime - startTime,'ms')
        return result

    return wrapper


def timeme(method):
    def wrapper(*args, **kw):
        startTime = int(round(time.time() * 1000))
        result = method(*args, **kw)
        endTime = int(round(time.time() * 1000))

        print(endTime - startTime,'ms')
        return result

    return wrapper


# takes the POI coords and gets the coords for the label
# this centers the marker (char) on the point specified (x_coord, y_coord)
def marker_coords(char, x_coord, y_coord, font):
    size = font.getsize(char)  # gets a tuple with size of text in pixels (X, Y) (X is horiz, Y is vert)
    x_offset = size[0] // 2  # (integer division)
    y_offset = size[1] // 2  # (integer division)
    coords = (x_coord - x_offset, y_coord - y_offset)  # origin (0,0) is upper left corner
    return coords


# convert between in-game coordinates and pillow coordinates
# in-game coords have their origin at the center, pillow coords have their origin in upper left corner
def convert_coords(map_size, in_game_coords):
    x, y = in_game_coords
    xloc = (map_size//2) + x  # maps are hi-res enough that these rounding errors are negligible
    yloc = (map_size//2) - y
    return (xloc, yloc)


# X is EW, Y is NS
# gets the values from the location string of a POI instance
# returns a tuple
def extract_xy(text):
    xpos = text.find(',')
    ypos = text.rfind(',') + 1
    return (int(text[:xpos]), int(text[ypos:]))


# takes the in-game, internal coordinates (tuple) and formats them to be NS EW coordinates (returns a string)
def pretty_in_game_coords(coord_tuple):
    x, y = coord_tuple
    if x > 0:
        EW = str(x) + "E"  # east is positive
    else:
        EW = str(abs(x)) + "W"  # west is negative
    if y > 0:
        NS = str(y) + "N"  # north is positive
    else:
        NS = str(abs(y)) + "S"  # south is negative
    return NS + " " + EW


# returns a tuple containing both pretty and reverse pretty name dictionaries
# pretty name dict = p_n_d[internal name] = pretty display name
def get_prefab_lookup(lookup_csv):
    pretty_name_dict = dict()
    with open(lookup_csv) as lookup_csv_file:  # open the file, read it, split it into a list of lines, typecast to set to remove duplicates
        prefab_text = lookup_csv_file.read()
        prefab_set = set(prefab_text.split('\n'))
    try:
        prefab_set.remove('')  # remove empty string from set
    except KeyError:
        pass

    # prefab_list = list(prefab_set)  # because sets aren't
    for i in prefab_set:
        in_name, nice_name = i.split(',')
        pretty_name_dict[in_name] = nice_name  # create name-pretty name lookup dict
    logging.debug("pretty name keys")
    logging.debug(pretty_name_dict.keys())
    logging.debug("pretty name values")
    logging.debug(pretty_name_dict.values())
    reverse_pretty_name_dict = dict((v, k) for k, v in pretty_name_dict.items())  # #######################
    return pretty_name_dict, reverse_pretty_name_dict


# do the thing
@timeme
def main(folder, lookup):
    try:
        # get biome and road maps
        biomes = Image.open(folder + '\\biomes.png').convert('RGBA')
        roads = Image.open(folder + '\\splat3.png').convert('RGBA')
        prefabs_xml = folder + '\\prefabs.xml'
    except:
        logging.error('Missing required file(s), aborting ' + folder)
        return
    try:
        nitro_map = Image.open(folder + '\\previewMap.png').convert('RGBA')
        nitro_bool = True
    except:
        nitro_bool = False

    if biomes.size != roads.size:
        logging.error('Size mismatch between biomes and roads. Aborting ' + folder + ' biomes: ' + str(biomes.size) + ' roads: ' + str(roads.size))
        return
    if nitro_bool:
        if nitro_map.size != biomes.size:
            logging.error('Size mismatch between biomes and previewMap. Cancelling labeling of previewMap in ' + folder)
            nitro_bool = False
    out = Image.alpha_composite(biomes, roads)
    out.save(folder + '\\' + folder + ' no markers.png', 'png')  # this needs to set the filename to the folder name
    map_size = out.size[0]
    logging.debug("map_size: " + str(map_size))

    pretty_name_dict = lookup[0]
    reverse_pretty_name_dict = lookup[1]

    # this block of code pulls all the individual POIs out of the XML file
    results = dict()
    try:
        tree = et.parse(prefabs_xml)
    except:
        logging.error('Error parsing prefabs.xml for ' + folder + ', aborting.')
        return
    prefabs = tree.findall('./decoration')
    for model in prefabs:
        name = model.get('name')
        logging.debug("prefab name is: " + name)
        coords = convert_coords(map_size, extract_xy(model.get('position')))
        if name in results.keys():
            results[name].append(coords)  # if we've seen this one before
        else:
            results[name] = [coords]  # if this is the first one
    logging.debug("len(results.keys()): " + str(len(results.keys())))

    results_set = set(results.keys())
    lookup_set = set(pretty_name_dict.keys())
    search_set = results_set.intersection(lookup_set)
    search_list = list(search_set)  # search_list is internal names at this point
    pretty_name_list = []
    for i in search_list:
        pretty_name_list.append(pretty_name_dict[i])
        logging.debug(pretty_name_dict[i])
    search_list = sorted(search_list)
    pretty_search_list = sorted(pretty_name_list)
    logging.debug("search_list sorted and typecast")
    logging.debug(search_list)
    logging.debug("pretty name list")
    logging.debug(pretty_name_list)

    fnt = ImageFont.truetype('LSANSD.ttf', 45)  # get a font
    fnt_color = (0, 162, 232, 255)  # default color (0, 162, 232, 255)
    d = ImageDraw.Draw(out)  # get a drawing context for the biome+road composite
    if nitro_bool:
        dp = ImageDraw.Draw(nitro_map)  # get a drawing context for the NitroGen previewMap.png
    legend = ['Marker\tPOI Name (count)']  # write header row
    for i in range(len(pretty_search_list)):
        marker = str(i)  # POIs are listed by number, lookup table in a text file
        search_term = pretty_search_list[i]
        leg_string = str(i) + "\t" + search_term + " (" + str(len(results[reverse_pretty_name_dict[search_term]])) + ")"
        if len(results[reverse_pretty_name_dict[search_term]]) == 1:
            leg_string += ' ' + pretty_in_game_coords(extract_xy(tree.findall("./decoration[@name='" + reverse_pretty_name_dict[search_term] + "']")[0].get('position')))
        legend.append(leg_string)
        current_POI_loc_list = results[reverse_pretty_name_dict[search_term]]
        for j in current_POI_loc_list:  # iterate through each instance of the POI
            txt_coords = marker_coords(marker, j[0], j[1], fnt)  # adjust placement of the marker to center it over the
            d.text(txt_coords, marker, font=fnt, fill=fnt_color)
            if nitro_bool:
                dp.text(txt_coords, marker, font=fnt, fill=fnt_color)

    out.save(folder + '\\' + folder + ' with markers.png', 'png')  # writing the marked map
    if nitro_bool:
        nitro_map.save(folder + '\\previewMap with markers.png', 'png')  # write the marked previewMap.png
    with open(folder + '\\' + folder + ' legend.txt', mode='w') as leg:  # writing the legend file
        leg.write('\n'.join(legend))


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:  # if no folders are specified, look in every folder in the directory
        logging.debug('scanning folders')
        folders = []
        for entry in os.scandir():
            if entry.is_dir():
                folders.append(entry)
    else:
        folders = args[1:]
        for i in folders:
            if not os.path.isdir(i):
                folders.remove(i)
    logging.debug(folders)
    Image.MAX_IMAGE_PIXELS = None  # this is necessary for 16k maps, otherwise decompression bomb-prevention kicks in and cancels it
    lookup_csv_path = 'prefab_lookup.csv'

    lookup_csv = get_prefab_lookup(lookup_csv_path)

    for name in folders:
        print('Processing ' + name.name)
        logging.info('Processing ' + name.name)
        main(name.name, lookup_csv)
