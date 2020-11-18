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
import random

from countries_info import getCountryInfo


# ================= CONFIGURATION VARIABLES =====================

# Limits
photos_per_page = '500'
max_number_of_pages = 200
max_number_of_photos = max_number_of_pages * int(photos_per_page)


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
    if photo['latitude'] == 0 and photo['longitude'] == 0 and photo['accuracy'] == 0:
        return False
    return True

# Get the number of markers on locations dictionary
def getNumberOfMarkers(dict):
    n = 0
    for key in dict:
        n += len(dict[key])
    return n

# Get the number of photos on locations dictionary
def getNumberOfPhotos(dict):
    p = 0
    for key in dict:
        for marker in dict[key]:
            p += len(marker[1])
    return p

# Update last_total file with the new value
def updateLastTotalFile(run_path, current_total):
    if os.path.exists("{}/locations.py".format(run_path)):
        os.system("echo \"number = {0}\" > {1}/last_total.py".format(current_total, run_path))


#===== MAIN CODE ==============================================================#

user_alias = config.user

# get user id from user url on config file
try:
    user_id = flickr.urls.lookupUser(api_key=api_key, url='flickr.com/people/{}'.format(user_alias))['user']['id']
except:
    print("ERROR: FATAL: Unable to get user id")
    sys.exit()

# get the username
try:
    user_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['username']['_content']
except:
    print("ERROR: FATAL: Unable to get user name")
    sys.exit()

try:
    real_name = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['realname']['_content']
    if len(real_name) > 0:
        user_name = real_name
except:
    pass

if len(user_name) > 30:
    user_name = user_name[:30]

# user avatar url
user_avatar = "https://live.staticflickr.com/5674/buddyicons/{}_r.jpg".format(user_id)
os.system("wget -q {}".format(user_avatar))
if os.path.exists("{}_r.jpg".format(user_id)):
    os.system("rm {}_r.jpg".format(user_id))
else:
    user_avatar = "../../icons/photographer.svg"

# get user's photos base url
try:
    photos_base_url = flickr.people.getInfo(api_key=api_key, user_id=user_id)['person']['photosurl']['_content']
except:
    print("ERROR: FATAL: Unable to get photos base url")
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
        npages = int(photos['photos']['pages'])
        total = int(photos['photos']['total'])
    except:
        print("ERROR: FATAL: Unable to get photos")
        sys.exit()

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
        sys.exit()

# if difference > 0, makes total = delta_total
# to process only the new photos, otherwise
# (photos were deleted), run in all
# photostream to update the entire map
if delta_total > 0:
    if total != delta_total:
        total = delta_total
        print('{} new photo(s) added'.format(total))
else:
    n_deleted = abs(delta_total)
    if os.path.exists("{}/locations.py".format(run_path)):
        os.system("rm {}/locations.py".format(run_path))
    if os.path.exists("{}/countries.py".format(run_path)):
        os.system("rm {}/countries.py".format(run_path))
    if os.path.exists("{}/user.py".format(run_path)):
        os.system("rm {}/user.py".format(run_path))
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

# counts the number of processed photos
proc_photos = 0

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

            # read each markers coordinates and append photo in case
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

        proc_photos += 1

        # stop processing photos if any limit was reached
        if proc_photos >= total or proc_photos >= max_number_of_photos:
           break

    print('Batch {0}/{1} | {2} photo(s) in {3} marker(s)'.format(pg, npages, n_photos, n_markers), end='\r')

    # stop processing pages if any limit was reached
    if n_photos >= total:
        break
    if n_photos >= max_number_of_photos:
        print("\nMaximum number of photos on map reached!", end='')
        break

print('\nAdding marker(s) to map...')

# check if there is a file with the markers on map already
# and import it otherwise created a new variable
if os.path.exists("{}/locations.py".format(run_path)):
    from locations import locations_dict
else:
    locations_dict = dict()

# get the number of markers (locations) already on map
n_markers = getNumberOfMarkers(locations_dict)
if n_markers > 0:
    print('Map already has {} marker(s)'.format(n_markers))

# check if there is file with the countries already mapped
if os.path.exists("{}/countries.py".format(run_path)):
    from countries import countries_dict
else:
    countries_dict = dict()


# counts the number of new photos added to markers
new_photos = 0

