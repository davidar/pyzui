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

"""Threaded image tiler (abstract base class)."""

from __future__ import with_statement

from threading import Thread
import os
import math
import logging
import shutil

import tilestore as TileStore
import tile as Tile

class Tiler(Thread):
    """Tiler objects are used for tiling images.

    Constructor: Tiler(string[, string[, string[, int]]])
    """
    def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
        """Create a new Tiler for tiling the media given by `media_id` with the
        image given by `infile`.

        If `media_id` is omitted, it will be set to `infile`.

        Tiles will be saved in the format indicated by `filext` and with the
        dimensions given by `tilesize`.
        """
        Thread.__init__(self)

        self._infile = infile
        self.__filext = filext
        self.__tilesize = tilesize

        if media_id:
            self.__media_id = media_id
        else:
            self.__media_id = infile

        self.__outpath = TileStore.get_media_path(self.__media_id)

        self.__progress = 0.0

        self.__logger = logging.getLogger(str(self))

        self.error = None


    def _scanline(self):
        """Return string containing pixels of the next row.

        _scanline() -> string
        """
        pass


    def __savetile(self, tile, tilelevel, row, col):
        """Save the given tile to disk.

        __save(Tile, int, int, int) -> None
        """
        tile_id = (self.__media_id, tilelevel, row, col)
        filename = TileStore.get_tile_path(
            tile_id, True, self.__outpath, self.__filext)
        tile.save(filename)

        self.__progress += 1.0/self.__numtiles
        self.__logger.info("%3d%% tiled", int(self.__progress*100))


    def __load_row_from_file(self, row):
        """Load the requested row from the image file.

        __load_row_from_file(int) -> list<Tile>

        Precondition: calls to this function must take consecutive values for
        row i.e. the first call must have row=0, then the next call must have
        row=1, etc.
        """
        if row >= self.__numtiles_down_total:
            ## requested row does not exist
            return None

        tiles = [''] * self.__numtiles_across_total

        if row == self.__numtiles_down_total-1:
            ## we're in the bottom row
            tileheight = self.__bottom_tiles_height
        else:
            tileheight = self.__tilesize

        for pixrow in xrange(tileheight):
            scanline = self._scanline()
            if scanline == '':
                ## we've gone past the end of the file
                raise IOError("less data in image than "
                    "reported by the header")
            for i in xrange(self.__numtiles_across_total):
                p = self._bytes_per_pixel * i * self.__tilesize
                if i == self.__numtiles_across_total-1:
                    ## last tile in row
                    tiles[i] += scanline[p:]
                else:
                    tiles[i] += \
                        scanline[p : p + self._bytes_per_pixel*self.__tilesize]

        for i in xrange(self.__numtiles_across_total):
            if i == self.__numtiles_across_total-1:
                ## last tile in row
                tiles[i] = Tile.fromstring(tiles[i],
                    self.__right_tiles_width, tileheight)
            else:
                tiles[i] = Tile.fromstring(tiles[i],
                    self.__tilesize, tileheight)

        return tiles


    def __mergerows(self, row_a, row_b=None):
        """Merge blocks of 4 tiles (or blocks of 2 if row_b is None) into a
        single tile.

        __mergerows(list<Tile>[, list<Tile>]) -> list<Tile>
        """
        if not row_a:
            ## requested row does not exist
            return None
        if not row_b:
            ## make a fake row_b
            row_b = [None] * len(row_a)

        if len(row_a) % 2 == 1:
            ## buffer rows to make them even
            row_a.append(None)
            row_b.append(None)

        tiles = []
        while row_a:
            tiles.append(Tile.merged(
                row_a.pop(0), row_a.pop(0),
                row_b.pop(0), row_b.pop(0)))

        return tiles


    def __tiles(self, tilelevel=0, row=0):
        """Recursive function which retrieves the tiles in the given row, saves
        them, scales each dimension by 1/2, and then returns them as a list.

        As the function is recursive, all higher-resolution sub-tiles contained
        within the requested tile will be saved in the process. Therefore,
        requesting row 0 from tilelevel 0 will result in the entire image being
        tiled.

        __tiles(int, int) -> list<Tile>
        """
        if tilelevel == self.__maxtilelevel:
            tiles = self.__load_row_from_file(row)
        else:
            ## load the requested row by merging sub-tiles from
            ## tilelevel (tilelevel+1)
            row_a = self.__tiles(tilelevel+1, row*2)
            row_b = self.__tiles(tilelevel+1, row*2+1)
            tiles = self.__mergerows(row_a, row_b)

        if not tiles:
            ## requested row does not exist
            return None

        for i in xrange(len(tiles)):
            self.__savetile(tiles[i], tilelevel, row, i)
            tiles[i] = tiles[i].resize(tiles[i].size[0]/2, tiles[i].size[1]/2)

        return tiles


    def __calculate_maxtilelevel(self):
        """Calculate the maxtilelevel, which is the smallest non-negative
        integer such that:
        tilesize * (2**maxtilelevel) >= max(width, height)
        i.e. if tilelevel 0 contains a single tile, then the tiles in
        maxtilelevel are the same resolution as the input image

        __calculate_maxtilelevel() -> int
        """
        maxdim = max(self._width, self._height)
        if maxdim <= self.__tilesize:
            ## entire image can be contained within
            ## the (0,0,0) tile
            return 0
        else:
            ## above equation can be rearranged to
            ##   maxtilelevel >= log_2(maxdim) - log_2(tilesize)
            ## and using ceil to find smallest integer maxtilelevel
            ## satisfying this equation
            maxtilelevel = int(math.ceil(
                math.log(maxdim,2)
                 - math.log(self.__tilesize,2)))

            ## check if rounding errors caused maxtilelevel to be
            ## mistakenly rounded up to the next integer
            ## i.e. if maxtilelevel-1 also fulfills the req'ment
            if self.__tilesize * (2**(maxtilelevel-1)) >= maxdim:
                maxtilelevel -= 1

            return maxtilelevel


    def __calculate_numtiles(self):
        """Calculate the total number of tiles required.

        __calculate_numtiles() -> int
        """
        numtiles = 0
        for tilelevel in xrange(self.__maxtilelevel+1):
            tilescale = 2**(self.__maxtilelevel-tilelevel)

            ## number of pixels on the original image taken by the
            ## side of the tile
            real_tilesize = tilescale*self.__tilesize

            numtiles_across = \
                (self._width+real_tilesize-1)//real_tilesize
            numtiles_down = \
                (self._height+real_tilesize-1)//real_tilesize

            numtiles += numtiles_across * numtiles_down

        return numtiles


    def run(self):
        """Tile the image. If any errors are encountered then `self.error` will
        be set to a string describing the error.

        run() -> None
        """
        self.__logger.debug("beginning tiling process")

        self.__maxtilelevel = self.__calculate_maxtilelevel()
        self.__numtiles = self.__calculate_numtiles()

        ## number of tiles that fit on the original image
        self.__numtiles_across_total = \
            (self._width+self.__tilesize-1)//self.__tilesize
        self.__numtiles_down_total = \
            (self._height+self.__tilesize-1)//self.__tilesize

        ## width and height of the right-most and bottom-most tiles
        ## respectively
        self.__right_tiles_width =   (self._width  - 1) % self.__tilesize + 1
        self.__bottom_tiles_height = (self._height - 1) % self.__tilesize + 1

        try:
            with TileStore.disk_lock:
                ## recursively tile the image
                self.__tiles()
        except Exception, e:
            self.error = str(e)
            outpath = TileStore.get_media_path(self.__media_id)
            shutil.rmtree(outpath, ignore_errors=True)
        else:
            TileStore.write_metadata(self.__media_id,
                filext=self.__filext,
                tilesize=self.__tilesize,
                maxtilelevel=self.__maxtilelevel,
                width=self._width,
                height=self._height,
            )

        self.__progress = 1.0
        self.__logger.debug("tiling complete")


    @property
    def progress(self):
        """Tiling progress ranging from 0.0 to 1.0. A value of 1.0 indicates
        that the tiling has completely finished.
        """
        return self.__progress


    def __str__(self):
        return "Tiler(%s)" % self._infile


    def __repr__(self):
        return "Tiler(%s)" % repr(self._infile)
