#-------------------------------------------------------------------------
# module that convert Sentinel 1 (4 bands) rasters to single band raster 
#
#
#-------------------------------------------------------------------------
import sys
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal,osr,gdal_array
import CSAR_ImageProcessing as IP


#-----------------------------------------------------------------------------------------------------------------------
band = 4 # 1 -> R, 2 -> G, 3 -> B, 4 -> mean



path_input = "~/CoReSyF/python/Images/"
path_output = "~/CoReSyF/python/Images/"	

fname = 'Aveiro.tif'

filein = path_input + fname

# Create Uniband Image if MultiBand
fileout = IP.Convert1BandTiff(filein,band)

# verification
f = gdal.Open(fileout)
a2 = f.ReadAsArray()
print 'nb of band in output raster:', f.RasterCount
f = None
