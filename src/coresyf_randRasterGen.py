#!/usr/bin/env python

#==============================================================================
#                       <coresyf_randRasterGen.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Random Raster Generator)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line tool for generating a random raster image
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary:
This module runs the following Co-ReSyF tool:
 - RANDOM RASTER GENERATOR
This tool generates a raster image with random values uniformly distributed over
the half-open interval [low, high[ (includes low, but excluded high value).
Therefore, any value within the interval is equally likely to appear within the
raster image.
It uses the "numpy", "GDAL", and "h5py" Python modules to generate raster images in
different formats: GeoTIFF, IMG (Erdas file type) or netCDF and HDF.


@example:
Example 1 - Create a random raster image and save the output into GeoTIFF format:
./coresyf_randRasterGen.py --min=0 --max=1 -o myrandomraster.tif


@attention:
  @todo:
  - test all features and parameters?


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool.
'''

from os.path import basename, splitext
from argparse import ArgumentParser
from numpy.random import uniform
from osgeo import gdal
import h5py



VERSION = '1.0'

OUTPUT_FORMATS = ['GTiff', 'HFA', 'netCDF', 'HDF5']


def main():
    """The main."""

    parser = ArgumentParser(version=VERSION)

    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_argument('-o',
                        dest="target_file",
                        help="The output file path.",
                        required=True)
    parser.add_argument('--o_format',
                        dest="format",
                        help="The output format.",
                        default='GTiff',
                        choices=OUTPUT_FORMATS)
    parser.add_argument('--bands',
                        dest="bands",
                        help=("The number of bands."),
                        default="1",
                        type=int)
    parser.add_argument('--width',
                        dest="width",
                        help=("The image width (in pixels)."),
                        type=int,
                        required=True)
    parser.add_argument('--height',
                        dest="height",
                        help=("The image height (in pixels)."),
                        type=int,
                        required=True)
    parser.add_argument('--min',
                        dest="min",
                        help=("The min value."),
                        default="0",
                        type=int)
    parser.add_argument('--max',
                        dest="max",
                        help=("The max value."),
                        default="255",
                        type=int)

    opts = parser.parse_args()
    #==============================#
    #   Check options              #
    #==============================#

    if opts.min and opts.max and opts.min > opts.max:
        parser.error("Minimum should not exceed maximum.")

    print 'generating image...'
    generate_image(opts.target_file, opts.bands, opts.width, opts.height, opts.min, opts.max,
                   opts.format)
    print 'finished'

def generate_image(target_file, bands, width, height, minimum, maximum, img_format):
    """generate an synthetic raster image band
    with each pixel value drawn from a uniform distribution."""
    values = uniform(minimum, maximum, [bands, height, width])
    if img_format == 'HDF5':
        h5py_create_image(target_file, values)
    else:
        gdal_create_image(target_file, width, height, bands, img_format, values)

def h5py_create_image(target_file, values):
    """create an HDF5 image from a 3D matrix, where the 1th dimension represents the bands,
    2th the rows, and the 3th the lines of the image"""
    hdf_file = h5py.File(target_file, 'w')
    dataset_name = basename(splitext(target_file)[0])
    hdf_file.create_dataset(dataset_name, data=values)
    hdf_file.close()
    return hdf_file

def gdal_create_image(target_file, width, height, bands, img_format, values):
    """create an gdal compatible image from a 3D matrix, where 1th dimension represents the
    bands, 2th the rows, and the 3th the lines of the image"""
    driver = gdal.GetDriverByName(img_format)
    if not driver:
        raise Exception('No gdal driver was found for %s.' % img_format)
    dataset = driver.Create(target_file, width, height, bands, gdal.GDT_Float32)
    for i in range(0, bands):
        dataset.GetRasterBand(i+1).WriteArray(values[i])
    dataset.FlushCache()
    return dataset

if __name__ == '__main__':
    main()
