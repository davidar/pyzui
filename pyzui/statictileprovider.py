## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
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

"""Class for loading tiles from the local tilestore."""

import os

import Image

from tileprovider import TileProvider
import tilestore as TileStore

class StaticTileProvider(TileProvider):
    """StaticTileProvider objects are used for loading tiles from the
    disk-cache into a TileCache.

    Constructor: StaticTileProvider(TileCache)
    """
    def __init__(self, tilecache):
        TileProvider.__init__(self, tilecache)


    def _load(self, tile_id):
        media_id, tilelevel, row, col = tile_id

        maxtilelevel = TileStore.get_metadata(media_id, 'maxtilelevel')
        if tilelevel > maxtilelevel:
            return None

        filename = TileStore.get_tile_path(tile_id)
        try:
            tile = Image.open(filename)
            tile.load()
            return tile
        except IOError:
            return None
