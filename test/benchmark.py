#!/usr/bin/python
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

"""
Benchmark the processing and display of a given image
USAGE
  benchmark.py image
e.g.:
  for file in images/*; do ./benchmark.py $file; done
"""

import sys
import os
import tempfile
import time
import shutil

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from PyQt4 import QtCore, QtGui

import pyzui.tilemanager as TileManager
import pyzui.tilestore as TileStore
from pyzui.magickconverter import MagickConverter
from pyzui.ppm import PPMTiler, read_ppm_header
from pyzui.qzui import QZUI
import pyzui.scene as Scene
from pyzui.tiledmediaobject import TiledMediaObject

def mem(size='rss'):
    """Quick and dirty function to get the memory usage (in KB) of the current
    process:
    rss: resident memory
    rsz: resident + text memory
    vsz: virtual memory

    Adapted from <http://snipplr.com/view/6460/> by Florian Leitner
    """
    return int(os.popen("ps -p %d -o %s | tail -1" %
        (os.getpid(), size)).read())


def benchmark(filename, ppmfile):
    print "Benchmarking %s ..." % os.path.basename(filename)

    base_mem = mem()

    ## conversion
    c = MagickConverter(filename, ppmfile)
    start_time = time.time()
    print "Converting to PPM...",
    sys.stdout.flush()
    c.run()
    end_time = time.time()
    print "Done: took %.2fs" % (end_time - start_time)
    del c

    ## metadata
    f = open(ppmfile, 'rb')
    w,h = read_ppm_header(f)
    f.close()
    print "Dimensions: %dx%d, %.2f megapixels" % (w, h, w * h * 1e-6)
    del f, w, h

    ## tiling
    t = PPMTiler(ppmfile)
    start_time = time.time()
    print "Tiling...",
    sys.stdout.flush()
    t.run()
    end_time = time.time()

    ## in general, python doesn't necessarily return allocated memory to the OS
    ## (see <http://effbot.org/pyfaq/
    ## why-doesnt-python-release-the-memory-when-i-delete-a-large-object.htm>)
    ## so the current memory usage is likely to be approximately equal to the
    ## peak memory usage during tiling
    ## however, it would probably be better to periodically check memory usage
    ## while the tiler is running and maintain a max value
    end_mem = mem()

    print "Done: took %.2fs consuming %.2fMB RAM" % \
        ((end_time - start_time), (end_mem - base_mem) * 1e-3)
    del t

    ## zooming
    viewport_w = 800
    viewport_h = 600
    print "Viewport: %dx%d" % (viewport_w, viewport_h)
    zoom_amount = 5.0
    print "Zoom amount: %.1f" % zoom_amount

    qzui = QZUI()
    qzui.framerate = None
    qzui.resize(viewport_w, viewport_h)
    qzui.show()

    scene = Scene.new()
    qzui.scene = scene
    obj = TiledMediaObject(ppmfile, scene, True)
    scene.add(obj)
    obj.fit((0, 0, viewport_w, viewport_h))

    start_time = time.time()
    print "Zooming (cold)...",
    sys.stdout.flush()
    num_frames = 100
    for i in xrange(num_frames):
        qzui.repaint()
        scene.centre = (viewport_w/2, viewport_h/2)
        scene.zoom(zoom_amount/num_frames)
    end_time = time.time()
    print "Done: %d frames took %.2fs, mean framerate %.2f FPS" % \
        (num_frames, (end_time - start_time),
        num_frames / (end_time - start_time))

    scene.zoom(-zoom_amount)
    start_time = time.time()
    print "Zooming (warm)...",
    sys.stdout.flush()
    num_frames = 100
    for i in xrange(num_frames):
        qzui.repaint()
        scene.centre = (viewport_w/2, viewport_h/2)
        scene.zoom(zoom_amount/num_frames)
    end_time = time.time()
    print "Done: %d frames took %.2fs, mean framerate %.2f FPS" % \
        (num_frames, (end_time - start_time),
        num_frames / (end_time - start_time))


def main():
    TileManager.init()
    TileStore.tile_dir = tempfile.mkdtemp()
    app = QtGui.QApplication(sys.argv)

    filename = os.path.abspath(sys.argv[1])
    ppmfile = tempfile.mkstemp('.ppm')[1]

    try:
        benchmark(filename, ppmfile)
        # import cProfile
        # cProfile.run("benchmark(%s, %s)" % (repr(filename), repr(ppmfile)))
    finally:
        shutil.rmtree(TileStore.tile_dir, ignore_errors=True)
        os.unlink(ppmfile)
if __name__ == '__main__': main()
