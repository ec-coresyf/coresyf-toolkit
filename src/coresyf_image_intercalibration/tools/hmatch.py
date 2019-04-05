#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Name: hmatch.py
#  Purpose: Perform histogram matching of a target image to a
#  reference image i.e. apply a transformation of the target
#  image so that the histogram matches the histogram of the
#  reference image.
'''
@summary:
This module uses histogram matching between target and reference
images as a relative detector calibration technique.

This is a normalization routine best suited when the images are
acquired over the same location, but by different sensors, global
illumination or atmospheric conditions

@info:
Description https://en.wikipedia.org/wiki/Histogram_matching
'''

import tools.image as img
import os, sys
import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32
# import matplotlib.pyplot as plt 
import logging

def hmatch(opts):
    '''Perform histogram matching'''

    logger = logging.getLogger('intercal')
    logger.info("Entering Histogram Match module")

    # input images
    logger.info('Reference image: %s', opts.reffile)
    inDataset1 = img.open_raster(opts.reffile)
    col1 = inDataset1.RasterXSize
    row1 = inDataset1.RasterYSize    
    band1 = inDataset1.RasterCount
 
    logger.info('Uncalibrated image: %s', opts.infile)
    inDataset2 = img.open_raster(opts.infile)
    col2 = inDataset2.RasterXSize
    row2 = inDataset2.RasterYSize    
    band2 = inDataset2.RasterCount

    if (row1 != row2) or (col1 != col2) or (band1 != band2):
    # if (row1 != row2) or (col1 != col2) or (band1 != band2) or (len(pos) != band1):
        print("HMATCH image size mismatch")
        sys.exit(1)

    pos = opts.bands
    bands = len(pos)
    cols = col1
    rows = row1

    x10 = y10 = x20 = y20 = 0

    # output image file
    outfile = os.path.join(opts.workdir, \
        "cal_"+os.path.basename(os.path.splitext(opts.infile)[0]+".tif"))

    driver = gdal.GetDriverByName(opts.format)    
    outDataset = driver.Create(outfile,cols,rows,bands,GDT_Float32) 
    projection = inDataset1.GetProjection()
    geotransform = inDataset1.GetGeoTransform()
    if geotransform is not None:
        gt = list(geotransform)
        gt[0] = gt[0] + x10*gt[1]
        gt[3] = gt[3] + y10*gt[5]
        outDataset.SetGeoTransform(tuple(gt))
    if projection is not None:
        outDataset.SetProjection(projection) 
    i = 1
    # process image
    for band in pos:
        refband = inDataset1.GetRasterBand(band).ReadAsArray(x10,y10,cols,rows).astype(float).ravel()
        inpband = inDataset2.GetRasterBand(band).ReadAsArray(x20,y20,cols,rows).astype(float).ravel() 
        gray_levels = 256*256
        refhist, refbin_edges = np.histogram(refband, bins=gray_levels)
        inphist, inpbin_edges = np.histogram(inpband, bins=gray_levels)
        refcdf = np.cumsum(refhist)
        inpcdf = np.cumsum(inphist)

        outband = np.zeros(len(inpband))
        for i in range(len(inpband)):
            index = np.searchsorted(refcdf,[inpcdf[inpband[i]]])
            outband[i] = index[0]

        outDataset.GetRasterband(i).WriteArray(outband.reshape((cols,rows)))
        outband.FlushCache()

        refbin_edges = inpbin_edges
        inpbin_edges = refbin_edges

    # TODO  Output bands here

    outDataset = None
    logger.info('Wrote calibrated image: %s', outfile)

    inDataset1 = None
    inDataset2 = None

def main():
    pass


if __name__ == "__main__":  
    main()