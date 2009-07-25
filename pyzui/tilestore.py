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

"""Module for managing the disk-based tile storage facility."""

import os
import sha
from threading import RLock

## set the default tilestore directory, this can be overridden if required
if 'APPDATA' in os.environ:
    ## Windows
    tile_dir = os.path.join(os.environ['APPDATA'], "pyzui", "tilestore")
else:
    ## Unix
    tile_dir = os.path.join(os.path.expanduser('~'), ".pyzui", "tilestore")

## threads which intend performing disk-access-intensive activities should
## acquire this lock first to reduce stress on the disk
disk_lock = RLock()

__metadata = {}

def get_media_path(media_id):
    """Return the path to the directory containing the tiles for the media
    identified by `media_id`.

    get_media_path(string) -> string
    """
    media_hash = sha.new(media_id).hexdigest()
    media_dir = os.path.join(tile_dir, media_hash)
    return media_dir


def get_tile_path(tile_id, mkdirp=False, prefix=None, filext=None):
    """Return the path to the tile identified by `tile_id`.

    If `mkdirp` is True, then any non-existent parent directories of the tile
    will be created.

    If `prefix` is omitted, it will be set to the value returned by
    `get_media_path`.

    If `filext` is omitted, it will be set to the value returned by
    `get_metadata`.

    get_tile_path(tuple<string,int,int,int>[, bool[, string[, string]]])
    -> string

    Precondition: if `filext` is None, then the metadata file for the media
    that this tile belongs to exists and contains an entry for filext
    """

    media_id, tilelevel, row, col = tile_id

    if not prefix:
        prefix = get_media_path(media_id)

    if filext is None:
        filext = get_metadata(media_id, 'filext')

    filename = os.path.join(prefix, "%02d" % tilelevel, "%06d" % row)

    if mkdirp and not os.path.exists(filename):
        ## create parent directories
        os.makedirs(filename)

    filename = os.path.join(
        filename, "%02d_%06d_%06d.%s" % (tilelevel, row, col, filext))

    return filename


def load_metadata(media_id):
    """Load metadata from disk for the given `media_id`, and return a bool
    indicating whether the load was successful.

    load_metadata(string) -> bool
    """
    path = get_media_path(media_id)

    try:
        f = open(os.path.join(path, "metadata"), 'U')
    except IOError:
        return False

    __metadata[media_id] = {}

    for line in f:
        key, val, val_type = line.split()

        try:
            if   val_type == 'int':   val = int(val)
            elif val_type == 'bool':  val = bool(val)
            elif val_type == 'float': val = float(val)
            elif val_type == 'long':  val = long(val)
        except Exception:
            pass
        else:
            __metadata[media_id][key] = val

    f.close()

    return True


def get_metadata(media_id, key):
    """Return the value associated with the given metadata key, None if there
    is no such value.

    get_metadata(string, string) -> object or None
    """
    if media_id not in __metadata and not load_metadata(media_id):
        return None
    return __metadata[media_id].get(key)


def write_metadata(media_id, **kwargs):
    """Write the metadata given in `kwargs` for the given `media_id`.

    write_metadata(string, metadata_key=metadata_val, ...) -> None
    """
    path = get_media_path(media_id)
    f = open(os.path.join(path, "metadata"), 'w')
    for key,val in kwargs.iteritems():
        f.write("%s\t%s\t%s\n"
            % (key, str(val), type(val).__name__))
    f.close()


def tiled(media_id):
    """Return True iff the media identified by `media_id` has been tiled
    i.e. iff both a metadata file and the (0,0,0) tile exist.

    tiled(string) -> bool
    """
    path = get_media_path(media_id)
    return os.path.exists(os.path.join(path, "metadata")) and \
           os.path.exists(get_tile_path((media_id, 0, 0, 0)))
