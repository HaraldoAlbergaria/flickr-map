#!/usr/bin/python3

# This script generates a html file of all the photos on a
# Flickr group, that can be viewed in a web browser as a map
#
# Author: Haraldo Albergaria
# Date  : Jul 24, 2020
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import flickrapi
import json
import os
import sys
import math

# get full script's path
run_path = os.path.dirname(os.path.realpath(__file__))

# check if there is a config file and import it
if os.path.exists("{}/config.py".format(run_path)):
    import config
else:
    print("ERROR: File 'config.py' not found. Create one and try again.")
    sys.exit()

# check if there is a api_credentials file and import it
if os.path.exists("{}/api_credentials.py".format(run_path)):
    import api_credentials
else:
    print("ERROR: File 'api_credentials.py' not found. Create one and try again.")
    sys.exit()

# Credentials
api_key = api_credentials.api_key
api_secret = api_credentials.api_secret

# Flickr api access
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

# Limits
photos_per_page = '500'
max_number_of_pages = 200
max_number_of_photos = max_number_of_pages * int(photos_per_page)
max_number_of_markers = 5000


#===== FUNCTIONS ==============================================================#

# Function to verify if there is geo tag info
def isGeoTagged(photo):
    if photo['longitude'] != 0 and photo['latitude'] != 0:
        return True
    return False


#===== MAIN CODE ==============================================================#

# check if there is a header file and read it
if os.path.exists("{}/map.html".format(run_path)):
    map_file = open("{}/map.html".format(run_path))
    map = map_file.readlines()
    map_file.close()
else:
    print("ERROR: FATAL: File 'map.html' is missing. Unable to run.")
    sys.exit()

# check if there is a mapbox token file and get the token
if os.path.exists("{}/mapbox_token".format(run_path)):
    mapbox_token_file = open("{}/mapbox_token".format(run_path))
    mapbox_token_lines = mapbox_token_file.readlines()
    mapbox_token_file.close()
    if mapbox_token_lines == []:
        print("ERROR: File 'mapbox_token' is empty. Add a valid token and try again.")
        sys.exit()
    mapbox_token = mapbox_token_lines[0].replace('\n','')
else:
    print("ERROR: File 'mapbox_token' not found. Create one and try again.")
    sys.exit()

try:
    # get group id from group url on config file
    group_id = flickr.urls.lookupGroup(api_key=api_key, url='flickr.com/groups/{}'.format(config.group))['group']['id']
    # get group name
    group_name = flickr.groups.getInfo(api_key=api_key, group_id=group_id)['group']['name']['_content'][:30]
except:
    print('ERROR: FATAL: Group doesn\'t exist')
    sys.exit()

coordinates = []

photos = flickr.groups.pools.getPhotos(api_key=api_key, group_id=group_id, per_page=photos_per_page)
npages = int(photos['photos']['pages'])
total = int(photos['photos']['total'])
print('Generating map for \'{}\''.format(group_name))
print('{} photos in the pool'.format(total))

if os.path.exists("{}/last_total.py".format(run_path)):
    import last_total
    if total == last_total.number:
        print('No changes on number of photos since last run.\nAborted.')
        sys.exit()

os.system("echo \"number = {0}\" > {1}/last_total.py".format(total, run_path))

# create output map file
index_file = open("{}/index.html".format(run_path), 'w')

# read header and write to map
for line in map:
    if line == '    mapboxgl.accessToken = \'\';\n':
        # add mapbox access token
        index_file.write("    mapboxgl.accessToken = \'{}\';\n".format(mapbox_token))
    else:
        index_file.write(line)

    if line == '<meta charset=\"utf-8\" />\n':
        # add map page title
        index_file.write("<title>{} | Photos Map</title>\n".format(group_name))

index_file.close()

print('Extracting photo coordinates and ids...')

# get number of pages to be processed
npages = math.ceil(total/int(photos_per_page))

# to be included on map
n_photos = 0  # counts number of photos
n_markers = 0 # counts number of markers

# extracts only the photos below a number limit
if npages > max_number_of_pages:
    npages = max_number_of_pages
    total = max_number_of_pages * int(photos_per_page);
    print("Extracting for the last {} photos".format(total))

