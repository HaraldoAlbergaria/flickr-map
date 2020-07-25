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
photos_per_page = '500'


#===== FUNCTIONS ==============================================================#

# Function to verify if there is geo tag info
def isGeoTagged(photo):
    if photo['longitude'] != 0 and photo['latitude'] != 0:
        return True
    return False


#===== MAIN CODE ==============================================================#

# check if there is a header file and read it
if os.path.exists("{}/header.html".format(run_path)):
    header_file = open("{}/header.html".format(run_path))
    header = header_file.readlines()
    header_file.close()
else:
    print("ERROR: FATAL: File 'header.html' is missing. Unable to run.")
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
    group_name = flickr.groups.getInfo(api_key=api_key, group_id=group_id)['group']['name']['_content']
except:
    print('ERROR: FATAL: Group doesn\'t exist')
    sys.exit()

# create output map file
map_file = open("{}/map.html".format(run_path), 'w')

# read reader and write to map
for line in header:
    if line == '    mapboxgl.accessToken = \'\';\n':
        # add mapbox access token
        map_file.write("    mapboxgl.accessToken = \'{}\';\n".format(mapbox_token))
    else:
        map_file.write(line)

    if line == '<meta charset=\"utf-8\" />\n':
        # add map page title
        map_file.write("  <title>Group \'{}\' | Photos Map</title>\n".format(group_name))

coordinates = []

print('################ Flickr Map ################')

photos = flickr.groups.pools.getPhotos(api_key=api_key, group_id=group_id, per_page=photos_per_page)
npages = int(photos['photos']['pages'])
total = int(photos['photos']['total'])
print('Generating map for \'{}\''.format(group_name))
print('{} photos in the pool'.format(total))

print('Extracting photo coordinates and ids...')

n = 0
e = 0
m = 0
for pg in range(1, npages+1):
    page = flickr.groups.pools.getPhotos(api_key=api_key, group_id=group_id, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']
    photos_in_page = len(page)
    for ph in range(0, photos_in_page):
        n += 1
        photo = page[ph]
        exists = False
        if isGeoTagged(photo):
            m += 1
            for coord in coordinates:
                if photo['longitude'] == coord[0][0] and photo['latitude'] == coord[0][1]:
                    coord[1].append([photo['owner'], photo['id'], photo['url_sq']])
                    exists = True
            if not exists:
                coordinates.append([[photo['longitude'], photo['latitude']], [[photo['owner'], photo['id'], photo['url_sq']]]])
    e += photos_in_page
    print('Processed photo {0}/{1}'.format(e, total), end='\r')

if m == 0:
    print('No geo tagged photo on the group pool\nMap not generated')
    sys.exit()

print('\n{} photos will be attached to markers'.format(m))
print('Adding markers to map...')

m = 0
n_markers = len(coordinates)
for marker_info in coordinates:
    m += 1
    longitude = marker_info[0][0]
    latitude = marker_info[0][1]
    map_file.write("        locations.push([[{0}, {1}], \"".format(longitude, latitude))
    for photo in marker_info[1]:
        photo_url = 'https://www.flickr.com/photos/{}/{}/in/pool-{}/'.format(photo[0], photo[1], config.group)
        thumb_url = photo[2]
        map_file.write("<a href=\\\"{0}\\\" target=\\\"_blank\\\"><img src=\\\"{1}\\\"/></a> ".format(photo_url, thumb_url))
        print('Added {0}/{1}'.format(m, n_markers), end='\r')
    map_file.write("\"]);\n")

print('\nFinished!')

map_file.write("\n        return locations;\n\n    }\n\n</script>\n\n")
map_file.write("\n</body>\n</html>\n\n")
map_file.close()

