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

"""Dynamic tile provider for the WMS Global Mosaic."""

import urllib
import tempfile
import os

import Image

from dynamictileprovider import DynamicTileProvider
import tilestore as TileStore

class GlobalMosaicTileProvider(DynamicTileProvider):
    """GlobalMosaicTileProvider objects are used for downloading tiles from the
    WMS Global Mosaic server <http://onearth.jpl.nasa.gov/>.

    Constructor: GlobalMosaicTileProvider(TileCache)
    """
    def __init__(self, tilecache):
        DynamicTileProvider.__init__(self, tilecache)


    filext = 'jpg'
    tilesize = 256
    aspect_ratio = 2.0

    base_url = "http://wms.jpl.nasa.gov/wms.cgi?"
    base_params = {
        'request': 'GetMap',
        'layers': 'global_mosaic',
        'srs': 'EPSG:4326',
        'width': 512,
        'height': 512,
        'format': 'image/jpeg',
        'version': '1.1.1',
        'styles': 'visual',
    }

    def __download(self, tile_id):
        """Download the tile identified by tile_id to a temporary file, and
        return the location of that tile.

        __download(tuple<string,int,int,int>) -> string

        Precondition: tile_id is valid
        """
        media_id, tilelevel, row, col = tile_id

        tilesize_degrees = 360.0 * 2**-tilelevel
        x = col * tilesize_degrees
        y = row * tilesize_degrees

        ## the corners of the tile are:
        ## (x1,y2) +----+ (x2,y2)
        ##         |    |
        ## (x1,y1) +----+ (x2,y1)

        x1 = x - 180.0
        y2 = 90.0 - y
        x2 = x1 + tilesize_degrees
        y1 = y2 - tilesize_degrees

        params = self.base_params.copy()
        params['bbox'] = "%f,%f,%f,%f" % (x1, y1, x2, y2)
        query_string = urllib.urlencode(params)
        url = self.base_url + query_string

        fd, tmpfile = tempfile.mkstemp('.jpg')
        os.close(fd)

        self._logger.info("downloading %s", url)
        try:
            urllib.urlretrieve(url, tmpfile)
        except IOError:
            self._logger.exception("cannot reach server")

        return tmpfile


    def __process_big_tile(self, big_tile_id):
        """Download a 512x512 "big tile" identified by big_tile_id, and cut
        four 256x256 tiles from it, saving each of these tiles to the
        TileStore.

        This is required since the server only provides 512x512 and 480x480
        tiles.

        Technically we could provide the original 512x512 tiles, but it's nicer
        for all the tiles to have approximately the same dimensions so that
        memory usage is approximately proportional to the number of tiles
        loaded into memory.

        __process_big_tile(tuple<string,int,int,int>) -> None

        Precondition: tile_id is valid
        """
        media_id, tilelevel, row, col = big_tile_id

        tmpfile = self.__download(big_tile_id)

        try:
            big_tile = Image.open(tmpfile)
        except Exception, e:
            self._logger.exception("unable to load %s" % tmpfile)
        else:
            for x in [0,1]:
                for y in [0,1]:
                    tile= big_tile.crop((x*256, y*256, (x+1)*256, (y+1)*256))
                    tile_id = (media_id, tilelevel+1, row*2 + y, col*2 + x)
                    filename = TileStore.get_tile_path(
                        tile_id, True, filext=self.filext)
                    tile.save(filename)

        try:
            os.unlink(tmpfile)
        except:
            self._logger.exception("unable to unlink temporary file "
                "'%s'" % tmpfile)


    def __process_tilelevel1(self, tile_id):
        """Create the tile identified by tile_id by merging the four sub-tiles
        and resizing to 256x256, and save it to the TileStore.

        __process_tilelevel1(tuple<string,int,int,int>) -> None

        Precondition: the tilelevel component of tile_id is 1
        Precondition: tile_id is valid
        """
        media_id, tilelevel, row, col = tile_id

        self.__process_big_tile((media_id, 1, 0, col))

        tile00 = Image.open(TileStore.get_tile_path(
            (media_id, 2, 0, 0 + col*2), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)
        tile01 = Image.open(TileStore.get_tile_path(
            (media_id, 2, 0, 1 + col*2), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)
        tile10 = Image.open(TileStore.get_tile_path(
            (media_id, 2, 1, 0 + col*2), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)
        tile11 = Image.open(TileStore.get_tile_path(
            (media_id, 2, 1, 1 + col*2), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)

        tile = Image.new('RGB', (256,256))
        tile.paste(tile00, (0,   0, 128, 128))
        tile.paste(tile01, (128, 0, 256, 128))
        tile.paste(tile10, (0,   128, 128, 256))
        tile.paste(tile11, (128, 128, 256, 256))

        filename = TileStore.get_tile_path(
            tile_id, True, filext=self.filext)
        tile.save(filename)


    def __process_tilelevel0(self, media_id):
        """Create the (0,0,0) tile, and save it to the TileStore using the
        media indentifier media_id.

        __process_tilelevel0(string) -> None

        Precondition: tile_id is valid
        """
        self.__process_tilelevel1((media_id, 1, 0, 0))
        self.__process_tilelevel1((media_id, 1, 0, 1))

        tile0 = Image.open(TileStore.get_tile_path(
            (media_id, 1, 0, 0), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)
        tile1 = Image.open(TileStore.get_tile_path(
            (media_id, 1, 0, 1), filext=self.filext)) \
            .resize((128,128), Image.BILINEAR)

        tile = Image.new('RGB', (256,128))
        tile.paste(tile0, (0,   0, 128, 128))
        tile.paste(tile1, (128, 0, 256, 128))

        filename = TileStore.get_tile_path(
            (media_id, 0, 0, 0), True, filext=self.filext)
        tile.save(filename)


    def _load_dynamic(self, tile_id, outfile):
        media_id, tilelevel, row, col = tile_id

        if row < 0 or col < 0:
            ## row,col out of range
            return

        if tilelevel == 0:
            if row > 0 or col > 0:
                ## row,col out of range
                return

            self.__process_tilelevel0(tile_id[0])

        elif tilelevel == 1:
            if row > 0 or col > 1:
                ## row,col out of range
                return

            self.__process_tilelevel1(tile_id)

        else:
            if row > 2**(tilelevel-1) - 1 or \
               col > 2**tilelevel - 1:
                ## row,col out of range
                return

            big_tile_id = (media_id, tilelevel-1, row//2, col//2)
            self.__process_big_tile(big_tile_id)
