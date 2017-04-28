#!/usr/bin/env python
#==============================================================================
#                         <snap_fileFormat_test.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : File recognition
# Language  : Python (v.2.7)
#------------------------------------------------------------------------------
# Scope : (see the following docstring)
# Usage : python snap_fileFormat_test.py
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
This module recognizes and differentiates the file formats that SNAP can handle.

It will be used to automatically identify which file(s) should be open by the
GPT tool.

@info
Adapted from: 
http://remote-sensing.eu/preprocessing-of-sentinel-1-sar-data-via-snappy-python-module/
https://github.com/senbox-org/snap-examples/blob/master/snap-engine-python-scripts/src/main/python/ndvi_processor_34.py

SNAP Engine API documentation:
http://step.esa.int/docs/v5.0/apidoc/engine/

SNAP examples:
https://github.com/senbox-org/snap-engine/blob/master/snap-python/src/main/resources/snappy/examples/ 

@version: v.0.1
@author: RCCC

@note: Creating symbolic links resolves issue/warning with reading product files (OPTIONAL): 
    SNAP_HOME=~/snap
    cd $SNAP_HOME/snap/modules/lib/x86_64
    ln -s ../amd64/libjhdf.so
    ln -s ../amd64/libjhdf5.so
'''

__version__ = '0.1'


''' SYSTEM MODULES '''
import sys
sys.path.append('/home/rccc/.snap/snap-python')
import os


''' PROGRAM MODULES '''
import snappy
#print('snappy.__file__:', snappy.__file__)

from snappy import jpy
from snappy import GPF
from snappy import ProductIO


''' PROGRAM DIRECTORIES '''
PRODUCTS_DIR = "/home/rccc/Downloads/TEMP_SAR_PRODUCTS/"
RADARSAT2_DIR = '/home/rccc/Downloads/TEMP_SAR_PRODUCTS/RS2_OK871_PK6633_DK3208_FQ2_20080415_143805_HH_VV_HV_VH_SLC/'
SENT3_DIR = '/home/rccc/Downloads/TEMP_SAR_PRODUCTS/S3A_SL_1_RBT____20170202T140355_20170202T140655_20170202T150744_0179_014_039_0539_SVL_O_NR_002.SEN3/'
SENT2_DIR = '/home/rccc/Downloads/TEMP_SAR_PRODUCTS/S2A_MSIL1C_20170202T090201_N0204_R007_T34QGF_20170202T091143.SAFE/'
SENT1_DIR = '/home/rccc/Downloads/TEMP_SAR_PRODUCTS/S1B_EW_GRDM_1SDH_20170202T133833_20170202T133937_004122_007219_D680.SAFE/'


#=========================================================================================================================#
# CREATING OBJECTS FROM JAVA CLASS                                                                                        #
# Adapted from:                                                                                                           #
# https://github.com/senbox-org/snap-examples/blob/master/snap-engine-python-scripts/src/main/python/ndvi_processor_34.py #
#=========================================================================================================================#
ProductIOPlugInManager = snappy.jpy.get_type('org.esa.snap.core.dataio.ProductIOPlugInManager')
Logger = jpy.get_type('java.util.logging.Logger')
Level = jpy.get_type('java.util.logging.Level')
Arrays = jpy.get_type('java.util.Arrays')
File = jpy.get_type('java.io.File')
String = jpy.get_type('java.lang.String')
HashMap = jpy.get_type('java.util.HashMap')

Logger.getLogger('').setLevel(Level.OFF)
snappy.SystemUtils.LOG.setLevel(Level.OFF)


#=========================================================================================#
# FINDING FILE SNAP FORMAT (reads the product!!)                                          #
# Adapted from:                                                                           #
# http://remote-sensing.eu/preprocessing-of-sentinel-1-sar-data-via-snappy-python-module/ #
#=========================================================================================#
DIR_PATH = SENT1_DIR
dir_elem = os.listdir(DIR_PATH)
files    = sorted ((fa for fa in dir_elem if os.path.isfile(DIR_PATH + fa)), reverse = False)

print("Finding file format at directory:")
print(DIR_PATH)
print('   |')
for fi in files: 
    print('   |==> "' + fi + '"...')
    p = None
    try:
        # Reads data product. The method does not automatically read band data
        p = ProductIO.readProduct(DIR_PATH + fi)
    except:
        pass
    
    if p:
        print('   |     - Type, Format: ' + p.getProductType() + ', ' + ', '.join( p.getProductReader().getReaderPlugIn().getFormatNames() ) )
        print('   |     - Band Names: ' + ', '.join( p.getBandNames() )  )
        print('   |     - Raster Sizes: heigth=%d'%p.getSceneRasterHeight() + ', Width=%d'%p.getSceneRasterWidth())
    else:
        print('   |     - PRODUCT NOT FOUND!')


#=========================================================================================#
#-------------------------#
# USING SNAP FILE FILTER  #
#-------------------------#
'''
radarsat2_file = File('/home/rccc/Downloads/TEMP_SAR_PRODUCTS/RS2_OK871_PK6633_DK3208_FQ2_20080415_143805_HH_VV_HV_VH_SLC/product.xml')
sent1_file = File('/home/rccc/Downloads/TEMP_SAR_PRODUCTS/S1B_EW_GRDM_1SDH_20170202T133833_20170202T133937_004122_007219_D680.SAFE/manifest.safe')

