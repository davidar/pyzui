To download and generate the ZoomQuilt[1] demo, enter the zoomquilt directory
and run `./download.sh && ./gen_pzs.py > zoomquilt.pzs`.

"Paradox", which was displayed in the screencast, can be downloaded from [2].
However, there's a bug in imagemagick (it doesn't convert TIFF to PPM properly)
which means that the image will need to be converted to another format, such as
JPEG or PNG, before loading it into the application.

maps.pzs demonstrates some of the mapping capabilities of the application. In
order to use this scene, [3] must be downloaded, and the last line of maps.pzs
edited so that /path/to/world.topo.bathy.200407.3x21600x10800.jpg is replaced
with the absolute location of the file.

loremipsum.net.pzs contains a mockup of how a ZUI can be applied to web-
browsing, using loremipsum.net[4] as an example. To navigate the site, simply
zoom into the thumbnails next to the appropriate links. On the front page,
links are available for "All caps version" and "What is 'lorem ipsum' all
about?", and within the latter link, the text under "English translations" is
also linked.

[1] http://zoomquilt.org/
[2] http://paradox.rambisyouth.com/lossless/paradox.tif
[3] http://earthobservatory.nasa.gov/Features/BlueMarble/images_bmng/2km/world.topo.bathy.200407.3x21600x10800.jpg
[4] http://loremipsum.net/
