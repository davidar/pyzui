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

"""Class for loading tiles into memory from somewhere other than the local
filesystem (abstract base class)."""

import os

from PyQt4 import QtCore, QtGui

from tileprovider import TileProvider
import tilestore as TileStore

class DynamicTileProvider(TileProvider):
    """DynamicTileProvider objects are used for either generating tiles or
    loading them from a remote host, and then loading them into a TileCache.

    Constructor: DynamicTileProvider(TileCache)
    """
    def __init__(self, tilecache):
        TileProvider.__init__(self, tilecache)


    ## set default values (derived classes may override these values)
    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0 ## width / height

    def _load_dynamic(self, tile_id, outfile):
        """Perform whatever actions necessary to load the tile identified by
        the given tile_id into the location given by outfile.

        _load_dynamic(tuple<string,int,int,int>, string)
        """
        pass


    def _load(self, tile_id):
        filename = TileStore.get_tile_path(
            tile_id, True, filext=self.filext)

        if not os.path.exists(filename):
            ## tile has not been retrieved yet
            self._load_dynamic(tile_id, filename)

        try:
            return QtGui.QImage(filename)
        except Exception:
            self._logger.exception("error loading tile, "
                "assuming it is unavailable")
            return None
