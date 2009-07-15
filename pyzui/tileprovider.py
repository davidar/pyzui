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

"""Threaded class for loading tiles into memory (abstract base class)."""

from __future__ import with_statement

from threading import Thread, Condition
from collections import deque
import logging

from tile import Tile

class TileProvider(Thread):
    """TileProvider objects are used for loading tiles into TileCache objects.

    Constructor: TileProvider(TileCache)
    """
    def __init__(self, tilecache):
        """Create a new TileProvider for loading tiles into the given
        `tilecache`."""

        Thread.__init__(self)
        self.setDaemon(True)

        self.__tilecache = tilecache

        self.__tasks = deque()
        self.__tasks_available = Condition()

        self._logger = logging.getLogger(str(self))


    def request(self, tile_id):
        """Request the tile identified by `tile_id` be loaded into the
        tilecache.

        Requests are processed in a LIFO order.

        If the tile is unavailable, then None will be inserted into the
        tilecache to indicate this.

        request(tuple<string,int,int,int>) -> None
        """
        self.__tasks_available.acquire()
        self.__tasks.append(tile_id)
        self.__tasks_available.notify()
        self.__tasks_available.release()


    def _load(self, tile_id):
        """Load the requested tile, and return it as an `Image` object.

        Returns None if the tile does not exist.

        _load(tuple<string,int,int,int>) -> Image or None
        """
        pass


    def run(self):
        """Run a loop to load requested tiles.

        run() -> None
        """
        while True:
            self.__tasks_available.acquire()
            while not self.__tasks:
                self.__tasks_available.wait()
            tile_id = self.__tasks.pop()
            self.__tasks_available.release()

            if tile_id not in self.__tilecache:
                try:
                    tile = self._load(tile_id)
                except Exception:
                    self._logger.exception("error loading tile")
                    tile = None

                if tile:
                    self._logger.debug("loaded %s", str(tile_id))
                    self.__tilecache[tile_id] = Tile(tile)
                    del tile
                else:
                    self._logger.debug("unavailable %s", str(tile_id))
                    self.__tilecache[tile_id] = None


    def purge(self, media_id=None):
        """Purge all tasks for the given `media_id`. All tasks will be purged
        if `media_id` is omitted.

        purge([string]) -> None
        """
        self.__tasks_available.acquire()
        self._logger.debug("purging %s", media_id or "all")
        if media_id:
            new_tasks = deque()
            for task in self.__tasks:
                if task[0] != media_id:
                    new_tasks.append(task)
            self.__tasks = new_tasks
        else:
            self.__tasks = deque()
        self.__tasks_available.release()


    def __str__(self):
        return type(self).__name__


    def __repr__(self):
        return "%s()" % type(self).__name__
