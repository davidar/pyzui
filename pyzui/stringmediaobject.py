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

"""Strings to be displayed in the ZUI."""

from PyQt4 import QtCore, QtGui

from mediaobject import MediaObject, LoadError, RenderMode

class StringMediaObject(MediaObject):
    """StringMediaObject objects are used to represent strings that can be
    rendered in the ZUI.

    `media_id` should be of the form 'string:rrggbb:foobar', where 'rrggbb' is
    a string of three two-digit hexadecimal numbers representing the colour of
    the text, and 'foobar' is the string to be displayed.

    Constructor: StringMediaObject(string, Scene)
    """
    def __init__(self, media_id, scene):
        MediaObject.__init__(self, media_id, scene)

        hexcol = self._media_id[len('string:'):len('string:rrggbb')]
        self.__color = QtGui.QColor('#' + hexcol)
        if not self.__color.isValid():
            raise LoadError("the supplied colour is invalid")

        self.__str = self._media_id[len('string:rrggbb:'):].decode('utf-8')


    transparent = True

    ## point size of the font when the scale is 100%
    base_pointsize = 24.0

    def render(self, painter, mode):
        if min(self.onscreen_size) > 1 and mode != RenderMode.Invisible:
            ## don't bother rendering if the string is too
            ## small to be seen, or invisible mode is set

            x,y = self.topleft
            w,h = self.onscreen_size

            painter.setPen(self.__color)
            painter.setFont(self.__font)
            painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter, self.__str)


    @property
    def __pointsize(self):
        return self.base_pointsize * self.scale


    @property
    def __font(self):
        pointsize = self.__pointsize
        if pointsize < 1:
            ## too small to be seen
            return None

        font = QtGui.QFont('Sans Serif')
        font.setPointSizeF(pointsize)
        return font


    @property
    def onscreen_size(self):
        font = self.__font

        if font:
            fontmetrics = QtGui.QFontMetrics(font)
            w = fontmetrics.width(self.__str)
            h = fontmetrics.height()
            return (w,h)
        else:
            return (0,0)
