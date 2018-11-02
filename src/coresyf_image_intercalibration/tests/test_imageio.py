#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for raster image I/O functions"""

import tools.image as img
import numpy as np
from osgeo import osr
import os
import pytest


def test_geotiff_is_valid_format():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_tags.tif')
    assert img.open_raster(testfile) is not None

def test_bbox_coordinates_latlon():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_tags.tif')
    coords = img.get_bbox_coords(img.open_raster(testfile))
    assert pytest.approx(coords['ulx']) == 150.9100000
    assert pytest.approx(coords['uly']) == -34.1700000
    assert pytest.approx(coords['lrx']) == 150.9491667
    assert pytest.approx(coords['lry']) == -34.2300000

def test_bbox_coordinates_utm():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_proj.tif')
    coords = img.get_bbox_coords(img.open_raster(testfile))
    assert pytest.approx(coords['ulx']) == -(117+38.0/60.0+30.24/3600.0)
    assert pytest.approx(coords['uly']) == 33+56.0/60.0+37.8/3600.0
    assert pytest.approx(coords['lrx']) == -(117+18.0/60.0+31.15/3600.0)
    assert pytest.approx(coords['lry']) == 33+39.0/60.0+54.26/3600.0

def test_bbox_coordinates_match():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_tags.tif')
    coords = img.get_bbox_coords(img.open_raster(testfile))
    assert coords['ulx'] == coords['tlg'][0]
    assert coords['uly'] == coords['tlg'][1]
    assert coords['lrx'] == coords['brg'][0]
    assert coords['lry'] == coords['brg'][1]

def test_bbox_other_params():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_tags.tif')
    coords = img.get_bbox_coords(img.open_raster(testfile))
    assert coords['xres'] == -coords['yres']
    assert coords['xrot'] == coords['yrot'] == 0
    assert coords['cols'] == 47
    assert coords['rows'] == 72

def test_get_band_info():
    testfile = os.path.join(os.path.dirname(__file__), 'data/small_tif_tags.tif')
    info = img.get_band_info(img.open_raster(testfile))
    assert pytest.approx(info['min'] == -3.5677621364593506)
    assert pytest.approx(info['max'] == -0.3097841441631317)
    assert pytest.approx(info['mean'] == -2.339052484655958)
    assert pytest.approx(info['std'] == 0.37911647974348833)
    assert info['blocksize'] == [47, 43]
    assert info['ndv'] == 0.0

def test_raster_write():
    array = np.array([[0.1, 0.2, 0.3, 0.4],
                      [0.2, 0.3, 0.4, 0.5],
                      [0.3, 0.4, 0.5, 0.6],
                      [0.4, 0.5, 0.6, 0.7],
                      [0.5, 0.6, 0.7, 0.8]], dtype=np.float32)

    lat = np.array([[10.0, 10.0, 10.0, 10.0],
                    [9.5, 9.5, 9.5, 9.5],
                    [9.0, 9.0, 9.0, 9.0],
                    [8.5, 8.5, 8.5, 8.5],
                    [8.0, 8.0, 8.0, 8.0]])

    lon = np.array([[20.0, 20.5, 21.0, 21.5],
                    [20.0, 20.5, 21.0, 21.5],
                    [20.0, 20.5, 21.0, 21.5],
                    [20.0, 20.5, 21.0, 21.5],
                    [20.0, 20.5, 21.0, 21.]])

    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows, ncols = np.shape(array)
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    transform = (xmin, xres, 0, ymax, 0, -yres)

    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    projection = src.ExportToWkt()

    testfile = 'test.tif'
    img.write_raster(testfile, array, transform, projection)

    ds = img.open_raster(testfile)
    stats = img.get_band_info(ds)
    assert pytest.approx(stats['min']) == 0.1
    assert pytest.approx(stats['max']) == 0.8
    assert pytest.approx(stats['mean']) == 0.45
    assert pytest.approx(stats['std']) == 0.18027756

    os.remove(testfile)
