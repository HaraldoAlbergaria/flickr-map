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
import time
import math

from geopy.geocoders import Nominatim


# ================= CONFIGURATION VARIABLES =====================

# Limits
photos_per_page = '500'
max_number_of_pages = 200
max_number_of_photos = max_number_of_pages * int(photos_per_page)
max_number_of_markers = 5000

#geocoder
geo_accuracy = 0.001
geo_zoom = 18

# ===============================================================


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

# get geolocator
try:
    geolocator = Nominatim(user_agent="flickr_map")
except:
    print("ERROR: FATAL: Unable to get geolocator")
    sys.exit()


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

# get user id from user url on config file
user_id = flickr.urls.lookupUser(api_key=api_key, url='flickr.com/people/{}'.format(config.user))['user']['id']

# get the username
user_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['username']['_content']
try:
    real_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['realname']['_content']
    if len(real_name) > 0:
        user_name = real_name
except:
    pass

if len(user_name) > 30:
    user_name = user_name[:30]

# user vatar url
user_avatar = "https://live.staticflickr.com/5674/buddyicons/{}_r.jpg".format(user_id)

# get user's photos base url
photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']

# stores the coordinates fo the markers
coordinates = []

# set script mode (photoset or photostream) and get the total number of photos
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

# current number of photos on photostream
current_total = total

# difference on number of photos from previous run
delta_total = int(total)

# if there is no difference, finish script
if os.path.exists("{}/last_total.py".format(run_path)):
    import last_total
    delta_total = int(current_total) - int(last_total.number)
    if delta_total == 0:
        print('No changes on number of photos since last run.\nAborted.')
        geolocator = None
        sys.exit()

# if difference > 0, makes total = delta_total
# to process only the new photos, otherwise
# (photos were deleted), run in all
# photostream to update the entire map
if delta_total > 0:
    total = delta_total
    if total != delta_total:
        print('{} new photo(s)'.format(total))
