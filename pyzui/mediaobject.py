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

"""Media to be displayed in the ZUI (abstract base class)."""

import math

from physicalobject import PhysicalObject

class MediaObject(PhysicalObject):
    """MediaObject objects are used to represent media that can be rendered in
    the ZUI.

    Constructor: MediaObject(string, Scene)
    """
    def __init__(self, media_id, scene):
        """Create a new MediaObject from the media identified by `media_id`,
        and the parent Scene referenced by `scene`."""
        PhysicalObject.__init__(self)

        self._media_id = media_id
        self._scene = scene


    def render(self, painter, mode):
        """Render the media using the given `painter` and rendering `mode`.

        render(QPainter, int) -> None

        Precondition: `mode` is equal to one of the constants defined in
        `RenderMode`
        """
        pass


    def move(self, dx, dy):
        """Move the image relative to the scene, where (`dx`,`dy`) is given as
        an on-screen distance.

        move(float, float) -> None
        """
        self._x += dx * (2 ** -self._scene.zoomlevel)
        self._y += dy * (2 ** -self._scene.zoomlevel)


    def zoom(self, amount):
        """Zoom by the given `amount` with the centre maintaining its position
        on the screen.

        zoom(float) -> None
        """

        ## C_s is the scene coordinates of the centre
        ## C_i is the image coordinates of the centre
        ## P is the onscreen position of the centre
        ## zoomlevel_i' = zoomlevel_i + amount
        ##    P = scene.origin + C_s * 2**zoomlevel_s
        ##      => C_s = (P - scene.origin) * 2**-zoomlevel_s
        ## C_s  = self.pos  + C_i * 2**zoomlevel_i
        ##      => C_i = (C_s - self.pos) * 2**-zoomlevel_i
        ## C_s' = self.pos' + C_i * 2**zoomlevel_i'
        ##      = self.pos' + (C_s - self.pos)
        ##        * 2**(zoomlevel_i'-zoomlevel_i)
        ## solving for C_s = C_s' yields:
        ##   self.pos' = C_s - (C_s - self.pos) * 2**amount

        # Px, Py = self.centre
        # C_sx = (Px - self._scene.origin[0]) * 2**-self._scene.zoomlevel
        # C_sy = (Py - self._scene.origin[1]) * 2**-self._scene.zoomlevel

        C_ix, C_iy = self._centre
        C_sx = self._x + C_ix * 2**self._z
        C_sy = self._y + C_iy * 2**self._z

        self._x = C_sx - (C_sx - self._x) * 2**amount
        self._y = C_sy - (C_sy - self._y) * 2**amount
        self._z += amount


    def hides(self, other):
        """Returns True iff `other` is completely hidden behind `self` on the
        screen.

        hides(MediaObject) -> bool
        """
        if self.transparent:
            ## nothing can be hidden behind a transparent object
            return False

        viewport_size = self._scene.viewport_size

        s_left, s_top = self.topleft
        s_right, s_bottom = self.bottomright
        ## clamp values
        s_left =   max(0, min(s_left,   viewport_size[0]))
        s_top =    max(0, min(s_top,    viewport_size[1]))
        s_right =  max(0, min(s_right,  viewport_size[0]))
        s_bottom = max(0, min(s_bottom, viewport_size[1]))

        o_left, o_top = other.topleft
        o_right, o_bottom = other.bottomright
        ## clamp values
        o_left =   max(0, min(o_left,   viewport_size[0]))
        o_top =    max(0, min(o_top,    viewport_size[1]))
        o_right =  max(0, min(o_right,  viewport_size[0]))
        o_bottom = max(0, min(o_bottom, viewport_size[1]))

        return o_left  >= s_left  and o_top    >= s_top and \
               o_right <= s_right and o_bottom <= s_bottom


    def fit(self, bbox):
        """Move and resize the image such that it the greatest size possible
        whilst fitting inside and centred in the onscreen bounding box `bbox`
        (x1,y1,x2,y2).

        fit(tuple<float,float,float,float>) -> None
        """
        box_x, box_y, box_x2, box_y2 = map(float, bbox)
        box_w = box_x2 - box_x
        box_h = box_y2 - box_y

        w, h = self.onscreen_size

        if w/h > box_w/box_h:
            ## need to fit width
            scale = box_w / w
            target_x = box_x
            target_y = box_y + box_h/2 - (h*scale)/2
        else:
            ## need to fit height
            scale = box_h / h
            target_x = box_x + box_w/2 - (w*scale)/2
            target_y = box_y

        self.zoomlevel += math.log(scale, 2)

        self._x = (target_x - self._scene.origin[0]) \
            * (2 ** -self._scene.zoomlevel)
        self._y = (target_y - self._scene.origin[1]) \
            * (2 ** -self._scene.zoomlevel)


    def __cmp__(self, other):
        if self is other:
            return 0
        elif self.onscreen_area < other.onscreen_area:
            return -1
        else:
            return 1


    @property
    def media_id(self):
        """The object's media_id."""
        return self._media_id


    @property
    def scale(self):
        """The factor by which each dimension of the image should be scaled
        when rendering it to the screen."""
        return 2 ** (self._scene.zoomlevel + self.zoomlevel)


    @property
    def topleft(self):
        """The on-screen positon of the top-left corner of the image."""
        x = self._scene.origin[0] + self.pos[0] * (2 ** self._scene.zoomlevel)
        y = self._scene.origin[1] + self.pos[1] * (2 ** self._scene.zoomlevel)
        return (x,y)


    @property
    def onscreen_size(self):
        """The on-screen size of the image."""
        pass


    @property
    def bottomright(self):
        """The on-screen positon of the bottom-right corner of the image."""
        o = self.topleft
        s = self.onscreen_size
        x = o[0] + s[0]
        y = o[1] + s[1]
        return (x,y)


    @property
    def onscreen_area(self):
        """The number of pixels the image occupies on the screen."""
        w,h = self.onscreen_size
        return w * h

    def __get_pos(self):
        """The position of the object."""
        return (self._x, self._y)
    def __set_pos(self, pos):
        self._x, self._y = pos
    pos = property(__get_pos, __set_pos)

    def __get_centre(self):
        ## we need to convert image-coordinate C_i to
        ## screen-coordinate P (through scene-coordinate C_s):
        ##   P = scene.origin + C_s * 2**zoomlevel_s
        ## C_s = self.pos + C_i * 2**zoomlevel_i
        C_s = (self._x + self._centre[0] * 2**self._z,
               self._y + self._centre[1] * 2**self._z)
        return (self._scene.origin[0] + C_s[0] * 2**self._scene.zoomlevel,
                self._scene.origin[1] + C_s[1] * 2**self._scene.zoomlevel)
    def __set_centre(self, centre):
        ## we need to convert screen-coordinate P to
        ## image-coordinate C_i (through scene-coordinate C_s):
        ##   P = scene.origin + C_s * 2**zoomlevel_s
        ##     => C_s = (P - scene.origin) * 2**-zoomlevel_s
        ## C_s = self.pos  + C_i * 2**zoomlevel_i
        ##     => C_i = (C_s - self.pos) * 2**-zoomlevel_i
        C_s = ((centre[0] - self._scene.origin[0]) * 2**-self._scene.zoomlevel,
               (centre[1] - self._scene.origin[1]) * 2**-self._scene.zoomlevel)
        self._centre = ((C_s[0] - self._x) * 2**-self._z,
                        (C_s[1] - self._y) * 2**-self._z)
    centre = property(__get_centre, __set_centre)

    def __str__(self):
        return "%s(%s)" % (type(self).__name__, self._media_id)


    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, repr(self._media_id))


class LoadError(Exception):
    """Exception for if there is an error loading the media."""
    pass


class RenderMode:
    """Namespace for constants used to indicate the render mode."""
    Invisible = 0
    Draft = 1
    HighQuality = 2
