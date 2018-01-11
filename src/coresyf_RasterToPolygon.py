#!/usr/bin/env python
#==============================================================================
#                         <coresyf_RasterToPolygon.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Raster to Polygon)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line tool for converting a raster into a polygon shapefile
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary:
This module runs the following Co-ReSyF tool:
 - Raster to Polygon
It uses the GDAL raster utility program "gdal_polygonize.py" to produce polygon
feature layers from a raster. The number of shapefiles produced is equal to the number
of bands in the input raster. Each shapefile contains a layer with its own name, but
the user can specify the fieldname.
It creates vector polygons for all connected regions of pixels in the raster sharing
a common pixel value. Each polygon is created with an attribute indicating the pixel
value of that polygon.

@example:

Example 1 - Generate different polygons for all bands of the input raster:
./coresyf_RasterToPolygon.py -r ../examples/RasterToPolygon/multiBandImage.tif -o polygonized_raster.shp


@version: v.1.0
@author: RIAA

@change:
1.0
- First release of the tool.
'''

VERSION = '1.0'
USAGE = ('\n'
         'coresyf_RasterToPolygon.py [-r <InputRaster>]'
         "[-o <OutputRaster>] [-n <FieldName>]"
 #        "[--o_type=<DataType>]"
         "\n")



''' SYSTEM MODULES '''
import subprocess
import sys
from optparse import OptionParser

from osgeo import gdal


def main():
    parser = OptionParser(usage=USAGE,
                          version=VERSION)

    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r',
                      dest="input_raster", metavar=' ',
                      help="input raster file (GDAL supported file)", )
    parser.add_option('-o',
                      dest="output_polygon", metavar=' ',
                      help=("output polygon shapefile "
                            "(default: 'polygonized_raster.shp')"),
                      default="polygonized_raster.shp")
    parser.add_option('--o_format',
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'ESRI Shapefile')",
                      default="ESRI Shapefile")
    parser.add_option('-n',
                      dest="fieldname", metavar=' ',
                      help=("The name of the file to create "
                            "(default: 'DN')"),
                      default="DN")

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

    #Get the total number of raster bands in the raster file
    try:
        r_bands = gdal.Open(opts.input_raster, gdal.GA_ReadOnly).RasterCount
        r_bandsIDs = [i for i in range(1, r_bands+1)]
        print("Creating output file names from output basename...")
        output_files = [str(i) + '_' + opts.output_polygon for i in range(1, r_bands+1)]
    except:
        print("Unable to determine the number of bands of the input file!")
        sys.exit(1)

    #====================================#
    #    LOOP THROUGH ALL RASTER BANDS   #
    #====================================#

    for i in range(0, len(r_bandsIDs)):
        print("Creating output file for band #%d..." % r_bandsIDs[i])

        #--------------------------------------#
        # Building gdal_translate command line #
        #--------------------------------------#
        gdal_exe = 'gdal_polygonize.py '
        output_opts = '%s -b %s -f "%s" %s %s %s' % (opts.input_raster,
                                                     r_bandsIDs[i],
                                                     opts.output_format,
                                                     output_files[i],
                                                     output_files[i],
                                                     opts.fieldname)
        gdal_polygonize_command = gdal_exe + output_opts


        #==================================#
        # Run gdal_polygonize command line #
        #==================================#
        #print ('\n' + gdal_polygonize_command)
        #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])

        try:
            process = subprocess.Popen(gdal_polygonize_command,
                                       shell=True,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,)
            # Reads the output and waits for the process to exit before returning
            stdout, stderr = process.communicate()
            print(stdout)
            if stderr:
                raise Exception(stderr)  # or  if process.returncode:
        except Exception as message:
            print(str(message))
            sys.exit(process.returncode)


if __name__ == '__main__':
    main()
