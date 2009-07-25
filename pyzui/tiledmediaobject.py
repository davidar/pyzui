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

"""Tiled media to be displayed in the ZUI."""

import tempfile
import os
import math
import logging

from PyQt4 import QtCore, QtGui
from ImageQt import ImageQt

from mediaobject import MediaObject, LoadError, RenderMode
import tilemanager as TileManager
from ppm import PPMTiler
from webkitconverter import  WebKitConverter
from pdfconverter import PDFConverter
from magickconverter import MagickConverter

class TiledMediaObject(MediaObject):
    """TiledMediaObject objects are used to represent tiled media that can be
    rendered in the ZUI.

    If `autofit` is True, then once the media has loaded it will be fitted to
    the area occupied by the placeholder.

    Constructor: TiledMediaObject(string, Scene[, bool])
    """
    def __init__(self, media_id, scene, autofit=False):
        MediaObject.__init__(self, media_id, scene)

        self.__autofit = autofit

        self.__loaded = False

        self.__tmpfile = None

        self.__converter = None
        self.__tiler = None

        self.__logger = logging.getLogger(str(self))

        self.__maxtilelevel = 0
        self.__width, self.__height = self.default_size
        self.__aspect_ratio = None

        ## for caching tileblocks
        self.__tileblock = None
        self.__tileblock_id = None
        self.__tileblock_final = False
        self.__tileblock_age = 0

        if TileManager.tiled(self._media_id):
            TileManager.load_tile((self._media_id, 0, 0, 0))
        else:
            self.__logger.info("need to tile media")
            fd, self.__tmpfile = tempfile.mkstemp('.ppm')
            os.close(fd)
            if self._media_id.startswith('http://') or \
               self._media_id.lower().endswith('.html') or \
               self._media_id.lower().endswith('.htm'):
                self.__converter = WebKitConverter(
                    self._media_id, self.__tmpfile)
                self.__ppmfile = self.__tmpfile
                self.__converter.start()
            elif self._media_id.lower().endswith('.pdf'):
                self.__converter = PDFConverter(
                    self._media_id, self.__tmpfile)
                self.__ppmfile = self.__tmpfile
                self.__converter.start()
            elif self._media_id.lower().endswith('.ppm'):
                ## assume media_id is a local PPM file
                self.__logger.info(
                    "assuming media is a local PPM file")
                self.__ppmfile = self._media_id
            else:
                self.__converter = MagickConverter(
                    self._media_id, self.__tmpfile)
                self.__ppmfile = self.__tmpfile
                self.__converter.start()


    transparent = False

    ## initial size of the object before the actual dimensions have been
    ## loaded
    default_size = (256,256)

    ## maximum number of cycles to cache temporary tiles for
    tempcache = 5

    @property
    def __progress(self):
        if self.__converter is None and self.__tiler is None:
            return 0.0
        elif self.__converter is None:
            return self.__tiler.progress
        elif self.__tiler is None:
            return 0.5 * self.__converter.progress
        else:
            return 0.5 * (self.__converter.progress + self.__tiler.progress)


    def __pixpos2rowcol(self, pixpos, tilescale):
        """Convert the on-screen pixel position to to a (row,col) tile
        position.

        __pixpos2rowcol(tuple<float,float>, float) -> tuple<int,int>
        """
        o = self.topleft
        col = int((pixpos[0]-o[0]) / (tilescale*self.__tilesize))
        row = int((pixpos[1]-o[1]) / (tilescale*self.__tilesize))
        return (row,col)


    def __rowcol_bound(self, tilelevel):
        """Return the maximum row and column for the given tilelevel.

        __rowcol_bound(int) -> tuple<int,int>
        """
        if tilelevel <= 0:
            row_bound = col_bound = 0
        elif self.__aspect_ratio:
            if self.__aspect_ratio >= 1.0:
                ## width >= height
                col_bound = 2**tilelevel - 1
                row_bound = int((2**tilelevel)/self.__aspect_ratio) - 1
            else:
                ## height > width
                col_bound = int((2**tilelevel)*self.__aspect_ratio) - 1
                row_bound = 2**tilelevel - 1
        else:
            tile_pixsize = self.__tilesize \
                * 2 ** (self.__maxtilelevel - tilelevel)
            row_bound = int((self.__height - 1) / tile_pixsize)
            col_bound = int((self.__width  - 1) / tile_pixsize)

        return row_bound, col_bound


    def __render_tileblock(self, tileblock_id, mode):
        """Render, cache, and return the tileblock given the unique
        tileblock_id and render mode.

        __render_tileblock(tuple<int,int,int,int,int>, int) -> QImage

        Precondition: mode is equal to either RenderMode.Draft or
        RenderMode.HighQuality
        """
        self.__logger.debug("rendering tileblock")

        tilelevel, row_min, col_min, row_max, col_max = tileblock_id

        brtile = TileManager.get_tile_robust(
            (self._media_id, tilelevel, row_max, col_max))
        w = self.__tilesize * (col_max - col_min) + brtile.size[0]
        h = self.__tilesize * (row_max - row_min) + brtile.size[1]
        tileblock = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)

        tileblock_painter = QtGui.QPainter()
        tileblock_painter.begin(tileblock)

        tileblock_final = True

        for row in xrange(row_min, row_max+1):
            for col in xrange(col_min, col_max+1):
                tile_id = (self._media_id, tilelevel, row, col)
                try:
                    tile = TileManager.get_tile(tile_id)
                except TileManager.TileNotLoaded:
                    tileblock_final = False
                    if mode == RenderMode.HighQuality:
                        tile = TileManager.cut_tile(tile_id)[0]
                    else:
                        tile = TileManager.cut_tile(tile_id, self.tempcache)[0]
                except TileManager.TileNotAvailable:
                    if mode == RenderMode.HighQuality:
                        tile, final = TileManager.cut_tile(tile_id)
                    else:
                        tile, final = TileManager.cut_tile(tile_id,
                                                           self.tempcache)
                    if not final: tileblock_final = False
                x = self.__tilesize * (col-col_min)
                y = self.__tilesize * (row-row_min)
                tile.draw(tileblock_painter, x, y)

        tileblock_painter.end()

        del self.__tileblock
        self.__tileblock = tileblock
        self.__tileblock_id = tileblock_id
        self.__tileblock_final = tileblock_final
        self.__tileblock_age = 0

        return tileblock


    def __render_media(self, painter, mode):
        """Render the media using the given painter and render mode.

        __render_media(QPainter, int) -> None

        Precondition: mode is equal to one of the constants defined in
        RenderMode
        """
        if min(self.onscreen_size) <= 1 or mode == RenderMode.Invisible:
            ## don't bother rendering if the image is too
            ## small to be seen, or invisible mode is set
            return
        if mode == RenderMode.Draft:
            transform_mode = QtCore.Qt.FastTransformation
        elif mode == RenderMode.HighQuality:
            transform_mode = QtCore.Qt.SmoothTransformation

        viewport_size = self._scene.viewport_size

        zoomlevel = self.zoomlevel + self._scene.zoomlevel
        tilelevel = int(math.ceil(zoomlevel))
        tilescale = 2 ** (zoomlevel - tilelevel)

        row_min,col_min = self.__pixpos2rowcol((0,0),        tilescale)
        row_max,col_max = self.__pixpos2rowcol(viewport_size,tilescale)

        row_min = max(row_min, 0)
        col_min = max(col_min, 0)

        row_bound, col_bound = self.__rowcol_bound(tilelevel)
        row_max = min(row_max, row_bound)
        col_max = min(col_max, col_bound)

        if row_max < row_min or col_max < col_min:
            ## the image does not fall within the viewport
            return

        tileblock_id = (tilelevel, row_min, col_min, row_max, col_max)
        if (self.__tileblock_id != tileblock_id) or \
           (not self.__tileblock_final and \
            (mode == RenderMode.HighQuality or \
             self.__tileblock_age >= self.tempcache)):
            ## the cached tileblock is different to the required
            ## one, so we have draw the new tileblock
            ## we also re-render the tileblock if it is not final
            ## and either we are in HQ mode or the tileblock
            ## is at least self.tempcache cycles old
            tileblock = self.__render_tileblock(tileblock_id, mode)
        else:
            tileblock = self.__tileblock
            self.__tileblock_age += 1

        image_scaled = tileblock.scaled(
            int(tilescale * tileblock.width()),
            int(tilescale * tileblock.height()),
            QtCore.Qt.IgnoreAspectRatio,
            transform_mode)

        o = self.topleft
        x = o[0] + int(tilescale * self.__tilesize*col_min)
        y = o[1] + int(tilescale * self.__tilesize*row_min)
        painter.drawImage(x, y, image_scaled)


    def __render_placeholder(self, painter):
        """Render a placeholder indicating that the image is still loading,
        using the given painter.

        __render_placeholder(QPainter) -> None
        """
        x,y = self.topleft
        w,h = self.onscreen_size

        try:
            painter.fillRect(x, y, w, h, QtCore.Qt.darkGray)
        except TypeError:
            ## rectangle dimensions could not be converted to ints
            pass
        else:
            if self.__progress > 0:
                painter.setPen(QtGui.QColor(255,255,255))
                font = QtGui.QFont()
                font.setPointSizeF(w/4)
                painter.setFont(font)
                painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter,
                    str(int(self.__progress*100)) + '%')
            else:
                painter.setPen(QtGui.QColor(255,255,255))
                font = QtGui.QFont()
                font.setPointSizeF(w/10)
                painter.setFont(font)
                painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter,
                    "loading...")


    def __try_load(self):
        """Try to load the (0,0,0) tile from the TileManager.

        __try_load() -> None
        """
        try:
            TileManager.get_tile(
                (self._media_id, 0, 0, 0))
        except TileManager.TileNotLoaded:
            self.__logger.info("(0,0,0) tile not loaded yet")
            pass
        except (TileManager.MediaNotTiled,
            TileManager.TileNotAvailable):
            raise LoadError("unable to correctly tile the image")
        else:
            self.__logger.info("media loaded")
            self.__loaded = True

            if self.__tiler:
                ## destory tiler to close tmpfile (reqd to unlink on Windows)
                self.__tiler = None

            if self.__tmpfile:
                try:
                    os.unlink(self.__tmpfile)
                except:
                    self.__logger.exception("unable to unlink temporary file "
                        "'%s'" % self.__tmpfile)

            old_x1, old_y1 = self.topleft
            old_x2, old_y2 = self.bottomright
            old_centre = self.centre

            self.__width = TileManager.get_metadata(
                self._media_id, 'width')
            self.__height = TileManager.get_metadata(
                self._media_id, 'height')
            self.__maxtilelevel = TileManager.get_metadata(
                self._media_id, 'maxtilelevel')
            self.__tilesize = TileManager.get_metadata(
                self._media_id, 'tilesize')
            self.__aspect_ratio = TileManager.get_metadata(
                self._media_id, 'aspect_ratio')

            if self.__autofit:
                ## fit to area occupied by placeholder
                self.fit((old_x1, old_y1, old_x2, old_y2))
                self.centre = old_centre


    def __run_tiler(self):
        """Run the tiler (after checking that there is an image to run
        the tiler on).

        __run_tiler() -> None
        """
        if not os.path.exists(self.__ppmfile):
            ## there was a problem converting, or the input file
            ## never actually existed
            if self.__converter and self.__converter.error:
                raise LoadError(self.__converter.error)
            else:
                raise LoadError("there was a problem "
                    "converting and/or loading the input file")

        if self._media_id.lower().endswith('.jpg'):
            filext = 'jpg'
        else:
            filext = 'png'

        try:
            self.__tiler = PPMTiler(
                self.__ppmfile, self._media_id, filext)
            self.__tiler.start()
        except IOError, e:
            raise LoadError("there was an error creating the tiler: %s" % e)


    def render(self, painter, mode):
        if self.__loaded:
            self.__render_media(painter, mode)

        elif self.__tiler and self.__tiler.error:
            raise LoadError("an error ocurred during "
                "the tiling process: %s" % self.__tiler.error)

        elif TileManager.tiled(self._media_id):
            self.__try_load()
            if self.__loaded:
                self.__render_media(painter, mode)
            else:
                self.__render_placeholder(painter)

        elif self.__tiler is None and \
             (self.__converter is None or self.__converter.progress == 1.0):
            ## the tiler has not been run yet and either
            ## it was assumed that media_id is a local PPM
            ## file or the converter has just finished
            self.__run_tiler()
            self.__render_placeholder(painter)

        else:
            self.__render_placeholder(painter)


    @property
    def onscreen_size(self):
        if self.__aspect_ratio:
            if self.__aspect_ratio >= 1.0:
                ## width >= height
                w = 2**(self._scene.zoomlevel+self.zoomlevel) * self.__tilesize
                h = w / self.__aspect_ratio
            else:
                ## height > width
                h = 2**(self._scene.zoomlevel+self.zoomlevel) * self.__tilesize
                w = h * self.__aspect_ratio
            return (w,h)
        elif self.__width == 0 or self.__height == 0:
            return (0,0)
        else:
            scale = 2 ** (self._scene.zoomlevel + self.zoomlevel \
                - self.__maxtilelevel)
            w = self.__width * scale
            h = self.__height * scale
            return (w,h)
