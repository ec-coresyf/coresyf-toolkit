#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Name: irmad.py
#   Purpose: Perfrom IR-MAD change detection on bitemporal, multispectral
#            imagery 

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

import tools.auxil as auxil
import tools.image as img
import numpy as np    
from scipy import linalg, stats 
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly, GDT_Float32
import os, sys, time
import matplotlib.pyplot as plt

gdal.AllRegister()

def radcal(opts):
    ''' Perform IR-MAD based PIF identification'''
    piffile = os.path.join(opts.workdir, \
        "pif_"+os.path.basename(os.path.splitext(opts.reffile)[0]+".tif"))

    outfile = os.path.join(opts.workdir, \
        "cal_"+os.path.basename(os.path.splitext(opts.infile)[0]+".tif"))

    pifs = piffile # TODO keep PIFS in memory

    inDataset1 = img.open_raster(opts.reffile)
    col1 = inDataset1.RasterXSize
    row1 = inDataset1.RasterYSize    
    band1 = inDataset1.RasterCount
 
    inDataset2 = img.open_raster(opts.infile)
    col2 = inDataset2.RasterXSize
    row2 = inDataset2.RasterYSize    
    band2 = inDataset2.RasterCount

    pos = opts.bands
    bands = len(pos)
    cols = col1
    rows = row1

    # TODO Set adjustable penalties - not seen improve from default
    penalty = 0.0
    
    # TODO Allow selection of pif identifcation area
    x10 = y10 = x20 = y20 = 0


    if (row1 != row2) or (col1 != col2) or (band1 != band2):
    # if (row1 != row2) or (col1 != col2) or (band1 != band2) or (len(pos) != band1):
        print("IR-MAD image size mismatch")
        sys.exit(1)

    cpm = auxil.Cpm(2*bands)    
    delta = 1.0
    oldrho = np.zeros(bands)     
    itr = 0
    tile = np.zeros((cols,2*bands))
    sigMADs = 0
    means1 = 0
    means2 = 0
    A = 0
    B = 0
    rasterBands1 = []
    rasterBands2 = [] 
    for b in pos:
        rasterBands1.append(inDataset1.GetRasterBand(b)) 
        rasterBands2.append(inDataset2.GetRasterBand(b))
              
    while (delta > 0.001) and (itr < 100):   
#      spectral tiling for statistics
        for row in range(rows):
            for k in range(bands):
                tile[:,k] = rasterBands1[k].ReadAsArray(x10,y10+row,cols,1)
                tile[:,bands+k] = rasterBands2[k].ReadAsArray(x20,y20+row,cols,1)
#          eliminate no-data pixels (assuming all zeroes)                  
            tst1 = np.sum(tile[:,0:bands],axis=1) 
            tst2 = np.sum(tile[:,bands::],axis=1) 
            idx1 = set(np.where(  (tst1>0)  )[0]) 
            idx2 = set(np.where(  (tst2>0)  )[0]) 
            idx = list(idx1.intersection(idx2))    
            if itr>0:
                mads = np.asarray((tile[:,0:bands]-means1)*A - (tile[:,bands::]-means2)*B)
                chisqr = np.sum((mads/sigMADs)**2,axis=1)
                wts = 1-stats.chi2.cdf(chisqr,[bands])
                cpm.update(tile[idx,:],wts[idx])
            else:
                cpm.update(tile[idx,:])               
#     weighted covariance matrices and means 
        S = cpm.covariance() 
        means = cpm.means()    
#     reset prov means object           
        cpm.__init__(2*bands)  
        s11 = S[0:bands,0:bands]
        s11 = (1-penalty)*s11 + penalty*np.eye(bands)
        s22 = S[bands:,bands:] 
        s22 = (1-penalty)*s22 + penalty*np.eye(bands)
        s12 = S[0:bands,bands:]
        s21 = S[bands:,0:bands]        
        c1 = s12*linalg.inv(s22)*s21 
        b1 = s11
        c2 = s21*linalg.inv(s11)*s12
        b2 = s22
#     solution of generalized eigenproblems 
        if bands>1:
            mu2a,A = auxil.geneiv(c1,b1)                
            mu2b,B = auxil.geneiv(c2,b2)               
#          sort a   
            idx = np.argsort(mu2a)
            A = A[:,idx]        
#          sort b   
            idx = np.argsort(mu2b)
            B = B[:,idx] 
            mu2 = mu2b[idx]
        else:
            mu2 = c1/b1
            A = 1/np.sqrt(b1)
            B = 1/np.sqrt(b2)   
#      canonical correlations             
        mu = np.sqrt(mu2)
        a2 = np.diag(A.T*A)
        b2 = np.diag(B.T*B)
        sigma = np.sqrt( (2-penalty*(a2+b2))/(1-penalty)-2*mu )
        rho=mu*(1-penalty)/np.sqrt( (1-penalty*a2)*(1-penalty*b2) )
#      stopping criterion
        delta = max(abs(rho-oldrho))
        oldrho = rho  
#      tile the sigmas and means             
        sigMADs = np.tile(sigma,(cols,1)) 
        means1 = np.tile(means[0:bands],(cols,1)) 
        means2 = np.tile(means[bands::],(cols,1))
