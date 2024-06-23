#!/usr/bin/python3

#########################################################################################
## This code was extracted and modified from the following address:                    ##
## https://stuvel.eu/flickrapi-doc/3-auth.html#authenticating-without-local-web-server ##
#########################################################################################

import flickrapi
import api_credentials
import subprocess
import webbrowser
import time

api_key = api_credentials.api_key
api_secret = api_credentials.api_secret
user_id = api_credentials.user_id

flickr = flickrapi.FlickrAPI(api_key, api_secret)

proc = subprocess.Popen(["runlevel"], stdout=subprocess.PIPE, shell=True)
(runlevel, err) = proc.communicate()
runlevel = str(runlevel).replace("b\'N ","").replace("\\n\'","")

print('Authenticate')

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='write'):

    print('Not have a valid token')

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='write')
    print("Authorization URL: {}".format(authorize_url))
    if runlevel == '5':
        webbrowser.open_new_tab(authorize_url)
        time.sleep(1)

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = str(input('Verifier code: '))

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

