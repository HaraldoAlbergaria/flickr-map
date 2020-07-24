#!/usr/bin/python3

# This script generates a html file of all the photos on the
# Flickr user's photostream, that can be viewed in a web browser as a map
#
# Author: Haraldo Albergaria
# Date  : Jul 21, 2020
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import flickrapi
import json
import os
import sys

run_path = os.path.dirname(os.path.realpath(__file__))

if os.path.exists("{}/config.py".format(run_path)):
    import config
else:
    print("ERROR: File 'config.py' not found. Create one and try again.")
    sys.exit()

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

# Function to get photo's geo privacy
def getGeoPrivacy(photo):
    if photo['geo_is_public'] == 1:
        return 1
    if photo['geo_is_contact'] == 1:
        return 2
    if photo['geo_is_friend'] == 1 and photo['geo_is_family'] == 0:
        return 3
    if photo['geo_is_friend'] == 0 and photo['geo_is_family'] == 1:
        return 4
    if photo['geo_is_friend'] == 1 and photo['geo_is_family'] == 1:
        return 5
    if photo['geo_is_friend'] == 0 and photo['geo_is_family'] == 0:
        return 6


#===== MAIN CODE ==============================================================#

if os.path.exists("{}/header.html".format(run_path)):
    header_file = open("{}/header.html".format(run_path))
    header = header_file.readlines()
    header_file.close()
else:
    print("ERROR: FATAL: File 'header.html' is missing. Unable to run.")
    sys.exit()

if os.path.exists("{}/mapbox_token".format(run_path)):
    mapbox_token_file = open("{}/mapbox_token".format(run_path))
    mapbox_token_lines = mapbox_token_file.readlines()
    mapbox_token_file.close()
    if mapbox_token_lines == []:
        print("ERROR: File 'mapbox_token' is empty. Add a valid token and try again.")
        sys.exit()

else:
    print("ERROR: File 'mapbox_token' not found. Create one and try again.")
    sys.exit()

mapbox_token = mapbox_token_lines[0].replace('\n','')

user_id = flickr.urls.lookupUser(api_key=api_key, url='flickr.com/people/{}'.format(config.user))['user']['id']
real_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['realname']['_content']

map_file = open("{}/map.html".format(run_path), 'w')

for line in header:
    if line == '    mapboxgl.accessToken = \'\';\n':
        map_file.write("    mapboxgl.accessToken = \'{}\';\n".format(mapbox_token))
    else:
        map_file.write(line)
    if line == '<meta charset=\"utf-8\" />\n':
        map_file.write("  <title>{} | Photos Map</title>\n".format(real_name))

photos = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, per_page=photos_per_page)

npages = int(photos['photos']['pages'])
total = int(photos['photos']['total'])

coordinates = []
photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']

print('############## Flickr Map ##############')
print('Generating map for \'{}\''.format(real_name))
print('{} photos in the photostream'.format(total))
print('Extracting photo coordinates and ids...')

n = 0
e = 0
m = 0
for pg in range(1, npages+1):
    page = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']
    photos_in_page = len(page)
    for ph in range(0, photos_in_page):
        n += 1
        photo = page[ph]
        exists = False
        longitude = photo['longitude']
        latitude = photo['latitude']
        if (longitude != 0 and latitude != 0) and (config.geo_privacy == 0 or getGeoPrivacy(photo) == config.geo_privacy) and config.dont_map_tag.lower() not in photo['tags']:
            m += 1
            for coord in coordinates:
                if longitude == coord[0][0] and latitude == coord[0][1]:
                    coord[1].append([photo['id'], photo['url_sq']])
                    exists = True
            if not exists:
                coordinates.append([[longitude, latitude], [[photo['id'], photo['url_sq']]]])
    e += photos_in_page
    print('Processed photo {0}/{1}'.format(e, total), end='\r')

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
        photo_url = photos_base_url + photo[0]
        thumb_url = photo[1]
        map_file.write("<a href=\\\"{0}\\\" target=\\\"_blank\\\"><img src=\\\"{1}\\\"/></a> ".format(photo_url, thumb_url))
        print('Added {0}/{1}'.format(m, n_markers), end='\r')
    map_file.write("\"]);\n")

print('\nFinished!')

map_file.write("\n        return locations;\n\n    }\n\n</script>\n\n")
map_file.write("\n</body>\n</html>\n\n")
map_file.close()

