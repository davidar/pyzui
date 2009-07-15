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

"""Dynamic tile provider for OpenStreetMap."""

import urllib

from dynamictileprovider import DynamicTileProvider

class OSMTileProvider(DynamicTileProvider):
    """OSMTileProvider objects are used for downloading tiles from
    OpenStreetMap (<http://openstreetmap.org/>).

    Constructor: OSMTileProvider(TileCache)
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

        url = "http://tile.openstreetmap.org/%d/%d/%d.png" \
            % (tilelevel, col, row)

        self._logger.info("downloading %s", url)
        try:
            urllib.urlretrieve(url, outfile)
        except IOError:
            self._logger.exception("cannot reach server")
