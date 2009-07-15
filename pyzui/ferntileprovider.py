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

"""Dynamic tile provider for Barnsley's fern."""

import random

import Image

from dynamictileprovider import DynamicTileProvider

class FernTileProvider(DynamicTileProvider):
    """FernTileProvider objects are used for generating tiles of Barnsley's
    fern iterated function system.

    Constructor: FernTileProvider(TileCache)
    """
    def __init__(self, tilecache):
        DynamicTileProvider.__init__(self, tilecache)


    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0

    max_iterations = 50000
    max_points = 10000
    transformations = [
        ## (probability, (a, b, c, d, e, f))
        ## x_n+1 = a*x_n + b*y_n + c
        ## y_n+1 = d*x_n + e*y_n + f

        ## for details about the transformations, see:
        ## <http://en.wikipedia.org/wiki/Barnsley's_fern>
        ## <http://books.google.com/books?id=oh7NoePgmOIC
        ##  &printsec=frontcover#PPA86,M1>
        ## <http://mathworld.wolfram.com/BarnsleysFern.html>
        ## <http://www.home.aone.net.au/~byzantium/ferns/fractal.html>

        ## rachis
        (0.01, ( 0.00,  0.00,  0.00,  0.00,  0.16,  0.00)),

        ## left hand first pinna
        (0.07, ( 0.20, -0.26,  0.00,  0.23,  0.22,  1.60)),

        ## right hand first pinna
        (0.07, (-0.15,  0.28,  0.00,  0.26,  0.24,  0.44)),

        ## body of fern
        (0.85, ( 0.85,  0.04,  0.00, -0.04,  0.85,  1.60)),
    ]
    color = (100, 170, 0)

    def __choose_transformation(self):
        """Randomly choose a transformation based on the probability of each
        transformation being chosen.

        __choose_transformation() -> tuple<float,float,float,float,float,float>
        """
        n = random.uniform(0,1)
        for probability, transformation in self.transformations:
            if n <= probability:
                break
            else:
                n -= probability
        return transformation


    def __transform(self, x, y):
        """Randomly choose a transformation and apply it to x and y, returning
        the result as a tuple.

        __transform(float, float) -> tuple<float,float>
        """
        t = self.__choose_transformation()
        x_new = t[0]*x + t[1]*y + t[2]
        y_new = t[3]*x + t[4]*y + t[5]
        return (x_new,y_new)


    def __draw_point(self, tile, x, y, tilesize_units):
        """Draw the given point on the given tile.

        __draw_point(Image, float, float, float) -> None

        Precondition: 0.0 <= x <= tilesize_units
        Precondition: 0.0 <= y <= tilesize_units
        """

        x = x * self.tilesize / tilesize_units
        x = min(int(x), self.tilesize-1)
        y = y * self.tilesize / tilesize_units
        y = min(int(self.tilesize - y), self.tilesize-1)

        tile.putpixel((x,y), self.color)


    def _load_dynamic(self, tile_id, outfile):
        media_id, tilelevel, row, col = tile_id

        if row < 0 or col < 0 or \
           row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
            ## row,col out of range
            return

        tilesize_units = 10.0 * 2**-tilelevel
        x = col * tilesize_units
        y = row * tilesize_units

        ## the corners of the tile are:
        ## (x1,y2) +----+ (x2,y2)
        ##         |    |
        ## (x1,y1) +----+ (x2,y1)

        x1 = x - 5.0
        y2 = 10.0 - y
        x2 = x1 + tilesize_units
        y1 = y2 - tilesize_units

        tile = Image.new('RGB', (self.tilesize,self.tilesize))

        num_points = 0

        x = 0.0
        y = 0.0
        for i in xrange(self.max_iterations):
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.__draw_point(
                    tile, x-x1, y-y1, tilesize_units)

                num_points += 1
                if num_points > self.max_points:
                    break

            x,y = self.__transform(x,y)

        tile.save(outfile)
