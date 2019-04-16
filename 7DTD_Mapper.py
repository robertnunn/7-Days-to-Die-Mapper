from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as et
import sys
import logging

logging.basicConfig(level=logging.DEBUG, filename='mapping.log', filemode='w')


# takes the POI coords and gets the coords for the label
def marker_coords(char, x_coord, y_coord, font):
  size = font.getsize(char) # gets a tuple with size of text in pixels (X, Y) (X is horiz, Y is vert)
  x_offset = size[0] // 2 # (integer division)
  y_offset = size[1] // 2 # (integer division)
  coords = (x_coord - x_offset, y_coord - y_offset) # origin (0,0) is upper left corner
  return coords


# convert between in-game coordinates and pillow coordinates
def convert_coords(map_size, in_game_coords):
    x, y = in_game_coords
    xloc = (map_size//2) + x
    yloc = (map_size//2) - y
    return (xloc, yloc)


# X is EW, Y is NS
# gets the values from the location string of a POI instance
def extract_xy(text):
    xpos = text.find(',')
    ypos = text.rfind(',') + 1
    return (int(text[:xpos]), int(text[ypos:]))


# takes the in-game, internal coordinates and formats them to be NS EW coordinates
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


# do the thing
def main(folder):
    # get biome and road maps
    biomes = Image.open(folder + '\\biomes.png').convert('RGBA')
    roads = Image.open(folder + '\\splat3.png').convert('RGBA')
    out = Image.alpha_composite(biomes, roads)  # 16k maps require changing the MAX_IMAGE_PIXELS parameter on line 84 of PIL/Image.py (goto alpha_comp declaration, scroll up)
    out.save(folder + '\\' + folder + ' no markers.png', 'png')  # this needs to set the filename to the folder name, folder name should be the seed used
    # out = Image.open('copy.png')
    map_size = out.size[0]
    logging.debug("map_size: " + str(map_size))

    pretty_name_dict = dict()
    with open('prefab_lookup.csv') as lookup_csv:  # open the file, read it, split it into a list of lines, typecast to set
        prefab_text = lookup_csv.read()
        prefab_set = set(prefab_text.split('\n'))
    try:
        prefab_set.remove('')  # remove empty string from set
    except:
        pass
    prefab_list = list(prefab_set)  # back to the more comfortable list
    for i in prefab_list:
        in_name, nice_name = i.split(',')
        pretty_name_dict[in_name] = nice_name # ########################
    logging.debug("pretty name keys")
    logging.debug(pretty_name_dict.keys())
    logging.debug("pretty name values")
    logging.debug(pretty_name_dict.values())
    reverse_pretty_name_dict = dict((v,k) for k,v in pretty_name_dict.items())  # #######################

    # this block of code pulls all the individual POIs out of the XML file
    filename = folder + '\\prefabs.xml'
    results = dict()
    tree = et.parse(filename)
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
    # logging.debug(search_list)

    fnt = ImageFont.truetype('LSANSD.ttf', 45)  # get a font
    fnt_color = (0, 162, 232, 255)  # default color (0, 162, 232, 255)
    d = ImageDraw.Draw(out)  # get a drawing context
    legend = ['Marker\tPOI Name (count)']  # write header row
    for i in range(len(pretty_search_list)):
        marker = str(i) # POIs are listed by number, lookup table in a text file
        search_term = pretty_search_list[i]
        leg_string = str(i) + "\t" + search_term + " (" + str(len(results[reverse_pretty_name_dict[search_term]])) + ")"
        if len(results[reverse_pretty_name_dict[search_term]]) == 1:
            leg_string += ' ' + pretty_in_game_coords(extract_xy(tree.findall("./decoration[@name='" + reverse_pretty_name_dict[search_term] + "']")[0].get('position')))
        legend.append(leg_string)
        current_POI_loc_list = results[reverse_pretty_name_dict[search_term]]
        for j in current_POI_loc_list:  # iterate through each instance of the POI
            txt_coords = marker_coords(marker, j[0], j[1], fnt)  # adjust placement of the marker to center it over the
            d.text(txt_coords, marker, font=fnt, fill=fnt_color)

    out.save(folder + '\\' + folder + ' with markers.png', 'png')  # writing the marked map
    with open(folder + '\\' + folder + ' legend.txt', mode='w') as leg:  # writing the legend file
        leg.write('\n'.join(legend))


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print('Error: Specify at least one folder')
        quit(1)
    folders = args[1:]
    logging.debug(folders)

    for i in folders:
        print('Processing ' + i)
        logging.debug('Processing ' + i)
        main(i)
