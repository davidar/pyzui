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

"""Webpage renderer based upon QtWebKit."""

import os
import sys
import logging
import time

from PyQt4 import QtCore, QtGui, QtWebKit, QtSvg

from converter import Converter

class WebKitConverter(Converter):
    """WebKitConverter objects are used for rendering webpages.

    `infile` may be either a URI or the location of a local file.

    Supported output formats are: BMP, JPG/JPEG, PNG, PPM, TIFF, XBM, XPM
    (see <http://doc.trolltech.com/qimage.html
    #reading-and-writing-image-files>)

    Constructor: WebKitConverter(string, string)
    """
    def __init__(self, infile, outfile):
        Converter.__init__(self, infile, outfile)


    def start(self):
        """If a global QApplication has already been instantiated, then this
        method will call `run()` directly, as Qt requires us to call `run()`
        from the same thread as the global QApplication. This will not block as
        Qt will then handle the threading.

        Otherwise, if no QApplication exists yet, then the default
        `Converter.start()` method will be called allowing Python to natively
        handle the threading.

        start() -> None
        """
        if QtGui.QApplication.instance() is None:
            self._logger.info("using Python threading")
            Converter.start(self)
        else:
            self._logger.info("using Qt threading")
            self.run()


    def run(self):
        if QtGui.QApplication.instance() is None:
            ## no QApplication exists yet
            self.__qapp = QtGui.QApplication([])
        else:
            ## a global QApplication already exists
            self.__qapp = None

        self.__qpage = QtWebKit.QWebPage()

        QtCore.QObject.connect(
            self.__qpage,QtCore.SIGNAL("loadFinished(bool)"),
            self.__load_finished)
        QtCore.QObject.connect(
            self.__qpage, QtCore.SIGNAL("loadProgress(int)"),
            self.__load_progress)

        self.__qpage.mainFrame().setScrollBarPolicy(
            QtCore.Qt.Horizontal, QtCore.Qt.ScrollBarAlwaysOff)
        self.__qpage.mainFrame().setScrollBarPolicy(
            QtCore.Qt.Vertical, QtCore.Qt.ScrollBarAlwaysOff)

        pagewidth = 1024
        pageminheight = 0
        self.__qpage.setViewportSize(
            QtCore.QSize(pagewidth, pageminheight))

        self.__qpage.mainFrame().load(QtCore.QUrl(self._infile))

        if self.__qapp is not None:
            self.__qapp.exec_()


    def __load_finished(self, ok):
        """Qt slot called when the page has finished loading.

        __load_finished(bool) -> None
        """
        if ok and self.__qpage.mainFrame().contentsSize().height() != 0:
            ## load was successful

            self._logger.info("page successfully loaded")

            painter = QtGui.QPainter()

            ## resize height to fit page
            self.__qpage.setViewportSize(
                self.__qpage.mainFrame().contentsSize())

            if self._outfile.lower().endswith('.svg'):
                svg = QtSvg.QSvgGenerator()
                svg.setFileName(self._outfile)
                svg.setSize(self.__qpage.viewportSize())
                painter.begin(svg)
                self.__qpage.mainFrame().render(painter)
                painter.end()
            else:
                image = QtGui.QImage(
                    self.__qpage.viewportSize(),
                    QtGui.QImage.Format_RGB32)
                painter.begin(image)
                self.__qpage.mainFrame().render(painter)
                painter.end()
                image.save(self._outfile)
        else:
            self.error = "unable to load the page"
            self._logger.error(self.error)
            os.unlink(self._outfile)

        if self.__qapp is not None:
            self.__qapp.exit()

        self._progress = 1.0


    def __load_progress(self, progress):
        """Qt slot called when the page load progress changes.

        __load_progress(int) -> None
        """
        self._logger.info("page %3d%% loaded", progress)
        self._progress = 0.01*progress


    def __str__(self):
        return "WebKitConverter(%s, %s)" % (self._infile, self._outfile)


    def __repr__(self):
        return "WebKitConverter(%s, %s)" % \
            (repr(self._infile), repr(self._outfile))


if __name__ == '__main__' and len(sys.argv) == 3:
    logging.basicConfig(level=logging.INFO)
    c = WebKitConverter(sys.argv[1], sys.argv[2])
    c.start()
    c.join()
