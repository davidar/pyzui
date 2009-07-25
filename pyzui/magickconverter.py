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

"""Image converter based upon ImageMagick."""

from __future__ import with_statement

import subprocess
import os
import sys

from converter import Converter
import tilestore as TileStore

class MagickConverter(Converter):
    """MagickConverter objects are used for converting media with ImageMagick.
    For a list of supported image formats see
    <http://imagemagick.org/script/formats.php>

    Constructor: MagickConverter(string, string)
    """
    def __init__(self, infile, outfile):
        Converter.__init__(self, infile, outfile)

        ## since PPMTiler only supports 8-bit images
        self.bitdepth = 8


    def run(self):
        if sys.platform == 'win32':
            convert_exe = 'imconvert'
        else:
            convert_exe = 'convert'
        
        with TileStore.disk_lock:
            self._logger.debug("calling convert")
            process = subprocess.Popen([convert_exe,
                '-depth', str(self.bitdepth),
                self._infile, self._outfile],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            stdout = process.communicate()[0]

        if process.returncode != 0:
            self.error = "conversion failed with return code " \
                "%d:\n%s" % (process.returncode, stdout)
            self._logger.error(self.error)
            try:
                os.unlink(self._outfile)
            except:
                self.__logger.exception("unable to unlink temporary file "
                    "'%s'" % self._outfile)

        self._progress = 1.0


    def __str__(self):
        return "MagickConverter(%s, %s)" %  (self._infile, self._outfile)


    def __repr__(self):
        return "MagickConverter(%s, %s)" % \
            (repr(self._infile), repr(self._outfile))
