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

"""SVG objects to be displayed in the ZUI."""

from PyQt4 import QtCore, QtGui, QtSvg

from mediaobject import MediaObject, LoadError, RenderMode

class SVGMediaObject(MediaObject):
    """StringMediaObject objects are used to represent SVG images that can be
    rendered in the ZUI.

    Constructor: SVGMediaObject(string, Scene)
    """
    def __init__(self, media_id, scene):
        MediaObject.__init__(self, media_id, scene)

        self.__renderer = QtSvg.QSvgRenderer()
        if not self.__renderer.load(self._media_id):
            raise LoadError("unable to parse SVG file")

        size = self.__renderer.defaultSize()
        self.__width = size.width()
        self.__height = size.height()


    transparent = True

    def render(self, painter, mode):
        if min(self.onscreen_size) > 1 and mode != RenderMode.Invisible:
            ## don't bother rendering if the string is too
            ## small to be seen, or invisible mode is set

            x,y = self.topleft
            w,h = self.onscreen_size
            self.__renderer.render(painter, QtCore.QRectF(x,y,w,h))


    @property
    def onscreen_size(self):
        return (self.__width * self.scale, self.__height * self.scale)
