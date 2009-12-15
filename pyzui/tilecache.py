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

"""Thread-safe Least Recently Used (LRU) cache for storing tiles."""

from __future__ import with_statement

from threading import RLock, Thread
from collections import deque
import time

class TileCache(object):
    """TileCache objects are used for caching tiles in memory.

    Tiles can be accessed in much that same way as `dict` objects:
    `tilecache[tile_id]` holds the tile identified by the given `tile_id`.

    Constructor: TileCache(int, int)
    """
    def __init__(self, maxsize=256, maxage=60):
        """Create a new TileCache object.

        The maximum number of tiles to store is set by `maxsize`. There will be
        no limit if `maxsize` <= 0.

        The maximum age of the tiles (in seconds) allowed before they are
        discarded is set by `maxsize`. There will be no limit if `maxage` <= 0.

        None tiles and (0,0,0) tiles do not count towards the number of stored
        tiles and will therefore not be automatically discarded.
        """
        self.__maxsize = maxsize
        self.__maxage = maxage

        self.__d = {}
        self.__atime = {}
        self.__anum = {}
        self.__maxaccesses = {}
        self.__discard_queue = deque()
        self.__num_tiles = 0

        self.__lock = RLock()

        self.__periodic_clean_thread = Thread(target=self.__periodic_clean)
        self.__periodic_clean_thread.setDaemon(True)
        self.__periodic_clean_thread.start()


    def insert(self, tile_id, tile, maxaccesses=0):
        """Insert the `tile` with the given `tile_id` into the cache.

        If `maxaccesses` <= 0, then the behaviour is the same as
        `tilecache[tile_id]=tile`. Otherwise the tile is set to expire after it
        has been accessed `maxaccesses` times.

        insert(tuple<string,int,int,int>, object, int) -> None
        """
        with self.__lock:
            self[tile_id] = tile
            if maxaccesses > 0:
                self.__maxaccesses[tile_id] = maxaccesses


    # def expire(self):
    #     """Expire all tiles that have been set to expire after having been
    #     accessed a certain number of times (i.e. if `insert` has been called
    #     with `maxaccesses` > 0).
    #
    #     expire() -> None
    #     """
    #     with self.__lock:
    #         tile_ids = self.__maxaccesses.keys()
    #         for tile_id in tile_ids:
    #             del self[tile_id]


    # def temporary(self, tile_id):
    #     """Return True iff the tile with the given `tile_id` has been set to
    #     expire after having been accessed a certain number of times (i.e. if
    #     `insert` has been called with `maxaccesses` > 0).
    #
    #     temporary(tuple<string,int,int,int>) -> bool
    #     """
    #     return tile_id in self.__maxaccesses


    def __mortal(self, tile_id, tile):
        """Returns a bool indicating whether the given tile is mortal.

        The tile will never be removed from the cache if it is immortal.

        None tiles and (0,0,0) tiles are the only ones considered immortal.

        __mortal(tuple<string,int,int,int>, object) -> bool
        """
        return tile is not None and tile_id[1] != 0


    def __getitem__(self, tile_id):
        with self.__lock:
            if tile_id in self.__d:
                tile = self.__d[tile_id]

                if self.__mortal(tile_id, tile):
                    ## move this tile to the back of the discard queue
                    self.__discard_queue.remove(tile_id)
                    self.__discard_queue.append(tile_id)
                    self.__atime[tile_id] = int(time.time())

                self.__anum[tile_id] = self.__anum.get(tile_id, 0) + 1
                if tile_id in self.__maxaccesses and \
                   self.__anum[tile_id] >= self.__maxaccesses[tile_id]:
                    ## tile has expired
                    del self[tile_id]

                return tile
            else:
                raise KeyError


    def __periodic_clean(self):
        """Periodically remove old tiles based on maxage.

        __periodic_clean() -> infinite loop
        """
        while True:
            ## make sure the age of tiles never exceeds 4/3 maxage
            time.sleep(self.__maxage/3)

            with self.__lock:
                while self.__maxage > 0 and self.__discard_queue and \
                      time.time() - self.__atime[self.__discard_queue[0]] \
                        > self.__maxage:
                    tile_id = self.__discard_queue[0]
                    del self[tile_id]


    def __clean(self):
        """Remove the least recently used tiles based on maxsize.

        __clean() -> None
        """
        with self.__lock:
            while self.__maxsize > 0 and self.__num_tiles > self.__maxsize:
                tile_id = self.__discard_queue[0]
                del self[tile_id]


    def __setitem__(self, tile_id, tile):
        with self.__lock:
            if tile_id in self:
                if tile is None:
                    ## don't replace an existing tile with a None tile
                    return
                else:
                    del self[tile_id]

            self.__d[tile_id] = tile

            if self.__mortal(tile_id, tile):
                self.__discard_queue.append(tile_id)
                self.__atime[tile_id] = int(time.time())
                self.__num_tiles += 1

                self.__clean()

            elif tile_id not in self.__d:
                self.__d[tile_id] = None


    def __delitem__(self, tile_id):
        with self.__lock:
            if self.__mortal(tile_id, self.__d[tile_id]):
                self.__discard_queue.remove(tile_id)
                del self.__atime[tile_id]
                self.__num_tiles -= 1

            if tile_id in self.__maxaccesses:
                del self.__maxaccesses[tile_id]

            del self.__d[tile_id]


    def __contains__(self, tile_id):
        with self.__lock:
            return tile_id in self.__d


    def purge(self):
        """Purge all tiles from the cache.

        purge() -> None
        """
        self.__d = {}
        self.__atime = {}
        self.__anum = {}
        self.__maxaccesses = {}
        self.__discard_queue = deque()
        self.__num_tiles = 0
