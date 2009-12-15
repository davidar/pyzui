#!/bin/sh
## script to download the images from ZoomQuilt.org
for i in `seq 1 46`
do
    wget http://nikolaus-baumgarten.de/zoomquilt/steps/$i.jpg
done
