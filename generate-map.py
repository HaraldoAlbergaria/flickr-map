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
max_number_of_pages = 500
max_number_of_photos = 5000


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

# get user id from user url on config file
user_id = flickr.urls.lookupUser(api_key=api_key, url='flickr.com/people/{}'.format(config.user))['user']['id']

# get the username
user_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['username']['_content']

# get user's photos base url
coordinates = []
photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']

print('###################### Flickr Map ######################')

try:
    photos = flickr.photosets.getPhotos(api_key=api_key, user_id=user_id, photoset_id=config.photoset_id, privacy_filter=config.photo_privacy, per_page=photos_per_page)
    npages = int(photos['photoset']['pages'])
    total = int(photos['photoset']['total'])
    print('Generating map for \'{}\''.format(user_name))
    print('Photoset \'{}\''.format(photos['photoset']['title']))
    print('{} photos in the photoset'.format(total))
    mode = 'photoset'
except:
    photos = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, per_page=photos_per_page)
    npages = int(photos['photos']['pages'])
    total = int(photos['photos']['total'])
    if config.photoset_id != '':
        print('ERROR: Invalid photoset id.\nSwitching to user\'s photostream...')
    print('Generating map for \'{}\''.format(user_name))
    print('{} photos in the photostream'.format(total))
    mode = 'photostream'

if os.path.exists("{}/last_total.py".format(run_path)):
    import last_total
    if total == last_total.number:
        print('No changes on number of photos since last run.\nAborted.')
        sys.exit()

os.system("echo \"number = {0}\" > {1}/last_total.py".format(total, run_path))

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
        map_file.write("  <title>{} | Photos Map</title>\n".format(user_name))


print('Extracting photo coordinates and ids...')

n = 0
e = 0
m = 0

if npages > max_number_of_pages:
    npages = max_number_of_pages
    total = max_number_of_pages * int(photos_per_page);
    print("Extracting for the last {} photos".format(total))

for pg in range(1, npages+1):
    if mode == 'photoset':
        page = flickr.photosets.getPhotos(api_key=api_key, user_id=user_id, photoset_id=config.photoset_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photoset']['photo']
    else:
        page = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']
    photos_in_page = len(page)
    for ph in range(0, photos_in_page):
        n += 1
        photo = page[ph]
        exists = False
        if isGeoTagged(photo) and (config.geo_privacy == 0 or getGeoPrivacy(photo) == config.geo_privacy) and config.dont_map_tag.lower() not in photo['tags']:
            m += 1
            for coord in coordinates:
                if photo['longitude'] == coord[0][0] and photo['latitude'] == coord[0][1]:
                    coord[1].append([photo['id'], photo['url_sq']])
                    exists = True
            if not exists:
                coordinates.append([[photo['longitude'], photo['latitude']], [[photo['id'], photo['url_sq']]]])
        if m >= max_number_of_photos:
            break
    e += photos_in_page
    print('Processed photo {0}/{1} | {2} photos on map'.format(e, total, m), end='\r')
    if m >= max_number_of_photos:
        print("\nMaximum number of photos on map reached!")
        break

if m == 0:
    if mode == 'photoset':
        print('No geo tagged photo on the user photoset\nMap not generated')
    else:
        print('No geo tagged photo on the user photostream\nMap not generated')
    sys.exit()

print('{} photos will be attached to markers'.format(m))
print('Adding markers to map...')

m = 0
n_markers = len(coordinates)
for marker_info in coordinates:
    m += 1
    longitude = marker_info[0][0]
    latitude = marker_info[0][1]
    map_file.write("            [[{0}, {1}], \"".format(longitude, latitude))
    for photo in marker_info[1]:
        photo_url = photos_base_url + photo[0]
        thumb_url = photo[1]
        map_file.write("<a href=\\\"{0}\\\" target=\\\"_blank\\\"><img src=\\\"{1}\\\"/></a> ".format(photo_url, thumb_url))
        print('Added {0}/{1}'.format(m, n_markers), end='\r')
    map_file.write("\"],\n")

print('\nFinished!')

map_file.write("        ]\n\n        return locations;\n\n    }\n\n</script>\n\n")
map_file.write("\n</body>\n</html>\n\n")
map_file.close()

