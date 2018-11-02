#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osgeo import gdal
from osgeo import osr
import numpy as np
import os.path, sys

gdal.UseExceptions()


def write_raster(outfile, array, transform, projection, driver='GTiff'):
    # write out raster using metadata provided as argument
    driver = gdal.GetDriverByName(driver)
    if driver is None:
        raise ValueError("Cannot find %s driver" % driver)
    
    nrows, ncols = np.shape(array)
    ds = driver.Create(outfile,ncols,nrows,1,gdal.GDT_Float32)
    ds.GetRasterBand(1).WriteArray(array)
    ds.SetGeoTransform(transform)
    ds.SetProjection(projection)
    ds = None

def read_raster(infile)
    ds = open_raster(infile)
    meta = get_metadata(ds)
    # TODO add read array and unit test


def open_raster(infile):
    try:
        ds = gdal.Open(infile, gdal.GA_ReadOnly)
    except RuntimeError, e:
        print('Unable to open %s' % path)
        print e
        sys.exit(1)
    return ds


def get_bbox_coords(ds):
    # returns bounding box coordinates and resolution
    ulx, xres, xrot, uly, yrot, yres = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    lrx = ulx + cols * xres + rows * xrot
    lry = uly + rows * yres + cols * yrot
    tlg = brg = None  # corners in lat/lon
    if osr.SpatialReference(ds.GetProjection()).IsProjected:
        src = osr.SpatialReference()
        src.ImportFromWkt(ds.GetProjection())
        tgt = osr.SpatialReference()
        tgt.ImportFromEPSG(4326)
        tlg = coord_transform(src, tgt, ulx, uly)[0:2]
        brg = coord_transform(src, tgt, lrx, lry)[0:2]
    bbox = {
        'ulx':  ulx,  'uly':  uly,
        'lrx':  lrx,  'lry':  lry,
        'xres': xres, 'yres': yres,
        'xrot': xrot, 'yrot': yrot,
        'cols': cols, 'rows': rows,
        'tlg':  tlg,  'brg':  brg
    }
    return bbox


def get_band_info(ds, nband=1):
    # return statistics and metadata as dictionary
    try:
        band = ds.GetRasterBand(nband)
    except RuntimeError, e:
        print('No band %i found' % nband)
        print e
        sys.exit(1)
    bmin, bmax, mean, std = band.GetStatistics(0,1)
    info = {
        'min': bmin,
        'max': bmax,
        'mean': mean,
        'std': std,
        'ndv': band.GetNoDataValue(),
        'blocksize': band.GetBlockSize()
    }
    return info


def get_metadata(ds):
    # create a dictionary from metadata values
    bands = ds.RasterCount
    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    meta = {'bbox': get_bbox_coords(ds),
            'info': get_band_info(ds),
            'numbands': bands,
            'transform': transform,
            'projection': projection
            }
    return meta


def coord_transform(src, tgt, x, y):
    # transform points from source to target projection
    transform = osr.CoordinateTransformation(src, tgt)
    return transform.TransformPoint(x, y)


