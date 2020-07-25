#!/bin/bash

mkdir $1
cd $1
ln -s ../../api_credentials.py .
ln -s ../mapbox_token .
ln -s ../../header.html .
ln -P ../generate-map.py
echo "# group alias or id" > config.py
echo "group = '$1'" >> config.py