# iterate on each country
for country in locations_dict:

    # get markers for country
    country_markers = locations_dict[country]

    # iterate on each marker
    for marker in country_markers:

        # get info for photos on marker
        photos_info = marker[1]
        #n_photos = len(photos_info)

        # get number of photos (coordinates) to be added to map
        n_coords = len(coordinates)

        # iterate over each coordinate
        for coord in range(n_coords-1, -1, -1):

            # if there is already a marker on the same coordinate
            if coordinates[coord][0] == marker[0]:

                # read each photo already on the marker
                for photo in coordinates[coord][1]:
                    photo_id = photo[0]
                    thumb_url = photo[1]

                    # if the photo is not already on marker, add the photo to it
                    if [photo_id, thumb_url] not in photos_info:
                        photos_info.append([photo_id, thumb_url])
                        new_photos += 1

                # remove photo info from
                # coordinates to be added
                coordinates.pop(coord)

        # update the number of photos on marker
        marker[1] = photos_info

if new_photos > 0:
    print('Added {} new photo(s) to existing markers'.format(new_photos))

# reverse the coordinates order so
# the newest ones go to the end
coordinates.reverse()

# check if there is remaining markers to be added
n_markers = len(coordinates)
if n_markers > 0:
    print('{} new marker(s) will be added to the map'.format(n_markers))

new_markers = 0

# iterate over each marker to be added
for marker_info in coordinates:

    new_markers += 1

    # get coordinates of the new marker
    longitude = float(marker_info[0][0])
    latitude = float(marker_info[0][1])

    # get country code and name
    try:
        country_info = getCountryInfo(latitude, longitude)
        country_code = country_info[0]
        country_name = country_info[1]
    except:
        pass

    # add country to countries dictionary
    if country_code != '':
        if country_code not in countries_dict:
            countries_dict[country_code] = [country_name, 0 , 0]
        else:
            if countries_dict[country_code][0] == '':
                countries_dict[country_code][0] = country_name

    # add country to locations dictionary
    if country_code not in locations_dict:
        locations_dict[country_code] = [marker_info]
    else:
        locations_dict[country_code].append(marker_info)

    print('Added marker {0}/{1}'.format(new_markers, n_markers), end='\r')

# finish script
if new_markers > 0:
    print('')
else:
    print('No new markers were added to the map')

print('Finished!')

# write countries dictionary to file
countries_file = open("{}/countries.py".format(run_path), 'w')
countries_file.write("countries_dict = {\n")

i = 0
for code in countries_dict:
    markers = locations_dict[code]
    n_markers = len(markers)
    n_photos = 0
    for marker in markers:
        n_photos += len(marker[1])

    countries_dict[code][1] = n_markers
    countries_dict[code][2] = n_photos

    if i < len(countries_dict)-1:
        countries_file.write("  \'{0}\': {1},\n".format(code, countries_dict[code]))
    else:
        countries_file.write("  \'{0}\': {1}\n".format(code, countries_dict[code]))
    i += 1

countries_file.write("}\n")
countries_file.close()

# write markers information (locations) to file
locations_file = open("{}/locations.py".format(run_path), 'w')
locations_file.write("locations_dict = {\n")

i = 1
for country_code in locations_dict:
    locations_file.write("  \'{}\': [\n".format(country_code))
    random.shuffle(locations_dict[country_code])
    for coord in range(len(locations_dict[country_code])):
        locations_file.write("    {}".format(locations_dict[country_code][coord]))
        if coord < len(locations_dict[country_code])-1:
            locations_file.write(",\n")
        else:
            locations_file.write("\n  ]")
    if i < len(locations_dict):
        locations_file.write(",\n")
    else:
        locations_file.write("\n")
    i += 1

locations_file.write("}\n")
locations_file.close()

# get total number of markers and photos to write to user file
n_markers = getNumberOfMarkers(locations_dict)
n_photos = getNumberOfPhotos(locations_dict)

# write user information to file
user_file = open("{}/user.py".format(run_path), 'w')
user_file.write("user_info = {\n")
user_file.write("  \'id\': \'{}\',\n".format(user_id))
user_file.write("  \'alias\': \'{}\',\n".format(user_alias))
user_file.write("  \'name\': \'{}\',\n".format(user_name))
user_file.write("  \'avatar\': \'{}\',\n".format(user_avatar))
user_file.write("  \'url\': \'{}\',\n".format(photos_base_url))
user_file.write("  \'markers\': {},\n".format(n_markers))
user_file.write("  \'photos\': {}\n".format(n_photos))
user_file.write("}\n")
user_file.close()

updateLastTotalFile(run_path, current_total)
