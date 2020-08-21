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

#from geopy.geocoders import Nominatim
from countries_info import getCountryInfo


# ================= CONFIGURATION VARIABLES =====================

# Limits
photos_per_page = '500'
max_number_of_pages = 200
max_number_of_photos = max_number_of_pages * int(photos_per_page)
max_number_of_markers = 5000


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
    if 'geo_is_public' in photo:
        return True
    return False


#===== MAIN CODE ==============================================================#

# get user id from user url on config file
try:
    user_id = flickr.urls.lookupUser(api_key=api_key, url='flickr.com/people/{}'.format(config.user))['user']['id']
except:
    print("ERROR: FATAL: Unable to get user id")
    geolocator = None
    sys.exit()

# get the username
try:
    user_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['username']['_content']
    real_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['realname']['_content']
    if len(real_name) > 0:
        user_name = real_name
except:
    print("ERROR: FATAL: Unable to get user name")
    geolocator = None
    sys.exit()

if len(user_name) > 30:
    user_name = user_name[:30]

# user avatar url
user_avatar = "https://live.staticflickr.com/5674/buddyicons/{}_r.jpg".format(user_id)
os.system("wget -q {}".format(user_avatar))
if os.path.exists("{}_r.jpg".format(user_id)):
    os.system("rm {}_r.jpg".format(user_id))
else:
    user_avatar = "../photographer.svg"

# get user's photos base url
try:
    photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']
except:
    print("ERROR: FATAL: Unable to get photos base url")
    geolocator = None
    sys.exit()

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
    try:
        photos = flickr.people.getPublicPhotos(api_key=api_key, user_id=user_id, per_page=photos_per_page)
    except:
        print("ERROR: FATAL: Unable to get photos")
        geolocator = None
        sys.exit()

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
    try:
        if mode == 'photoset':
            page = flickr.photosets.getPhotos(api_key=api_key, user_id=user_id, photoset_id=config.photoset_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photoset']['photo']
        else:
            page = flickr.people.getPhotos(api_key=api_key, user_id=user_id, privacy_filter=config.photo_privacy, extras='geo,tags,url_sq', page=pg, per_page=photos_per_page)['photos']['photo']
    except:
        print("ERROR: FATAL: Unable to get photos")
        geolocator = None
        sys.exit()

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

# check if there is a file with the markers on map already
# and import it otherwise created a new variable
if os.path.exists("{}/locations.py".format(run_path)):
    from locations import locations
else:
    locations = []

# create a new location file or overwrite existing one
locations_file = open("{}/locations.py".format(run_path), 'w')
locations_file.write("locations = [\n")

# get the number of markers (locations) already on map
n_locations = len(locations)
if n_locations > 0:
    print('Map already has {} marker(s)'.format(n_locations))

# check if there is file with the countries already mapped
if os.path.exists("{}/countries.py".format(run_path)):
    from countries import countries
else:
    countries = dict()

countries_file = open("{}/countries.py".format(run_path), 'w')
countries_file.write("countries = {\n")

# counts the number of new photos added to markers
new_photos = 0

# process each marker info already on map
for loc in range(n_locations):

    # get info for photos on marker
    photos_info = locations[loc][2]
    n_photos = int(locations[loc][3])

    # get number of photos (coordinates) to be added to map
    n_coords = len(coordinates)

    # iterate over each coordinate
    for coord in range(n_coords-1, -1, -1):

        # if there is already a marker on the same coordinate
        if coordinates[coord][0] == locations[loc][0]:

            # read each photo already on the marker
            for photo in coordinates[coord][1]:
                photo_id = photo[0]
                thumb_url = photo[1]

                # if the photo is not already on marker, add the photo to it
                if [photo_id, thumb_url] not in photos_info:
                    photos_info.append([photo_id, thumb_url])
                    new_photos += 1
                    countries[locations[loc][1]][2] += 1

            # remove photo info from
            # coordinates to be added
            coordinates.pop(coord)

    # update the number of photos on marker
    locations[loc][2] = photos_info
    locations[loc][3] = len(photos_info)
    locations_file.write("    {}".format(locations[loc]))

    if len(coordinates) > 0:
        locations_file.write(",\n")
    else:
        locations_file.write("\n")


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
    try:
        country_info = getCountryInfo(latitude, longitude)
        country_code = country_info[0]
        country_name = country_info[1]
        if country_code not in countries:
            countries[country_code] = [country_name, 0 , 0]
    except:
        country_code = ''
        country_name = ''

    # write it to locations file
    locations_file.write("    [[{0}, {1}], \'{2}\', [".format(longitude, latitude, country_code))

    # counts the number of photos
    n_photos = 0

    # iterate over each photo
    for photo in marker_info[1]:

        # add photo to marker, writing it to locations file
        locations_file.write("[\'{0}\', \'{1}\']".format(photo[0], photo[1]))
        n_photos += 1

        if n_photos < len(marker_info[1]):
            locations_file.write(", ")

    # finish marker writing to location file
    locations_file.write("], {}]".format(n_photos))
    if new_markers < n_markers:
        locations_file.write(",\n")
    else:
        locations_file.write("\n")

    if country_code != '':
        countries[country_code][1] += 1
        countries[country_code][2] += n_photos

    print('Added marker {0}/{1}'.format(new_markers, n_markers), end='\r')

# finish script
if new_markers > 0:
    print('')
else:
    print('No new markers were added to the map')

print('Finished!')

locations_file.write("]\n")
locations_file.close()

i = 0
for code in countries:
    if i < len(countries):
        countries_file.write("  \'{0}\': {1},\n".format(code, countries[code]))
    else:
        countries_file.write("  \'{0}\': {1}\n".format(code, countries[code]))

countries_file.write("}\n")
countries_file.close()

# counts number of markers and photos to write to user file
n_markers = len(locations)
n_photos = 0
for loc in locations:
    n_photos += loc[3]

user_js_file = open("{}/user.js".format(run_path), 'w')
user_js_file.write("var user_info = {\n")
user_js_file.write("  \"id\": \"{}\",\n".format(user_id))
user_js_file.write("  \"name\": \"{}\",\n".format(user_name))
user_js_file.write("  \"avatar\": \"{}\",\n".format(user_avatar))
user_js_file.write("  \"url\": \"{}\",\n".format(photos_base_url))
user_js_file.write("  \"markers\": {},\n".format(n_markers))
user_js_file.write("  \"photos\": {}\n".format(n_photos))
user_js_file.write("}\n")
user_js_file.close()

# update last_total file with the new value
if os.path.exists("{}/locations.py".format(run_path)):
    os.system("echo \"number = {0}\" > {1}/last_total.py".format(current_total, run_path))
