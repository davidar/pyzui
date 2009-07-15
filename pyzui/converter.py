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

"""A threaded media converter (abstract base class)."""

from threading import Thread
import logging

class Converter(Thread):
    """Converter objects are used for converting media.

    Constructor: Converter(string, string)
    """
    def __init__(self, infile, outfile):
        """Create a new Converter for converting media at the location given by
        `infile` to the location given by `outfile`.

        Where appropriate, the output format will be determined from the file
        extension of `outfile`.
        """
        Thread.__init__(self)

        self._infile = infile
        self._outfile = outfile

        self._progress = 0.0

        self._logger = logging.getLogger(str(self))

        self.error = None


    def run(self):
        """Run the conversion. If any errors are encountered then `self.error`
        will be set to a string describing the error.

        run() -> None
        """
        pass


    @property
    def progress(self):
        """Conversion progress ranging from 0.0 to 1.0. A value of 1.0
        indicates that the converter has completely finished.
        """
        return self._progress


    def __str__(self):
        return "Converter(%s, %s)" % (self._infile, self._outfile)


    def __repr__(self):
        return "Converter(%s, %s)" % (repr(self._infile), repr(self._outfile))
