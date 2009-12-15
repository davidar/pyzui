#!/usr/bin/env python
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

import logging
import sys
import os

from PyQt4 import QtCore, QtGui

import pyzui.tilemanager as TileManager
from pyzui.mainwindow import MainWindow

def main():
    if os.path.dirname(__file__):
        ## set the working directory to the directory containing this script
        os.chdir(os.path.dirname(__file__))

    logging.basicConfig(level=logging.DEBUG)
    TileManager.init()

    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join("data", "icon.png")))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
if __name__ == '__main__': main()
