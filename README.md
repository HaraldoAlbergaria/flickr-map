# Flickr Map

This script generates a map with markers for all photos in a user's Flickr™ photostream. Click [here](https://haraldofilho.github.io/flickr-map/example/) to see an example.

## Installation

The script was developed to run on _Linux_ systems and need _Python 3.x_ to run. 

To start, open a terminal and execute the following commands:

```
git clone https://github.com/HaraldoFilho/flickr-map.git
cd FlickrMap
```

The script uses *[Flickr](https://www.flickr.com/)™* and *[Mapbox](https://www.mapbox.com/)™* APIs. To get and use these APIs follow the instructions below.

#### Flickr API key
First, install the [_flickrapi_](https://stuvel.eu/flickrapi) package by typing in a terminal:

```
% pip3 install flickrapi
```
Now, get an API key by visiting the [_Flickr_ API key request page](https://www.flickr.com/services/apps/create/apply/).

After that, create a file __api_credentials.py__ with the following code and with the obtained values:

```python
api_key = u'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
api_secret = u'xxxxxxxxxxxxxxx'
user_id = 'XXXXXXXXXXXX'

```

Then, [authenticate](https://stuvel.eu/flickrapi-doc/3-auth.html#authenticating-without-local-web-server) on _Flickr_ by running:

```
% ./auth2flickr.py
```
A web browser will be opened to get the user approval (in a non-graphical environment, just copy and paste the authorization url in any external web browser). After approve, type in the terminal the generated code.

#### Mapbox API access token

Get an access token by visiting the [Create an access token](https://account.mapbox.com/access-tokens/create) page on [Mapbox](https://www.mapbox.com/) website.

Give a name to the token (e.g.: "Flickr Photos Map") and click on "**Create token**".

Then, include the generated code in the file **mapbox_token.js**:

```
var mapbox_token =
'<-- include the mapbox access token here -->'
```

## Configuration

Open the file 'config.py' and edit it as following:

Add the user for whom the map will be generated. It can be the user alias or id.

```
# user alias or id
user = '<-- include user alias or id here -->'
```

The map can be generated for just the photos on a user's photoset. In this case, add a valid photoset id to the _photoset_id_ variable.:
```
# Photoset id:
# If this is defined the map will
# be generated for the photoset
# To generate for entire user's
# photostream, leave it empty
photoset_id = ''
```
If the variable is empty or have a invalid id the map will be generated for the entire user's photostream.

By default, the script will generate the map marking only the public photos on the user's photostream, and those with a geolocation set as visible to anyone. 
This can be changed by editing the variables _photo_privacy_ and/or _geo_privacy_:

```
# Photo Privacy Filter:
# 0 = all photos (public and private)
# 1 = public photos
# 2 = private photos visible to friends
# 3 = private photos visible to family
# 4 = private photos visible to friends & family
# 5 = completely private photos
photo_privacy = 1

# Geolocation Privacy Filter:
# 0 = All
# 1 = Anyone (Recommended)
# 2 = Your contacts
# 3 = Your friends
# 4 = Your family
# 5 = Your friends and family
# 6 = Only you
geo_privacy = 1
```
But only the authenticated user will be able to see the privated photos of your own photostream, i.e. when generating for a different user only the public photos will be visible, independently of this configuration.

There is one more option that can be changed, the variable _dont_map_tag_. To exclude a photo from the map, define a tag in this variable and add the same tag to the photo. 
The default tag is _DontMap_:

```
# Photos with this tag
# won't be included on map
dont_map_tag = 'DontMap'
```

## Usage

Just run the script:

```
% ./generate-map-data.py
```

The output will be like this:

```
Generating map for 'Haraldo Albergaria'
1065 photos in the photostream
Extracting photo coordinates and ids...
Batch 3/3 | 958 photo(s) in 530 marker(s)
Adding marker(s) to map...
530 new marker(s) will be added to the map
Added marker 530/530
Finished!
```
Three files are generated:

- **locations.py**: Contains all the markers information, as coordinates and photos attached to them.
- **countries.py**: List of countries where the photos were taken, including number of places and photos for each place.
- **user.py**: Basic user information, such as user id, name, avatar url, photostream url, number of markers and photos on map.

After the script finishes, open the file **index.html** in a web browser, such as _Google Chrome_ and _Microsoft Edge_ 
(doesn't work on _Internet Explorer_ and has not been tested on other browsers) to see the map.

It is possible to make customizations on the map, by coding them in _Javascript_ in the file **custom.js** and adding any includes, such as styles and additional javascript files in the appropriate field in 'index.html' file:

```
<!-- Begin of customization includes -->

<!-- End of customization includes -->
```

An example of a customization file can be seen [here](https://raw.githubusercontent.com/HaraldoFilho/haraldoalbergaria.page/master/map/custom.js) and its result, where was added a panel with visited countries flags, which zoom in to the country when clicked, can be seen [here](https://haraldoalbergaria.page/map/).
