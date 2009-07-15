## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <dvdr18@gmail.com>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""Dynamic tile provider for the Mandelbrot set."""

import tempfile
import subprocess
import os

from dynamictileprovider import DynamicTileProvider
from magickconverter import MagickConverter

class MandelTileProvider(DynamicTileProvider):
    """MandelTileProvider objects are used for generating tiles of the
    Mandelbrot set using jrMandel (<http://freshmeat.net/projects/jrmandel/>).

    Constructor: MandelTileProvider(TileCache)
    """
    def __init__(self, tilecache):
        DynamicTileProvider.__init__(self, tilecache)


    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0

    def _load_dynamic(self, tile_id, outfile):
        media_id, tilelevel, row, col = tile_id

        if row < 0 or col < 0 or \
           row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
            ## row,col out of range
            return

        tilesize_units = 4.0 * 2**-tilelevel
        x = col * tilesize_units
        y = row * tilesize_units

        ## the corners of the tile are:
        ## (x1,y1) +----+ (x2,y1)
        ##         |    |
        ## (x1,y2) +----+ (x2,y2)

        x1 = x - 3.0
        y1 = 2.0 - y
        x2 = x1 + tilesize_units
        y2 = y1 - tilesize_units

        tmpfile = tempfile.mkstemp('.pgm')[1]

        bbox = "%f,%f:%f,%f" % (x1,y1,x2,y2)
        size = "%d,%d" % (self.tilesize,self.tilesize)
        max_iterations = 512

        self._logger.debug("calling jrMandel -w %s" % bbox)
        returncode = subprocess.call(['jrMandel',
            '-w', bbox, '-s', size, '-i', str(max_iterations), tmpfile])

        if returncode != 0:
            self._logger.error("conversion failed with return code %d",
                returncode)
        else:
            converter = MagickConverter(tmpfile, outfile)
            converter.start()
            converter.join() ## block until conversion finished

        os.unlink(tmpfile)
