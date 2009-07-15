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

"""Class for representing image tiles."""

import Image
from ImageQt import ImageQt
from PyQt4 import QtCore, QtGui

class Tile(object):
    """Tile objects allow storage and manipulation of image tiles.

    Constructor: Tile(Image or QImage)
    """
    def __init__(self, image):
        """Create a new tile with the given image."""
        if image.__class__ is ImageQt or type(image) is QtGui.QImage:
            self.__image = image
        else:
            self.__image = ImageQt(image)


    def crop(self, bbox):
        """Return the region of the tile contained in the bounding box `bbox`
        (x1,y1,x2,y2).

        crop(tuple<int,int,int,int>) -> Tile
        """
        x, y, x2, y2 = bbox
        w = x2 - x
        h = y2 - y
        return Tile(self.__image.copy(x, y, w, h))


    def resize(self, width, height):
        """Return a resized copy of the tile.

        resize(int, int) -> Tile
        """
        return Tile(self.__image.scaled(width, height,
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation))


    def save(self, filename):
        """Save the tile to the location given by `filename`.

        save(string) -> None
        """
        self.__image.save(filename)


    def draw(self, painter, x, y):
        """Draw the tile on the given `painter` at the given position.

        paint(QPainter, int, int) -> None
        """
        painter.drawImage(x, y, self.__image)


    @property
    def size(self):
        """The dimensions of the tile."""
        return (self.__image.width(), self.__image.height())



def new(width, height):
    """Create a new tile with the given dimensions.

    new(int, int) -> Tile
    """
    return Tile(QtGui.QImage(width, height, QtGui.QImage.Format_RGB32))


def fromstring(string, width, height):
    """Create a new tile from a `string` of raw pixels, with the given
    dimensions.

    fromstring(string, int, int) -> Tile
    """
    return Tile(Image.fromstring('RGB', (width, height), string))


def merged(t1, t2, t3, t4):
    """Merge the given tiles into a single tile.

    `t1` must be a Tile, but any or all of `t2`,`t3`,`t4` may be None, in which
    case they will be ignored.

    merged(Tile, Tile or None, Tile or None, Tile or None) -> Tile
    """

    ## tiles are merged in the following layout:
    ## +---------+
    ## | t1 | t2 |
    ## |----+----|
    ## | t3 | t4 |
    ## +---------+

    tilewidth, tileheight = t1.size
    if t2: tilewidth  += t2.size[0]
    if t3: tileheight += t3.size[1]

    painter = QtGui.QPainter()
    image = QtGui.QImage(tilewidth, tileheight, QtGui.QImage.Format_RGB32)
    painter.begin(image)

    if t1: t1.draw(painter, 0,          0         )
    if t2: t2.draw(painter, t1.size[0], 0         )
    if t3: t3.draw(painter, 0,          t1.size[1])
    if t4: t4.draw(painter, t1.size[0], t1.size[1])

    painter.end()

    return Tile(image)
