#!/usr/bin/env python
#==============================================================================
#                         <coresyf_isodata_classification.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (ISOdata classification algorithm)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line ISOdata classification for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - ISODATA CLASSIFICATION
It uses the pyradar module isodata_classification to classificate a raster
into a defined number of classes.

@example:

Example 1 - Classify a GTiff image "example" and store the output in another GTiff:
python coresyf_isodata_classification.py -r ../examples/ISOdata_classification/example.TIF -o classified_example.tif


@attention: 
    @todo
    - Is projection checking performed???
    - Explore other limitations...


@version: v.1.0
@author: RIAA

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_isodata_classification.py [-r <InputRaster>]' 
            '[-c_threshold <ConvergenceThreshold>]'
            "[-i <IterationNumber>] [-k <InitialClusters>] [-s <StdThreshold>]"
            "[-p <PairClusters>] [-m <MinPixels>] [-c <MergeDist>]"
            "[-o <OutputRaster>] [--o_format=<OutputFileFormat>]"
            "\n")



''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import subprocess
from pyradar.classifiers.isodata import isodata_classification
#from pyradar.core.equalizers import equalization_using_histogram
#from pyradar.core.sar import create_dataset_from_path
#from scipy import misc
import os
#import Image
import numpy as np
from osgeo import gdal
def gdal_create_image(target_file, width, height, bands, img_format, values, geotrans, proj):
    """create an gdal compatible image from a 3D matrix, where 1th dimension represents the
    bands, 2th the rows, and the 3th the lines of the image"""
    driver = gdal.GetDriverByName(img_format)
    if not driver:
        raise Exception('No gdal driver was found for %s.' % img_format)
    dataset = driver.Create(target_file, width, height, bands, gdal.GDT_Float32)
    dataset.GetRasterBand(1).WriteArray(values)
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    return dataset

def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)
    
    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r', 
                      dest="input_raster", metavar=' ',
                      help="input raster file (GDAL supported file)", )
    parser.add_option('-o', 
                      dest="output_raster_classified", metavar=' ',
                      help=("output raster file classified using ISODATA "
                            "algorithm (default: 'classified_image.tif')"),
                      default="classified_image.tif")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GTiff')",
                      default="GTiff" )
    parser.add_option('--c_threshold', 
                      dest="convergence_threshold", metavar=' ',
                      help="Threshold of the change allowed in the clusters between each iteration (default: 0.01)",
                      default=0.01 )
    parser.add_option('-i', 
                      dest="iteration_number", metavar=' ',
                      help="Maximum number of iterations (default: 100)",
                      default=100 )
    parser.add_option('-k', 
                      dest="initial_clusters", metavar=' ',
                      help="Number of initial clusters (default: 15)",
                      default=15 )
    parser.add_option('-s', 
                      dest="std_threshold", metavar=' ',
                      help="Threshold value for standard deviation, to split the clusters (default: 0.1)",
                      default=0.1 )
    parser.add_option('-p', 
                      dest="pair_clusters", metavar=' ',
                      help="Maximum number of pairs of clusters which can be merged (default: 2)",
                      default=2 )
    parser.add_option('-m', 
                      dest="min_pixels", metavar=' ',
                      help="Minimum number of pixels in each cluster (default: 10)",
                      default=10 )
    parser.add_option('-c', 
                      dest="merge_dist", metavar=' ',
                      help="Maximum distance between clusters before merging (default: 2)",
                      default=2 )
    '''parser.add_option('--no_data_value', 
                      dest="no_data_value", metavar=' ',
                      help="Pixel value excluded from the classification",
                      type=int )'''

    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()

    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_raster:
        print("No input raster provided. Nothing to do!")
        print(USAGE)
        return
    
    params = {"K": opts.initial_clusters, "I" : opts.iteration_number, "P" : opts.pair_clusters, "THETA_M" : opts.min_pixels, "THETA_S" : opts.std_threshold,
          "THETA_C" : opts.merge_dist, "THETA_O" : opts.convergence_threshold}

    data = gdal.Open(opts.input_raster)
    width=data.RasterXSize
    height=data.RasterYSize
    geotrans=data.GetGeoTransform()  
    proj=data.GetProjection() 
    dataset = np.array(data.GetRasterBand(1).ReadAsArray())
    '''if opts.no_data_value:
        dataset[dataset==opts.no_data_value]=-99999'''
    target_file=opts.output_raster_classified
    img_format=opts.output_format
    class_image = isodata_classification(dataset, parameters=params)
    #print(np.unique(class_image))
    gdal_create_image(target_file, width, height, 1, img_format, class_image, geotrans, proj)


if __name__ == '__main__':
    main()