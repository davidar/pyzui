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

"""A collection of media objects."""

from __future__ import with_statement

## we need to import __builtin__ to be able to call __builtin__.open since this
## module defines its own open function
import __builtin__

import logging
from threading import RLock
import urllib
import math

from PyQt4 import QtCore, QtGui

from physicalobject import PhysicalObject
import tilemanager as TileManager
import mediaobject as MediaObject
from tiledmediaobject import TiledMediaObject
from stringmediaobject import StringMediaObject
from svgmediaobject import SVGMediaObject

class Scene(PhysicalObject):
    """Scene objects are used to hold a collection of MediaObjects.

    Constructor: Scene()
    """
    def __init__(self):
        """Create a new scene."""
        PhysicalObject.__init__(self)

        self.__objects = []
        self.__objects_lock = RLock()
        self.__viewport_size = self.standard_viewport_size

        self.selection = None

        self.__logger = logging.getLogger("Scene")


    ## an arbitrary size that is common to all scenes upon creation
    standard_viewport_size = (256,256)

    def save(self, filename):
        """Save the scene to the location given by `filename`.

        It is recommended (but not compulsory) that the file extension of
        filename be '.pzs'.

        save(string) -> None
        """

        actual_viewport_size = self.viewport_size
        ## set the viewport to a standard size before saving, so that
        ## when it is loaded the scene can be scaled to fit whatever
        ## viewport the user currently has, independent of the viewport
        ## size when the scene was saved
        self.viewport_size = self.standard_viewport_size

        f = __builtin__.open(filename, 'w')

        f.write("%s\t%s\t%s\n" % \
            (self.zoomlevel, self.origin[0], self.origin[1]))

        with self.__objects_lock:
            self.__sort_objects()
            for mediaobject in self.__objects:
                f.write("%s\t%s\t%s\t%s\t%s\n" % \
                    (type(mediaobject).__name__,
                    urllib.quote(mediaobject.media_id) \
                        .replace('%3A', ':'),
                    mediaobject.zoomlevel,
                    mediaobject.pos[0],
                    mediaobject.pos[1]))

        f.close()

        self.viewport_size = actual_viewport_size


    def add(self, mediaobject):
        """Add `mediaobject` to this scene.

        This has no effect if `mediaobject` is already in the scene.

        add(MediaObject) -> None
        """
        with self.__objects_lock:
            if mediaobject not in self.__objects:
                self.__objects.append(mediaobject)


    def remove(self, mediaobject):
        """Remove `mediaobject` from scene.

        This has no effect if `mediaobject` is not in the scene.

        remove(MediaObject) -> None
        """
        with self.__objects_lock:
            if mediaobject in self.__objects:
                self.__objects.remove(mediaobject)

                media_id = mediaobject.media_id
                media_active = False
                for other in self.__objects:
                    if other.media_id == media_id:
                        ## another object exists for
                        ## this media, meaning that
                        ## this media is active
                        media_active = True

                if not media_active:
                    TileManager.purge(media_id)


    def __sort_objects(self):
        """Sort self.__objects from largest to smallest area.

        __sort_objects() -> None
        """
        with self.__objects_lock:
            self.__objects.sort(reverse=True)


    def get(self, pos):
        """Return the foremost visible `MediaObject` which overlaps the
        on-screen point `pos`.

        Return None if there are no `MediaObject`s overlapping the point.

        get(tuple<float,float>) -> MediaObject or None
        """
        foremost = None

        with self.__objects_lock:
            self.__sort_objects()
            for mediaobject in self.__objects:
                left, top = mediaobject.topleft
                right, bottom = mediaobject.bottomright
                if pos[0] >= left  and pos[1] >= top and \
                   pos[0] <= right and pos[1] <= bottom:
                    foremost = mediaobject

        return foremost


    def render(self, painter, draft):
        """Render the scene using the given `painter`.

        If `draft` is True, draft mode is enabled. Otherwise High-Quality mode
        is enabled.

        If any errors occur rendering any of the `MediaObject`s, then they will
        be removed from the scene and a list of tuples representing the errors
        will be returned. Otherwise the empty list will be returned.

        render(QPainter, bool) -> list<tuple<MediaObject,
        MediaObject.LoadError> >
        """

        errors = []

        with self.__objects_lock:
            self.__sort_objects()

            hidden = False
            hidden_objects = set()
            for mediaobject in reversed(self.__objects):
                if hidden:
                    hidden_objects.add(mediaobject)
                else:
                    x1, y1 = mediaobject.topleft
                    x2, y2 = mediaobject.bottomright
                    if x1 <= 0 and y1 <= 0 and \
                       x2 >= self.viewport_size[0] and \
                       y2 >= self.viewport_size[1]:
                        ## mediaobject fills the entire
                        ## screen, so mark the rest of
                        ## the mediaobjects behind it
                        ## as hidden
                        hidden = True

            num_objects = len(self.__objects)
            for mediaobject in self.__objects:
                if mediaobject in hidden_objects:
                    mode = MediaObject.RenderMode.Invisible
                elif draft:
                    mode = MediaObject.RenderMode.Draft
                else:
                    mode = MediaObject.RenderMode.HighQuality

                try:
                    mediaobject.render(painter, mode)
                except MediaObject.LoadError, e:
                    errors.append((mediaobject, e))

            for mediaobject, e in errors:
                ## remove mediaobjects that have raised errors
                self.remove(mediaobject)

            ## draw border around selected object
            if self.selection:
                x1, y1 = self.selection.topleft
                x2, y2 = self.selection.bottomright

                ## clamp values
                x1 = max(0, min(int(x1), self.viewport_size[0] - 1))
                y1 = max(0, min(int(y1), self.viewport_size[1] - 1))
                x2 = max(0, min(int(x2), self.viewport_size[0] - 1))
                y2 = max(0, min(int(y2), self.viewport_size[1] - 1))

                painter.setPen(QtCore.Qt.green)
                painter.drawRect(x1, y1, x2-x1, y2-y1)

        return errors


    def step(self, t):
        """Step the scene and all contained `MediaObject`s forward `t` seconds
        in time.

        step(float) -> None
        """
        with self.__objects_lock:
            for mediaobject in self.__objects:
                mediaobject.step(t)
            PhysicalObject.step(self, t)


    @property
    def moving(self):
        """Boolean value indicating whether the scene or any contained
        `MediaObject`s have a non-zero velocity."""
        if not (self.vx == self.vy == self.vz == 0):
            return True
        else:
            with self.__objects_lock:
                for mediaobject in self.__objects:
                    if mediaobject.moving:
                        return True

        return False


    def __get_origin(self):
        """Location of the scene's origin."""
        return (self._x, self._y)
    def __set_origin(self, origin):
        self._x, self._y = origin
    origin = property(__get_origin, __set_origin)

    def __get_viewport_size(self):
        """Dimensions of the viewport."""
        return self.__viewport_size
    def __set_viewport_size(self, viewport_size):
        ## centre the scene in the new viewport
        old_viewport_size = self.__viewport_size
        self._x += (viewport_size[0] - old_viewport_size[0]) / 2
        self._y += (viewport_size[1] - old_viewport_size[1]) / 2

        ## scale the scene such that the minimum dimension of the old
        ## viewport is the same in-scene distance as the minimum
        ## dimension of the new viewport
        self.centre = (viewport_size[0]/2, viewport_size[1]/2)
        scale = float(min(viewport_size)) / min(old_viewport_size)
        self.zoom(math.log(scale, 2))

        self.__viewport_size = viewport_size
    viewport_size = property(__get_viewport_size, __set_viewport_size)


