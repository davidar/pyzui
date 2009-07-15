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

"""PyZUI is a Zooming User Interface for Python."""

__author__ = "David Roberts"
__copyright__ = "Copyright (C) 2009  David Roberts <dvdr18@gmail.com>"
__copyright_notice__ = """
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
"""
__credits__ = ["David Roberts"]
__license__ = "GPLv2"
__version__ = "0.1"
__maintainer__ = "David Roberts"
__email__ = "dvdr18@gmail.com"

__all__ = [
    'converter',
        'magickconverter',
        'pdfconverter',
        'webkitconverter',
    'tilestore',
    'tiler',
    'ppm',
    'tile',
    'tilecache',
    'tileprovider',
        'statictileprovider',
        'dynamictileprovider',
            'osmtileprovider',
            'globalmosaictileprovider',
            'mandeltileprovider',
            'ferntileprovider',
    'tilemanager',
    'physicalobject',
        'mediaobject',
            'tiledmediaobject',
            'stringmediaobject',
            'svgmediaobject',
        'scene',
    'qzui',
    'mainwindow',
]