# process each page
for pg in range(1, npages+1):

    # get photos on the pool
    page = flickr.groups.pools.getPhotos(api_key=api_key, group_id=group_id, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']

    photos_in_page = len(page)

    # process each photo on page
    for ph in range(0, photos_in_page):

        photo = page[ph]

        # variable to store information if already exist a marker
        # on the same photo's coordinates
        marker_exists = False

        # check if photo can be included on the map (according to privacy settings)
        if isGeoTagged(photo):

            n_photos += 1

            # get coordinates from photo
            longitude = float(photo['longitude'])
            latitude = float(photo['latitude'])

            # read each markers coordinates and append photo is case
            # there is already a marker on the same coordinate
            for coord in coordinates:
                if longitude == coord[0][0] and latitude == coord[0][1]:
                    coord[1].append([photo['owner'], photo['id'], photo['url_sq']])
                    marker_exists = True
                    break

            # create a new marker to be added to the map
            if not marker_exists:
                coordinates.append([[longitude, latitude], [[photo['owner'], photo['id'], photo['url_sq']]]])
                n_markers += 1

        # stop processing photos if any limit was reached
        if n_photos >= total or n_photos >= max_number_of_photos or n_markers >= max_number_of_markers:
           break

    print('Batch {0}/{1} | {2} photo(s) in {3} marker(s)'.format(pg, npages, n_photos, n_markers), end='\r')

    # stop processing pages if any limit was reached
    if n_photos >= total:
        break
    if n_photos >= max_number_of_photos:
        print("\nMaximum number of photos on map reached!", end='')
        break
    if n_markers >= max_number_of_markers:
        print("\nMaximum number of markers on map reached!", end='')
        break

# stop and exit script if there is no photo to be added to the map
if n_photos == 0:
    if mode == 'photoset':
        print('\nNo geo tagged photo on the user photoset\nMap not generated')
    else:
        print('\nNo geo tagged photo on the user photostream\nMap not generated')
    sys.exit()

print('\nAdding marker(s) to map...')

# check if there is java script file with the markers on map already
# and readt it otherwise created a new one
if os.path.exists("{}/locations.js".format(run_path)):
    locations_js_file = open("{}/locations.js".format(run_path))
else:
    locations_js_file = open("{}/locations.js".format(run_path), 'w')
    locations_js_file.write("var locations = [\n")
    locations_js_file.write("]\n")
    locations_js_file.close()
    locations_js_file = open("{}/locations.js".format(run_path))

# read the file and store it
locations_js_lines = locations_js_file.readlines()
locations_js_file.close()

# create a python file with the existing markers,
# import it and delete it
locations_py_file = open("{}/locations.py".format(run_path), 'w')
locations_py_file.write("locations = [\n")
for i in range(1, len(locations_js_lines)):
    locations_py_file.write(locations_js_lines[i])
locations_py_file.close()
from locations import locations
os.system("rm {}/locations.py".format(run_path))

# create a new javascript file to store new markers
locations_js_file = open("{}/locations.js".format(run_path), 'w')
locations_js_file.write("var locations = [\n")

# get the number of markers (locations) already on map
n_locations = len(locations)
if n_locations > 0:
    print('Map already has {} marker(s)'.format(n_locations))

# counts the number of new photos added to markers
new_photos = 0

# process each marker info already on map
for loc in range(n_locations):

    # get info for photos on marker
    photos_info = locations[loc][1].replace('</div>','')
    n_photos = int(locations[loc][2])

    # get number of photos (coordinates) to be added to map
    n_coords = len(coordinates)

    # iterate over each coordinate
    for coord in range(n_coords):

        # if there is already a marker on the same coordinate
        if coordinates[coord][0] == locations[loc][0]:

            # read each photo already on the marker
            for photo in coordinates[coord][1]:
                photo_url = photos_base_url + photo[0]
                thumb_url = photo[1]

                # if the photo is not already on marker, add the photo to it
                if photo_url not in photos_info:
                    photos_info += "<a href=\"{0}\" target=\"_blank\"><img src=\"{1}\"/></a> ".format(photo_url, thumb_url)
                    new_photos += 1

            # remove photo info from
            # coordinates to be added
            coordinates.pop(coord)

    photos_info += "</div>"

    # update the number of photos on marker
    n_photos += new_photos
    locations[loc][1] = photos_info
    locations[loc][2] = n_photos
    locations_js_file.write("    {}".format(locations[loc]))

    if len(coordinates) > 0:
        locations_js_file.write(",\n")
    else:
        locations_js_file.write("\n")

if new_photos > 0:
    print('Added {} new photo(s) to existing markers'.format(new_photos))

# reverse the coordinates order so
# the newest ones go to the end
coordinates.reverse()

# check if there is remaining markers to be added
n_markers = len(coordinates)
if n_markers > 0:
    print('{} new marker(s) will be added to the map'.format(n_markers))

# remove the oldest locations to make
# room for new markers without violate
# the max number of markers limit
new_locations_length = len(locations) + n_markers
if new_locations_length >= max_number_of_markers:
    new_locations_length = max_number_of_markers - n_markers
    print('Max number of markers reached. Removing {} marker(s)...'.format(n_markers))
    while len(locations) > new_locations_length:
        locations.pop(0)

new_markers = 0

# iterate over each marker to be added
for marker_info in coordinates:

    new_markers += 1

    # get coordinates of the new marker
    longitude = float(marker_info[0][0])
    latitude = float(marker_info[0][1])

    # write it to locations file
    locations_js_file.write("    [[{0}, {1}], \'<div style=\"max-height:410px;overflow:auto;\">".format(longitude, latitude))

    # counts number of photos on marker
    n_photos = 0

    # iterate over each photo
    for photo in marker_info[1]:

        # add photo to marker, writing it to locations file
        photo_url = 'https://www.flickr.com/photos/{}/{}/in/pool-{}/'.format(photo[0], photo[1], config.group)
        thumb_url = photo[2]
        locations_js_file.write("<a href=\"{0}\" target=\"_blank\"><img src=\"{1}\"/></a> ".format(photo_url, thumb_url))
        n_photos += 1

    # finish marker writing to location file
    locations_js_file.write("</div>\', {}]".format(n_photos))
    if new_markers < n_markers:
        locations_js_file.write(",\n")
    else:
        locations_js_file.write("\n")

    print('Added marker {0}/{1}'.format(new_markers, n_markers), end='\r')

# finish script
if new_markers > 0:
    print('')
else:
    print('No new markers were added to the map')

print('Finished!')

locations_js_file.write("]\n")
locations_js_file.close()

