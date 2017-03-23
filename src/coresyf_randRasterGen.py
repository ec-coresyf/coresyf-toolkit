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
It uses the "numpy" and "GDAL" Python modules to generate raster images in
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

from argparse import ArgumentParser
from numpy.random import uniform
from osgeo import gdal



VERSION = '1.0'

OUTPUT_FORMATS = ['GTiff', 'HFA', 'netCDF', 'HDF4', 'HDF5']


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

    generate_image(opts.target_file, opts.bands, opts.width, opts.height, opts.min, opts.max, opts.format)
 
def generate_image(target_file, bands, width, height, min, max, format):
    """generate an synthetic raster image band
    with each pixel value drawn from a uniform distribution."""
    values = uniform(min, max, [bands, height, width])
    print values

    driver = gdal.GetDriverByName(format)
    if (not driver):
        raise Exception('No gdal driver was found for %s.' % format)
    dataset = driver.Create(target_file, width, height, bands, gdal.GDT_Float32)
    for i in range(0, bands):
        dataset.GetRasterBand(i+1).WriteArray(values[i])
    dataset.FlushCache()
    return dataset



#if __name__ == '__main__':
main()