else:
    n_deleted = abs(delta_total)
    print('{} photo(s) deleted from photostream.\nThe corresponding markers will also be deleted'.format(n_deleted))


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

    # get photos according to run mode
    if mode == 'photoset':
        page = flickr.photosets.getPhotos(api_key=api_key, user_id=user_id, photoset_id=config.photoset_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photoset']['photo']
    else:
        page = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']

    photos_in_page = len(page)

    # process each photo on page
    for ph in range(0, photos_in_page):

        photo = page[ph]

        # variable to store information if already exist a marker
        # on the same photo's coordinates
        marker_exists = False

        # check if photo can be included on the map (according to privacy settings)
        if isGeoTagged(photo) and (config.geo_privacy == 0 or getGeoPrivacy(photo) == config.geo_privacy) and config.dont_map_tag.lower() not in photo['tags']:

            n_photos += 1

            # get coordinates from photo
            longitude = float(photo['longitude'])
            latitude = float(photo['latitude'])

            # read each markers coordinates and append photo is case
            # there is already a marker on the same coordinate
            for coord in coordinates:
                if longitude == coord[0][0] and latitude == coord[0][1]:
                    coord[1].append([photo['id'], photo['url_sq']])
                    marker_exists = True
                    break

            # create a new marker to be added to the map
            if not marker_exists:
                coordinates.append([[longitude, latitude], [[photo['id'], photo['url_sq']]]])
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
    geolocator = None
    sys.exit()

print('\nAdding marker(s) to map...')

# check if there is javascript file with the markers on map already
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

time.sleep(1)

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
    for coord in range(n_coords-1, -1, -1):

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

# check if there is javascript file with the countries already mapped
if os.path.exists("{}/countries.js".format(run_path)):
    countries_js_file = open("{}/countries.js".format(run_path))
else:
    countries_js_file = open("{}/countries.js".format(run_path), 'w')
    countries_js_file.write("var countries = [\n")
    countries_js_file.write("]\n")
    countries_js_file.close()
    countries_js_file = open("{}/countries.js".format(run_path))

# read the file and store it
countries_js_lines = countries_js_file.readlines()
countries_js_file.close()

# create a python file with the existing countries,
# import it and delete it
countries_py_file = open("{}/countries.py".format(run_path), 'w')
countries_py_file.write("countries = [\n")
for i in range(1, len(countries_js_lines)):
    countries_py_file.write(countries_js_lines[i])
countries_py_file.close()

time.sleep(1)

from countries import countries
os.system("rm {}/countries.py".format(run_path))

# create a new javascript file to store new countries
countries_js_file = open("{}/countries.js".format(run_path), 'w')
countries_js_file.write("var countries = [\n")

# stores the previous values for comparison
prev_latitude = 0
prev_longitude = 0
prev_country_code = ''

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
        photo_url = photos_base_url + photo[0]
        thumb_url = photo[1]
        locations_js_file.write("<a href=\"{0}\" target=\"_blank\"><img src=\"{1}\"/></a> ".format(photo_url, thumb_url))
        n_photos += 1

    # finish marker writing to location file
    locations_js_file.write("</div>\', {}]".format(n_photos))
    if new_markers < n_markers:
        locations_js_file.write(",\n")
    else:
        locations_js_file.write("\n")

    print('Added marker {0}/{1}'.format(new_markers, n_markers), end='\r')

    # if current location is too near of previous location, skip it
    delta_latitude = abs(latitude - prev_latitude)
    delta_longitude = abs(longitude - prev_latitude)
    if delta_latitude > geo_accuracy and delta_longitude > geo_accuracy:
        # get country of the new marker
        try:
            latlong = "{0},{1}".format(latitude,longitude)
            location = geolocator.reverse(latlong, language='en-US', exactly_one=True, zoom=geo_zoom) # zoom='city'
            country_code = location.raw['address']['country_code'].upper()
            country_name = location.raw['address']['country']
        except:
            country_code = ''
            country_name = ''
    else:
        country_code = prev_country_code

    # add country code to countries array
    new_code = True
    for i in range(len(countries)):
        if countries[i][0] == country_code:
            countries[i][2] += 1
            countries[i][3] += n_photos
            new_code = False
            break

    if new_code and country_code != '':
        countries.append([country_code, country_name, 1, n_photos])

    prev_latitude = latitude
    prev_longitude = longitude
    prev_country_code = country_code

# finish script
if new_markers > 0:
    print('')
else:
    print('No new markers were added to the map')

print('Finished!')

locations_js_file.write("]\n")
locations_js_file.close()

for code in range(len(countries)):
    if code < len(countries)-1:
        countries_js_file.write("  {},\n".format(countries[code]))
    else:
        countries_js_file.write("  {}\n".format(countries[code]))

countries_js_file.write("]\n")
countries_js_file.close()

# counts number of markers and photos to write to use file
try:
    locations_js_file = open("{}/locations.js".format(run_path))
    locations_js_lines = locations_js_file.readlines()
    locations_js_file.close()
    locations_py_file = open("{}/locations_.py".format(run_path), 'w')
    locations_py_file.write("locations_ = [\n")
    for i in range(1, len(locations_js_lines)):
        locations_py_file.write(locations_js_lines[i])
    locations_py_file.close()
    time.sleep(1)
    from locations_ import locations_
    os.system("rm {}/locations_.py".format(run_path))
    n_markers = len(locations_)
    n_photos = 0
    for loc in locations_:
        n_photos += loc[2]
except:
    n_markers = ''
    n_photos = ''

user_js_file = open("{}/user.js".format(run_path), 'w')
user_js_file.write("var user_info = {\n")
user_js_file.write("  \"id\": \"{}\",\n".format(user_id))
user_js_file.write("  \"name\": \"{}\",\n".format(user_name))
user_js_file.write("  \"avatar\": \"{}\",\n".format(user_avatar))
user_js_file.write("  \"url\": \"{}\",\n".format(photos_base_url))
user_js_file.write("  \"markers\": {},\n".format(n_markers))
user_js_file.write("  \"photos\": {},\n".format(n_photos))
user_js_file.write("}\n")
user_js_file.close()

# update last_total file with the new value
if os.path.exists("{}/locations.js".format(run_path)):
    os.system("echo \"number = {0}\" > {1}/last_total.py".format(current_total, run_path))
