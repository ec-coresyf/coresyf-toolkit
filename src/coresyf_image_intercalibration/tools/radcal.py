#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Name: irmad.py
#  Purpose:  Automatic radiometric normalization
#
#  Copyright (c) 2013, Mort Canty
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
'''
@summary:
This module performs Relative Radiative Normalization of a target image against a
reference image based on a pseudo invariant feature (PIF) file created by irmad.py

@info:
Adapted from https://github.com/mortcanty/CRCPython/blob/master/src/CHAPTER9/radcal.py

Morton J. Canty (2014) Image Analysis, Classification and Change Detection in Remote
Sensing. Third Edition.
'''

import tools.auxil as auxil
import os, sys, time
import tools.image as img
import numpy as np    
from scipy import stats
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32
# import matplotlib.pyplot as plt 
import logging

gdal.AllRegister()

def radcal(opts):
    ''' Perform radiometric normalization'''

    logger = logging.getLogger('intercal')
    logger.info("Entering RADCAL module")

    piffile = os.path.join(opts.workdir, \
        "pif_"+os.path.basename(os.path.splitext(opts.reffile)[0]+".tif"))

    outfile = os.path.join(opts.workdir, \
        "cal_"+os.path.basename(os.path.splitext(opts.infile)[0]+".tif"))

    pifs = piffile # TODO keep PIFS in memory

   # input reference image
    logger.info('Reference image: %s', opts.reffile)
    inDataset1 = img.open_raster(opts.reffile)
    col1 = inDataset1.RasterXSize
    row1 = inDataset1.RasterYSize    
    band1 = inDataset1.RasterCount
 
    # input target image
    logger.info('Uncalibrated image: %s', opts.infile)
    inDataset2 = img.open_raster(opts.infile)
    col2 = inDataset2.RasterXSize
    row2 = inDataset2.RasterYSize    
    band2 = inDataset2.RasterCount

    pos = opts.bands
    bands = len(pos)
    cols = col1
    rows = row1
    
    # TODO Allow selection of pif identification area
    x10 = y10 = x20 = y20 = 0

    if (row1 != row2) or (col1 != col2) or (band1 != band2):
    # if (row1 != row2) or (col1 != col2) or (band1 != band2) or (len(pos) != band1):
        print("RADCAL input image size mismatch")
        sys.exit(1)

    # input PIF identification file
    logger.info('Using PIF file: %s', piffile)
    inDataset3 = gdal.Open(piffile,GA_ReadOnly)     
    cols = inDataset3.RasterXSize
    rows = inDataset3.RasterYSize    
    imadbands = inDataset3.RasterCount

    x30 = y30 = 0
    if (row1 != rows) or (col1 != cols):
        print("RADCAL PIF image size mismatch")
        exit(1)

    # no-change threshold    
    ncpThresh = opts.ncp    
    chisqr = inDataset3.GetRasterBand(imadbands).ReadAsArray(x30,y30,cols,rows).ravel()
    ncp = 1 - stats.chi2.cdf(chisqr,[imadbands-1])
    idx = np.where(ncp>ncpThresh)[0]
    # split train/test in ratio 2:1 
    tmp = np.asarray(range(len(idx)))
    tst = idx[np.where(np.mod(tmp,3) == 0)]
    trn = idx[np.where(np.mod(tmp,3) > 0)]
    
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
    aa = []
    bb = []  
    i = 1
    for k in pos:
        x = inDataset1.GetRasterBand(k).ReadAsArray(x10,y10,cols,rows).astype(float).ravel()
        y = inDataset2.GetRasterBand(k).ReadAsArray(x20,y20,cols,rows).astype(float).ravel() 
        b,a,R = auxil.orthoregress(y[trn],x[trn])
        logger.info('--------------------')
        logger.info('spectral band:      %s', k)
        logger.info('slope:              %s', b)
        logger.info('intercept:          %s', a)
        logger.info('correlation:        %s', R)
        logger.info('means(tgt,ref,nrm): %s %s %s', np.mean(y[tst]),np.mean(x[tst]),np.mean(a+b*y[tst]))
        logger.info('t-test, p-value:    %s', stats.ttest_rel(x[tst], a+b*y[tst]))
        logger.info('vars(tgt,ref,nrm)   %s %s %s', np.var(y[tst]),np.var(x[tst]),np.var(a+b*y[tst]))
        logger.info('F-test, p-value:    %s', auxil.fv_test(x[tst], a+b*y[tst]))
        aa.append(a)
        bb.append(b)   
        outBand = outDataset.GetRasterBand(i)
        outBand.WriteArray(np.resize(a+b*y,(rows,cols)),0,0) 
        outBand.FlushCache()
        """ if opts.debug:
            if i <= 10:
                plt.figure(i)    
                ymax = max(y[idx]) 
                xmax = max(x[idx])      
                plt.plot(y[idx],x[idx],'k.',[0,ymax],[a,a+b*ymax],'k-')
                plt.axis([0,ymax,0,xmax])
                plt.title('Band '+str(k))
                plt.xlabel('Target')
                plt.ylabel('Reference') """        
        i += 1
    outDataset = None
    logger.info('Wrote calibrated image: %s', outfile)
            
    if opts.fsfile is not None:
        path = os.path.dirname(opts.fsfile)
        basename = os.path.basename(opts.fsfile)
        root, ext = os.path.splitext(basename)
        fsoutfile = path+'/'+root+'_norm'+ext        
        
        fsDataset = gdal.Open(opts.fsfile,GA_ReadOnly)
        cols = fsDataset.RasterXSize
        rows = fsDataset.RasterYSize    
        driver = fsDataset.GetDriver()
        outDataset = driver.Create(fsoutfile,cols,rows,bands,GDT_Float32)
        projection = fsDataset.GetProjection()
        geotransform = fsDataset.GetGeoTransform()
        if geotransform is not None:
            outDataset.SetGeoTransform(geotransform)
        if projection is not None:
            outDataset.SetProjection(projection) 
        j = 0
        for k in pos:
            inBand = fsDataset.GetRasterBand(k)
            outBand = outDataset.GetRasterBand(j+1)
            for i in range(rows):
                y = inBand.ReadAsArray(0,i,cols,1)
                outBand.WriteArray(aa[j]+bb[j]*y,0,i) 
            outBand.FlushCache() 
            j += 1      
        outDataset = None
        logger.info('Wrote calibrated image: %s', fsoutfile)
    
    """if opts.debug:
        plt.show()"""
    
    inDataset1 = None
    inDataset2 = None
    inDataset3 = None

    return pifs


def main():
    pass


if __name__ == "__main__":  
    main()

