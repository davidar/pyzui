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

"""PyZUI QMainWindow."""

import logging
import os
import math

from PyQt4 import QtCore, QtGui

import __init__ as PyZUI
import scene as Scene
import tilemanager as TileManager
from qzui import QZUI
from tiledmediaobject import TiledMediaObject
from stringmediaobject import StringMediaObject
from svgmediaobject import SVGMediaObject

class MainWindow(QtGui.QMainWindow):
    """MainWindow windows are used for displaying the PyZUI interface.

    Constructor: MainWindow()
    """
    def __init__(self, framerate=10):
        """Create a new MainWindow."""
        QtGui.QMainWindow.__init__(self)

        self.__logger = logging.getLogger("MainWindow")

        self.__prev_dir = ''

        self.setWindowTitle("PyZUI")

        self.zui = QZUI(self, framerate)
        self.setCentralWidget(self.zui)

        self.__create_actions()
        self.__create_menus()

        self.connect(self.zui, QtCore.SIGNAL("error"), self.__show_error)

        self.__action_open_scene_home()


    def sizeHint(self):
        return QtCore.QSize(800,600)


    def minimumSizeHint(self):
        return QtCore.QSize(320,240)


    def __show_error(self, text, details):
        """Show an error dialog with the given text and details.

        __show_error(string, string) -> None
        """
        dialog = QtGui.QMessageBox(self)
        dialog.setWindowTitle("PyZUI - Error")
        dialog.setText(text)
        dialog.setDetailedText(details)
        dialog.setIcon(QtGui.QMessageBox.Warning)
        dialog.exec_()


    def __create_action(self, key, text, callback=None, shortcut=None,
                        checkable=False):
        """Create a QAction and store it in self.__action[key].

        __create_action(string, string, function, string, bool) -> None
        """
        self.__action[key] = QtGui.QAction(text, self)

        if shortcut:
            self.__action[key].setShortcut(shortcut)

        if callback:
            self.connect(
                self.__action[key], QtCore.SIGNAL("triggered()"), callback)

        self.__action[key].setCheckable(checkable)


    def __action_new_scene(self):
        """Create a new scene.

        __action_new_scene() -> None
        """
        self.zui.scene = Scene.new()


    def __action_open_scene(self):
        """Open a scene from the location chosen by the user in a file
        selection dialog.

        __action_open_scene() -> None
        """
        filename = str(QtGui.QFileDialog.getOpenFileName(
            self, "Open scene", self.__prev_dir, "PyZUI Scenes (*.pzs)"))

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                self.zui.scene = Scene.open(filename)
            except Exception, e:
                self.__show_error("Unable to open scene", str(e))


    def __action_open_scene_home(self):
        """Open the Home scene.

        __action_open_scene_home() -> None
        """
        try:
            self.zui.scene = Scene.open(
                os.path.join("data", "home.pzs"))
        except Exception, e:
            self.__show_error("Unable to open the Home scene", str(e))


    def __action_save_scene(self):
        """Save the scene to the location chosen by the user in a file
        selection dialog.

        __action_save_scene() -> None
        """
        filename = str(QtGui.QFileDialog.getSaveFileName(
            self, "Save scene", os.path.join(self.__prev_dir, "scene.pzs"),
            "PyZUI Scenes (*.pzs)"))

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                self.zui.scene.save(filename)
            except Exception, e:
                self.__show_error("Unable to save scene", str(e))


    def __action_save_screenshot(self):
        """Save a screenshot to the location chosen by the user in a file
        selection dialog.

        __action_save_screenshot() -> None
        """
        filename = str(QtGui.QFileDialog.getSaveFileName(
            self, "Save screenshot",
            os.path.join(self.__prev_dir, "screenshot.png"),
            "Images (*.bmp *.jpg *.jpeg *.png *.ppm *.tif *.tiff "
            "*.xbm *.xpm)"))

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                QtGui.QPixmap.grabWidget(self.zui).save(filename)
            except Exception, e:
                self.__show_error("Unable to save screenshot", str(e))


    def __open_media(self, media_id, add=True):
        """Open the media with the given media_id.

        If add is True then the media will be fit to the screen and added to
        the scene. Otherwise it will be returned.

        __open_media(string[, bool]) -> None
        """
        try:
            if media_id.startswith('string:'):
                mediaobject = StringMediaObject(media_id, self.zui.scene)
            elif media_id.lower().endswith('.svg'):
                mediaobject = SVGMediaObject(media_id, self.zui.scene)
            else:
                mediaobject = TiledMediaObject(media_id, self.zui.scene, True)
        except Exception, e:
            self.__show_error("Unable to open media", str(e))
        else:
            if add:
                w = self.zui.width()
                h = self.zui.height()
                mediaobject.fit((w/4, h/4, w*3/4, h*3/4))
                self.zui.scene.add(mediaobject)
            else:
                return mediaobject


    def __action_open_media_local(self):
        """Open media from the location chosen by the user in a file
        selection dialog.

        __action_open_media_local() -> None
        """
        filename = str(QtGui.QFileDialog.getOpenFileName(
            self, "Open local media", self.__prev_dir))

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            self.__open_media(filename)


    def __action_open_media_uri(self):
        """Open media by the URI entered by the user in an input dialog.

        __action_open_media_uri() -> None
        """
        uri, ok = QtGui.QInputDialog.getText(
            self, "Open media by URI", "URI:")
        uri = unicode(uri).encode('utf-8')

        if ok and uri:
            self.__open_media(uri)


    def __action_open_media_dir(self):
        """Open media from the directory chosen by the user in a file
        selection dialog.

        __action_open_media_dir() -> None
        """
        directory = str(QtGui.QFileDialog.getExistingDirectory(
            self, "Open media directory", self.__prev_dir))

        if directory:
            self.__prev_dir = os.path.dirname(directory)
            media = []
            for filename in os.listdir(directory):
                filename = os.path.join(directory, filename)
                if not os.path.isdir(filename):
                    mediaobject = self.__open_media(filename, False)
                    if mediaobject:
                        media.append(mediaobject)

            cells_per_side = int(math.ceil(math.sqrt(len(media))))
            cellsize = float(min(self.zui.width(),
                                 self.zui.height())) / cells_per_side
            innersize = 0.9 * cellsize
            centre = (self.zui.width()/2, self.zui.height()/2)
            bbox = (centre[0] - innersize/2, centre[1] - innersize/2,
                    centre[0] + innersize/2, centre[1] + innersize/2)
            grid_centre = 0.5 * cells_per_side

            for y in xrange(cells_per_side):
                for x in xrange(cells_per_side):
                    if not media: break
                    mediaobject = media.pop(0)

                    ## resize and centre object
                    mediaobject.fit(bbox)
                    mediaobject.centre = centre

                    ## aim object towards grid cell
                    mediaobject.aim('x', (x+0.5 - grid_centre) * cellsize)
                    mediaobject.aim('y', (y+0.5 - grid_centre) * cellsize)

                    self.zui.scene.add(mediaobject)


    def __action_set_fps(self, act):
        """Set the framerate to the value specified in act.

        __action_set_fps(QAction) -> None
        """
        self.zui.framerate = act.fps


    def __action_fullscreen(self):
        """Toggles fullscreen mode.

        __action_fullscreen() -> None
        """
        self.setWindowState(self.windowState() ^ QtCore.Qt.WindowFullScreen)


    def __action_about(self):
        """Display the PyZUI about dialog.

        __action_about() -> None
        """
        QtGui.QMessageBox.about(self,
            "PyZUI %s" % PyZUI.__version__,
            PyZUI.__doc__ + '\n' +
            PyZUI.__copyright__ + '\n' +
            PyZUI.__copyright_notice__)


    def __action_about_qt(self):
        """Display the Qt about dialog.

        __action_about_qt() -> None
        """
        QtGui.QMessageBox.aboutQt(self)


    def __create_actions(self):
        """Create the QActions required for the interface.

        __create_actions() -> None
        """
        self.__action = {}

        self.__create_action('new_scene', "&New Scene",
            self.__action_new_scene, "Ctrl+N")
        self.__create_action('open_scene', "&Open Scene",
            self.__action_open_scene, "Ctrl+O")
        self.__create_action('open_scene_home', "Open &Home Scene",
            self.__action_open_scene_home, "Ctrl+Home")
        self.__create_action('save_scene', "&Save Scene",
            self.__action_save_scene, "Ctrl+S")
        self.__create_action('save_screenshot', "Save Screens&hot",
            self.__action_save_screenshot, "Ctrl+H")
        self.__create_action('open_media_local', "Open &Local Media",
            self.__action_open_media_local, "Ctrl+L")
        self.__create_action('open_media_uri', "Open Media by &URI",
            self.__action_open_media_uri, "Ctrl+U")
        self.__create_action('open_media_dir', "Open Media &Directory",
            self.__action_open_media_dir, "Ctrl+D")
        self.__create_action('quit', "&Quit",
            QtGui.qApp.closeAllWindows, "Ctrl+Q")

        self.__action['group_set_fps'] = QtGui.QActionGroup(self)
        for i in xrange(5, 31, 5):
            key = "set_fps_%d" % i
            self.__create_action(key, "%d FPS" % i, checkable=True)
            self.__action[key].fps = i
            self.__action['group_set_fps'].addAction(self.__action[key])
        self.connect(self.__action['group_set_fps'],
            QtCore.SIGNAL("triggered(QAction*)"), self.__action_set_fps)
        self.__action['set_fps_%d' % self.zui.framerate].setChecked(True)

        self.__create_action('fullscreen', "&Fullscreen",
            self.__action_fullscreen, "Ctrl+F")

        self.__create_action('about', "&About", self.__action_about)
        self.__create_action('about_qt', "About &Qt", self.__action_about_qt)


    def __create_menus(self):
        """Create the menus.

        __create_menus() -> None
        """
        self.__menu = {}

        self.__menu['file'] = self.menuBar().addMenu("&File")
        self.__menu['file'].addAction(self.__action['new_scene'])
        self.__menu['file'].addAction(self.__action['open_scene'])
        self.__menu['file'].addAction(self.__action['open_scene_home'])
        self.__menu['file'].addAction(self.__action['save_scene'])
        self.__menu['file'].addAction(self.__action['save_screenshot'])
        self.__menu['file'].addAction(self.__action['open_media_local'])
        self.__menu['file'].addAction(self.__action['open_media_uri'])
        self.__menu['file'].addAction(self.__action['open_media_dir'])
        self.__menu['file'].addAction(self.__action['quit'])

        self.__menu['view'] = self.menuBar().addMenu("&View")
        self.__menu['set_fps'] = self.__menu['view'].addMenu("Set &Framerate")
        self.__menu['set_fps'].addActions(
            self.__action['group_set_fps'].actions())
        self.__menu['view'].addAction(self.__action['fullscreen'])

        self.__menu['help'] = self.menuBar().addMenu("&Help")
        self.__menu['help'].addAction(self.__action['about'])
        self.__menu['help'].addAction(self.__action['about_qt'])


    def showEvent(self, event):
        ## focus the QZUI widget whenever this window is shown
        self.zui.setFocus(QtCore.Qt.OtherFocusReason)
