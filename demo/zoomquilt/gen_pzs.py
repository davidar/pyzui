#!/usr/bin/python
## generate the .pzs file for zoomquilt

import os
import urllib

path = os.path.abspath(os.path.dirname(__file__))

print "46.0\t128.0\t128.0"
for i in xrange(1,47):
    print "TiledMediaObject\t%s\t%s\t%s\t%s" % \
        (os.path.join(urllib.quote(path), str(i)+'.jpg'),
         -1.0*i, -128.0/(2**i), -96.0/(2**i))
for i in xrange(47,93):
    print "TiledMediaObject\t%s\t%s\t%s\t%s" % \
        (os.path.join(urllib.quote(path), str(i-46)+'.jpg'),
         -1.0*i, -128.0/(2**i), -96.0/(2**i))
