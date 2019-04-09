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

import tools.auxil as auxil
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

    # output image file
    outfile = os.path.join(opts.workdir, \
        "cal_"+os.path.basename(os.path.splitext(opts.infile)[0]+".tif"))

    driver = gdal.GetDriverByName(opts.format)    
    outDataset = driver.Create(outfile,cols,rows,bands,GDT_Float32) 
    outDataset.SetProjection(inDataset1.GetProjection())
    outDataset.SetGeoTransform(inDataset1.GetGeoTransform())
    i = 1

    # process image
    for band in pos:
        refband = inDataset1.GetRasterBand(band).ReadAsArray().astype(float)
        refband = refband.ravel()
        inpband = inDataset2.GetRasterBand(band).ReadAsArray().astype(float)
        inpband = inpband.ravel()

        # get set of unique pixel values and corresponding index and counts
        _, bin_idx, i_counts = np.unique(inpband, return_inverse=True, return_counts=True)
        r_values, r_counts = np.unique(refband, return_counts=True)

        # take the cumsum and normalize by the numver of pixels to get the
        # empirical cumulative distribution funciton for the reference and
        # input (maps pixel values --> quantile)
        r_quantiles = np.cumsum(r_counts).astype(np.float64)
        r_quantiles /= r_quantiles[-1]
        i_quantiles = np.cumsum(i_counts).astype(np.float64)
        i_quantiles /= i_quantiles[-1]

        # interpolate linearly to find the pixel values in the input image
        # that correspond most closely to the quantities in the reference
        interp_r_values = np.interp(i_quantiles, r_quantiles, r_values)
        corrected = interp_r_values[bin_idx]

        outband = outDataset.GetRasterBand(i)
        outband.WriteArray(np.resize(corrected,(rows,cols)),0,0)

        """ if opts.debug:
            plt.figure(i)
            x1, y1 = auxil.ecdf(refband)
            x2, y2 = auxil.ecdf(inpband)
            x3, y3 = auxil.ecdf(corrected)
            plt.plot(x1, y1 * 100, '-r', lw=3, label='Reference')
            plt.plot(x2, y2 * 100, '-k', lw=3, label='Input')
            plt.plot(x3, y3 * 100, '--r', lw=3, label='Corrected')
            plt.xlabel('Pixel value')
            plt.ylabel('Cumulative %')
            plt.legend(loc=5) """

        outband.FlushCache()
        corrected = None
        i += 1

    outDataset = None
    logger.info('Wrote calibrated image: %s', outfile)

    """ if opts.debug:
            plt.show() """

    inDataset1 = None
    inDataset2 = None

def main():
    pass


if __name__ == "__main__":  
    main()