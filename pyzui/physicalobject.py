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

"""An object that obeys the laws of physics."""

import math

class PhysicalObject(object):
    """PhysicalObject objects are used to represent anything that has a
    3-dimensional position and velocity, where the z-dimension represents a
    zoomlevel.

    Constructor: PhysicalObject()
    """
    def __init__(self):
        """Create a new PhysicalObject at the origin with zero velocity."""
        self._x = 0.0
        self._y = 0.0
        self._z = 0.0

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self._centre = (0,0)


    ## the velocity is damped at each frame such that each second it is
    ## reduced by a factor of damping_factor:
    ##   v = u * damping_factor**-t
    damping_factor = 256

    def __damp(self, velocity, t):
        """Damp the given velocity.

        __damp(float, float) -> float
        """
        velocity *= self.damping_factor ** -t
        if abs(velocity) < 0.05:
            velocity = 0.0
        return velocity


    def __displacement(self, t, u):
        """Calculate the displacement at time t given initial velocity u.

        __displacement(float, float) -> float
        """

        ## Let d = damping_factor
        ##     u = initial velocity
        ##     t = time in seconds
        ## we know v(t) = u * d**-t
        ## s(t) = \int v(t)  dt
        ##      = \int u * d**-t  dt
        ##      = -u / log(d) * \int -log(d) * exp(-t*log(d))  dt
        ##      = -u * exp(-t*log(d)) / log(d) + C
        ##      = -u * d**-t / log(d) + C
        ## solving C for s=0 at t=0:
        ## s(t) = -u * d**-t / log(d) + u / log(d)
        ##      = (u / log(d)) * (1 - d**-t)

        return (u / math.log(self.damping_factor)) \
               * (1 - self.damping_factor**-t)


    def move(self, dx, dy):
        """Move the object by (`dx`,`dy`).

        move(float, float) -> None
        """
        self._x += dx
        self._y += dy


    def zoom(self, amount):
        """Zoom by the given `amount` with the centre maintaining its position
        on the screen.

        zoom(float) -> None
        """

        ## P is the onscreen position of the centre
        ## C is the coordinates of the centre
        ## zoomlevel' = zoomlevel + amount
        ## P  = pos  + C * 2**zoomlevel
        ##    => C = (P - pos) * 2**-zoomlevel
        ## P' = pos' + C * 2**zoomlevel'
        ##    = pos' + (P - pos) * 2**(zoomlevel'-zoomlevel)
        ## solving for P = P' yields:
        ##   pos' = P - (P - pos) * 2**amount

        Px, Py = self.centre
        self._x = Px - (Px - self._x) * 2**amount
        self._y = Py - (Py - self._y) * 2**amount
        self._z += amount


    def aim(self, v, s, t=None):
        """Calculate the initial velocity such that at time `t` the relative
        displacement of the object will be `s`, and increase the velocity
        represented by `v` by this amount.

        If `t` is omitted then it will be taken that `s` is the limit of the
        displacement as `t` approaches infinity
        i.e. the initial velocity will be calculated such that the total
        displacement will be `s` once the object has stopped moving.

        velocity(string, float[, float]) -> None

        Precondition: `v` is either 'x', 'y', or 'z'
        """
        if t:
            ## s(t) = (u / log(d)) * (1 - d**-t)
            ## => u = (s(t) * log(d)) / (1 - d**-t)
            u = (s * math.log(self.damping_factor)) \
                   / (1 - self.damping_factor**-t)
        else:
            ## s = lim_t->inf displacement
            ##   = lim_t->inf (u / log(d)) * (1 - d**-t)
            ##   = u / log(d)  since d > 1
            ## therefore u = s * log(d)
            u = s * math.log(self.damping_factor)

        if   v == 'x': self.vx += u
        elif v == 'y': self.vy += u
        elif v == 'z': self.vz += u


    def step(self, t):
        """Step forward `t` seconds in time.

        step(float) -> None
        """
        if self.vx or self.vy:
            self.move(
                self.__displacement(t, self.vx),
                self.__displacement(t, self.vy))
            self.vx = self.__damp(self.vx, t)
            self.vy = self.__damp(self.vy, t)

        if self.vz:
            self.zoom(self.__displacement(t, self.vz))
            self.vz = self.__damp(self.vz, t)


    @property
    def moving(self):
        """Boolean value indicating whether the object has a non-zero
        velocity."""
        return not (self.vx == self.vy == self.vz == 0)


    def __get_zoomlevel(self):
        """The zoomlevel of the object."""
        return self._z
    def __set_zoomlevel(self, zoomlevel):
        self._z = zoomlevel
    zoomlevel = property(__get_zoomlevel, __set_zoomlevel)

    def __get_centre(self):
        """The on-screen coordinates of the centre of the object (the
        point that will maintain its position on the screen as the
        object is being zoomed).
        """
        ## we need to convert object-coordinate C to
        ## screen-coordinate P:
        ## P = pos + C * 2**zoomlevel
        return (self._x + self._centre[0] * 2**self._z,
                self._y + self._centre[1] * 2**self._z)
    def __set_centre(self, centre):
        ## we need to convert screen-coordinate P to
        ## object-coordinate C:
        ## P = pos + C * 2**zoomlevel
        ##   => C = (P - pos) * 2**-zoomlevel
        self._centre = ((centre[0] - self._x) * 2**-self._z,
                        (centre[1] - self._y) * 2**-self._z)
    centre = property(__get_centre, __set_centre)