def new():
    """Create and return a new `Scene` object.

    new() -> Scene
    """
    return Scene()


def open(filename):
    """Load the scene stored in the file given by `filename`.

    open(string) -> Scene

    Precondition: `filename` refers to a file in the same format as produced by
    `Scene.save`
    """

    scene = Scene()

    f = __builtin__.open(filename, 'U')

    zoomlevel, ox, oy = f.readline().split()
    scene.zoomlevel = float(zoomlevel)
    scene.origin = (float(ox), float(oy))

    for line in f:
        class_name, media_id, zoomlevel, x, y = line.split()
        media_id = urllib.unquote(media_id)

        if class_name == 'TiledMediaObject' or \
           class_name == 'StringMediaObject' or \
           class_name == 'SVGMediaObject':
            if   class_name ==   'TiledMediaObject':
                mediaobject = TiledMediaObject(
                    media_id, scene)
            elif class_name ==   'StringMediaObject':
                mediaobject = StringMediaObject(
                    media_id, scene)
            elif class_name ==   'SVGMediaObject':
                mediaobject = SVGMediaObject(
                    media_id, scene)

            mediaobject.zoomlevel = float(zoomlevel)
            mediaobject.pos = (float(x), float(y))
            scene.add(mediaobject)
        else:
            ## ignore instances of any other class
            pass


    f.close()

    return scene
