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

"""Module for reading PPM images."""

from tiler import Tiler

def read_ppm_header(f):
    """Read the PPM header in the given file object `f` and return a tuple
    representing the dimensions of the image.

    Raises `IOError` if the header is invalid and/or unsupported (must be 'P6'
    binary PPM format with maxval=255).

    read_ppm_header(file) -> (long, long)
    """
    header = []
    while len(header) < 4:
        line = f.readline()

        if not line:
            ## we've hit EOF
            raise IOError("not enough entries in PPM header")

        header.extend(line.split())

    magic = header[0]
    if magic != 'P6':
        raise IOError("can only load binary PPM (P6 format)")

    try:
        width = long(header[1])
        height = long(header[2])
        maxval = int(header[3])
    except ValueError:
        raise IOError("invalid PPM header")

    if maxval != 255:
        raise IOError("PPM maxval must equal 255")

    return (width, height)


class PPMTiler(Tiler):
    """PPMTiler objects are used for tiling PPM images.

    Constructor: PPMTiler(string[, string[, string[, int]]])
    """
    def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
        Tiler.__init__(self, infile, media_id, filext, tilesize)

        try:
            self.__ppm_fileobj = open(self._infile, 'rb')
        except IOError:
            raise

        self._width, self._height = read_ppm_header(self.__ppm_fileobj)

        self._bytes_per_pixel = 3


    def _scanline(self):
        return self.__ppm_fileobj.read(self._bytes_per_pixel * self._width)


    def __del__(self):
        self.__ppm_fileobj.close()