#      ensure sum of positive correlations between X and U is positive
        D = np.diag(1/np.sqrt(np.diag(s11)))  
        s = np.ravel(np.sum(D*s11*A,axis=0)) 
        A = A*np.diag(s/np.abs(s))          
#      ensure positive correlation between each pair of canonical variates        
        cov = np.diag(A.T*s12*B)    
        B = B*np.diag(cov/np.abs(cov))          
        itr += 1                 
# write results to disk

    if (opts.debug):
        # TODO keep pifs in memory, only dump if debug
        timestr = time.strftime("%Y%m%d%H%M%S")
        piffile = os.path.join(opts.workdir, timestr+'_pifs.tif')

    driver = gdal.GetDriverByName('GTiff')    
    outDataset = driver.Create(piffile,cols,rows,bands+1,GDT_Float32)
    projection = inDataset1.GetProjection()
    geotransform = inDataset1.GetGeoTransform()
    if geotransform is not None:
        gt = list(geotransform)
        gt[0] = gt[0] + x10*gt[1]
        gt[3] = gt[3] + y10*gt[5]
        outDataset.SetGeoTransform(tuple(gt))
    if projection is not None:
        outDataset.SetProjection(projection)            
    outBands = [] 
    for k in range(bands+1):
        outBands.append(outDataset.GetRasterBand(k+1))   
    for row in range(rows):
        for k in range(bands):
            tile[:,k] = rasterBands1[k].ReadAsArray(x10,y10+row,cols,1)
            tile[:,bands+k] = rasterBands2[k].ReadAsArray(x20,y20+row,cols,1)       
        mads = np.asarray((tile[:,0:bands]-means1)*A - (tile[:,bands::]-means2)*B)
        chisqr = np.sum((mads/sigMADs)**2,axis=1) 
        for k in range(bands):
            outBands[k].WriteArray(np.reshape(mads[:,k],(1,cols)),0,row)
        outBands[bands].WriteArray(np.reshape(chisqr,(1,cols)),0,row)                        
    for outBand in outBands: 
        outBand.FlushCache()

    #===========================#
    # Radiometric normalization #
    #===========================#

    inDataset3 = gdal.Open(piffile,GA_ReadOnly)     
    cols = inDataset3.RasterXSize
    rows = inDataset3.RasterYSize    
    imadbands = inDataset3.RasterCount

    x30 = y30 = 0
    if (row1 != rows) or (col1 != cols):
        print("RADCAL image size mismatch")
        exit(1)

# no-change threshold    
    ncpThresh = opts.ncp    
    chisqr = inDataset3.GetRasterBand(imadbands).ReadAsArray(x30,y30,cols,rows).ravel()
    ncp = 1 - stats.chi2.cdf(chisqr,[imadbands-1])
    idx = np.where(ncp>ncpThresh)[0]
#  split train/test in ratio 2:1 
    tmp = np.asarray(range(len(idx)))
    tst = idx[np.where(np.mod(tmp,3) == 0)]
    trn = idx[np.where(np.mod(tmp,3) > 0)]
    
    print '========================================='
    print '             RADCAL'
    print '========================================='
    print time.asctime()     
    print 'reference: '+os.path.basename(opts.reffile)
    print 'target   : '+os.path.basename(opts.infile)
    print 'no-change probability threshold: '+str(ncpThresh)
    print 'no-change pixels (train): '+str(len(trn))
    print 'no-change pixels (test): '+str(len(tst))           
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
        print '--------------------'
        print 'spectral band:      ', k
        print 'slope:              ', b
        print 'intercept:          ', a
        print 'correlation:        ', R
        print 'means(tgt,ref,nrm): ', np.mean(y[tst]),np.mean(x[tst]),np.mean(a+b*y[tst])
        print 't-test, p-value:    ', stats.ttest_rel(x[tst], a+b*y[tst])
        print 'vars(tgt,ref,nrm)   ', np.var(y[tst]),np.var(x[tst]),np.var(a+b*y[tst])
        print 'F-test, p-value:    ', auxil.fv_test(x[tst], a+b*y[tst])
        aa.append(a)
        bb.append(b)   
        outBand = outDataset.GetRasterBand(i)
        outBand.WriteArray(np.resize(a+b*y,(rows,cols)),0,0) 
        outBand.FlushCache()
        if i <= 10:
            plt.figure(i)    
            ymax = max(y[idx]) 
            xmax = max(x[idx])      
            plt.plot(y[idx],x[idx],'k.',[0,ymax],[a,a+b*ymax],'k-')
            plt.axis([0,ymax,0,xmax])
            plt.title('Band '+str(k))
            plt.xlabel('Target')
            plt.ylabel('Reference')        
        i += 1
    outDataset = None
    print 'result written to: '+outfile        
    if opts.fsfile is not None:
        path = os.path.dirname(opts.fsfile)
        basename = os.path.basename(opts.fsfile)
        root, ext = os.path.splitext(basename)
        fsoutfile = path+'/'+root+'_norm'+ext        
        print 'normalizing '+opts.fsfile+'...' 
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
        print 'result written to: '+fsoutfile
    plt.show()
    print '-------done-----------------------------'
    


    inDataset1 = None
    inDataset2 = None
    inDataset3 = None

    return pifs


def main():
    pass


if __name__ == "__main__":
   
    main()