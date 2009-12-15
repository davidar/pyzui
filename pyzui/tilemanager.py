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

"""The TileManager is responsible for requesting tiles from TileProviders,
caching them in memory, and providing them to MediaObjects when requested
to do so.

It is also responsible for creating new tiles from available ones when
no tiles of the requested resolution are available.
"""

import logging

import Image
from PyQt4 import QtCore, QtGui

import tilestore as TileStore
from tilecache import TileCache
from statictileprovider import StaticTileProvider
from osmtileprovider import OSMTileProvider
from globalmosaictileprovider import GlobalMosaicTileProvider
from mandeltileprovider import MandelTileProvider
from ferntileprovider import FernTileProvider

def init(total_cache_size=192):
    """Initialise the TileManager. This **must** be called before any other
    functions are called.

    init() -> None
    """
    global __tilecache, __temptilecache, __tp_static, __tp_dynamic, __logger

    __tilecache =     TileCache(0.8 * total_cache_size)
    __temptilecache = TileCache(0.2 * total_cache_size)

    __tp_static = StaticTileProvider(__tilecache)
    __tp_static.start()

    __tp_dynamic = {
        'dynamic:osm':    OSMTileProvider(__tilecache),
        'dynamic:gm':     GlobalMosaicTileProvider(__tilecache),
        'dynamic:mandel': MandelTileProvider(__tilecache),
        'dynamic:fern':   FernTileProvider(__tilecache),
    }
    for tp in __tp_dynamic.itervalues():
        tp.start()

    __logger = logging.getLogger("TileManager")

def load_tile(tile_id):
    """Request that the tile identified by `tile_id` be loaded into the
    tilecache.

    load_tile(tuple<string,int,int,int>) -> None
    """

    media_id = tile_id[0]

    if media_id in __tp_dynamic:
        __tp_dynamic[media_id].request(tile_id)
    else:
        __tp_static.request(tile_id)


def get_tile(tile_id):
    """Return the requested tile identified by `tile_id`.

    If the tile is not available in the tilecache, one of three errors will be
    raised: `MediaNotTiled`, `TileNotLoaded`, or `TileNotAvailable`

    get_tile(tuple<string,int,int,int>) -> Tile
    """

    if tile_id[1] < 0:
        ## negative tilelevel
        raise TileNotAvailable

    try:
        tile = __tilecache[tile_id]
    except KeyError:
        media_id = tile_id[0]
        if tiled(media_id):
            load_tile(tile_id)
            raise TileNotLoaded
        else:
            raise MediaNotTiled

    if tile:
        return tile
    else:
        raise TileNotAvailable


def cut_tile(tile_id, tempcache=0):
    """Create a tile from resizing and cropping those loaded into the tile
    cache. Returns a tuple containing the tile, and a bool `final` which is
    False iff the tile is not the greatest resolution possible and should
    therefore not be cached indefinitely.

    If `tempcache` > 0, then tiles with `final`=False will cached in the
    TileCache, but will expire after they have been accessed `tempcache` times.

    This function should only be called if a `TileNotLoaded` or
    `TileNotAvailable` error has been encountered.

    cut_tile(tuple<string,int,int,int>, int) -> tuple<Tile,bool>

    Precondition: the (0,0,0) tile exists for the given media
    Precondition: the requested tile doesn't fall outside the bounds of the
    image
    """

    media_id, tilelevel, row, col = tile_id
    tilesize = get_metadata(media_id, 'tilesize')

    if tempcache <= 0:
        ## purge temporary tiles
        __temptilecache.purge()

    if tilelevel < 0:
        ## resize the (0,0,0) tile
        tile000 = __tilecache[media_id,0,0,0]
        scale = 2**tilelevel
        tile = tile000.resize(
            int(tile000.size[0] * scale), int(tile000.size[1] * scale))
        final = True
    else:
        big_tile_id = (media_id, tilelevel-1, row//2, col//2)
        try:
            return get_tile(tile_id), True
        except TileNotLoaded:
            final = False
            try:
                ## check if there is a temporary cut tile in the cache
                return __temptilecache[tile_id], False
            except KeyError:
                ## don't worry if there isn't
                pass
            big_tile = cut_tile(big_tile_id)[0]
        except TileNotAvailable:
            big_tile, final = cut_tile(big_tile_id)

        if col % 2 == 0:
            x1 = 0
            x2 = min(tilesize/2, big_tile.size[0])
        else:
            x1 = tilesize/2
            x2 = big_tile.size[0]

        if row % 2 == 0:
            y1 = 0
            y2 = min(tilesize/2, big_tile.size[1])
        else:
            y1 = tilesize/2
            y2 = big_tile.size[1]

        tile = big_tile.crop((x1, y1, x2, y2))
        tile = tile.resize(2*tile.size[0], 2*tile.size[1])

    if final:
        __tilecache[tile_id] = tile
    elif tempcache > 0:
        __temptilecache.insert(tile_id, tile, tempcache)

    return tile, final


def get_tile_robust(tile_id):
    """Will try returning the result of `get_tile`, and if that fails will
    return the result of `cut_tile`.

    This function will not raise `TileNotLoaded` or `TileNotAvailable`, but may
    raise `MediaNotTiled`.

    get_tile_robust(tuple<string,int,int,int>) -> Tile
    """
    try:
        return get_tile(tile_id)
    except (TileNotLoaded, TileNotAvailable):
        return cut_tile(tile_id)[0]


def tiled(media_id):
    """Returns True iff the media identified by `media_id` has been tiled.

    Will always return True for dynamic media.

    tiled(string) -> bool
    """
    return media_id.startswith('dynamic:') or TileStore.tiled(media_id)


def get_metadata(media_id, key):
    """Return the value associated with the given metadata `key` for the given
    `media_id`, None if there is no such value.

    get_metadata(string, string) -> object or None
    """
    if media_id in __tp_dynamic:
        tp = __tp_dynamic[media_id]
        if   key == 'filext':       return tp.filext
        elif key == 'tilesize':     return tp.tilesize
        elif key == 'aspect_ratio': return tp.aspect_ratio
        else: return None
    else:
        return TileStore.get_metadata(media_id, key)


def purge(media_id=None):
    """Purge the specified `media_id` from the `TileProvider`s. If `media_id`
    is omitted then all media will be purged.

    purge([string]) -> None

    Precondition: the media to be purged should not be active (i.e. no
    `MediaObject`s for the media should exist).
    """
    __tp_static.purge(media_id)
    for tp in __tp_dynamic.itervalues():
        tp.purge(media_id)


class MediaNotTiled(Exception):
    """Exception for when tiles are requested from a media that has not been
    tiled yet.

    This exception will never be thrown when requesting a tile from a dynamic
    media.
    """
    pass


class TileNotLoaded(Exception):
    """Exception for when tiles are requested before they have been loaded into
    the tile cache."""
    pass


class TileNotAvailable(Exception):
    """Exception for when an attempt to load the requested tile has previously
    failed."""
    pass
