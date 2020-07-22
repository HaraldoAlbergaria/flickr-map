#!/usr/bin/python3

# This script generates a html file of all the photos on the
# Flickr user's photostream, that can be viewed in a web browser as a map
#
# Author: Haraldo Albergaria
# Date  : Jul 21, 2020
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import flickrapi
import api_credentials
import json
import config
import os


# Credentials
api_key = api_credentials.api_key
api_secret = api_credentials.api_secret
user_id = api_credentials.user_id

# Flickr api access
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

# Script run path
run_path = config.run_path


#===== MAIN CODE ==============================================================#

#os.system('cp {0}header.html {0}map.html'.format(run_path))

header_file = open("{}header.html".format(run_path))
header = header_file.readlines()
header_file.close()

mapbox_token_file = open("{}mapbox_token".format(run_path))
mapbox_token_lines = mapbox_token_file.readlines()
mapbox_token_file.close()

mapbox_token = mapbox_token_lines[0].replace('\n','')

map_file = open("{}map.html".format(run_path), 'w')

for line in header:
    if line == '    mapboxgl.accessToken = \'\';\n':
        map_file.write("    mapboxgl.accessToken = \'{}\';\n".format(mapbox_token))
    else:
        map_file.write(line)

photos = flickr.photos.getWithGeoData(api_key=api_key, user_id=user_id, per_page='500')

npages = int(photos['photos']['pages'])
total = int(photos['photos']['total'])

coordinates = []
photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']

print('Extracting photos coordinates and ids...')

n = 0
for pg in range(1, npages+1):
    page = flickr.photos.getWithGeoData(api_key=api_key, user_id=user_id, page=pg, per_page='500', extras='geo,tags,url_sq')['photos']['photo']
    photos_in_page = len(page)
    for ph in range(0, photos_in_page):
        n = n + 1
        photo = page[ph]
        exists = False
        if photo['ispublic'] == 1 and photo['geo_is_public'] == 1 and config.dont_map_tag.lower() not in photo['tags']:
            for coord in coordinates:
                if photo['longitude'] == coord[0][0] and photo['latitude'] == coord[0][1]:
                    coord[1].append([photo['id'], photo['url_sq']])
                    exists = True
            if not exists:
                coordinates.append([[photo['longitude'], photo['latitude']], [[photo['id'], photo['url_sq']]]])

print('Adding markers...')

m = 0
n_markers = len(coordinates)
for marker_info in coordinates:
    m = m + 1
    longitude = marker_info[0][0]
    latitude = marker_info[0][1]
    map_file.write("        locations.push([[{0}, {1}], \"".format(longitude, latitude))
    for photo in marker_info[1]:
        photo_url = photos_base_url + photo[0]
        thumb_url = photo[1]
        map_file.write("<a href=\\\"{0}\\\" target=\\\"_blank\\\"><img src=\\\"{1}\\\"/></a> ".format(photo_url, thumb_url))
    map_file.write("\"]);\n")

map_file.write("\n        return locations;\n\n    }\n\n</script>\n\n")
map_file.write("\n</body>\n</html>\n\n")
map_file.close()

print('Finished!')