SnapFileFilter = jpy.get_type('org.esa.snap.core.util.io.SnapFileFilter')
filter_spi = SnapFileFilter("RADARSAT-2", [".xml"], '')
print (filter_spi.accept(radarsat2_file))
'''


#---------------------------------------------------#
# Test if file is accepted by any SNAP file filter  #
# (only analyzes file extensions!! )                #
#---------------------------------------------------#
'''
dir_elem = os.listdir(RADARSAT2_DIR)
files    = sorted ((fa for fa in dir_elem if os.path.isfile(RADARSAT2_DIR + fa)), reverse = False)
print dir_elem
for fi in files:
    # Tests whether or not the given file is accepted by any file filter
    print("Testing file: " + fi + ' ...')
    reader_spi_it = ProductIOPlugInManager.getInstance().getAllReaderPlugIns()
    
    found = False
    while reader_spi_it.hasNext():
        reader_spi = reader_spi_it.next()
        filter_spi = reader_spi.getProductFileFilter()
        if filter_spi.accept(File(fi)):
            print("  Product format(s): " + ', '.join(reader_spi.getFormatNames()))
            print("  Product extension(s): " + ', '.join(reader_spi.getDefaultFileExtensions()))
            found = True
            break
    if not found: print("  Product format not found!")
'''

#-----------------#
# READER PLUGINS  #
#-----------------#
'''
reader_spi_it = ProductIOPlugInManager.getInstance().getAllReaderPlugIns()
while reader_spi_it.hasNext():
    reader_spi = reader_spi_it.next()
    print("reader_spi: " + ', '.join(reader_spi.getFormatNames()) + " (" + reader_spi.getClass().getName() + ")")
    print("          |>> file extensions: " + ', '.join(reader_spi.getDefaultFileExtensions()) )
    print("          |>> file filter: " + str(reader_spi.getProductFileFilter()) )
'''
 
#-----------------#
# WRITER PLUGINS  #
#-----------------#
'''
writer_spi_it = ProductIOPlugInManager.getInstance().getAllWriterPlugIns()
while writer_spi_it.hasNext():
    writer_spi = writer_spi_it.next()
    print("writer_spi: " + ', '.join(writer_spi.getFormatNames()) + " (" + writer_spi.getClass().getName() + ")")
'''
    
#----------------------#
# OPERATORS/ALGORITHMS #
#----------------------#
'''
GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
op_spi_it = GPF.getDefaultInstance().getOperatorSpiRegistry().getOperatorSpis().iterator()
while op_spi_it.hasNext():
    op_spi = op_spi_it.next()
    print("op_spi:", op_spi.getOperatorAlias())
'''

#----------------------#
#       READ FILE      #
#----------------------#
'''
parameters = HashMap()
parameters.put('file', File('/home/rccc/Downloads/TEMP_SAR_PRODUCTS/RS2_OK871_PK6633_DK3208_FQ2_20080415_143805_HH_VV_HV_VH_SLC/product.xml'))
p = GPF.createProduct("Read", parameters)
#p = ProductIO.readProduct('L3_subset_watermask.dim')

name = p.getName()
w = p.getSceneRasterWidth()
h = p.getSceneRasterHeight()

print(name + ":", w, "x", h, "pixels")
'''
