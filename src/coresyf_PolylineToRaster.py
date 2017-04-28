#!/usr/bin/env python
#==============================================================================
#                         <coresyf_PolylineToRaster.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Polyline to Raster)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line polyline to raster tool for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary:
This module runs the following Co-ReSyF tool:
 - Polyline to Raster
It uses the GDAL raster utility program "gdal_rasterize" to burn vector geometries into a raster. 
This program burns vector geometries (points, lines, and polygons) into the raster band(s) of a 
raster image. Vectors are read from OGR supported vector formats.

@example:

Example 1 - Generate a 3000 by 3000 raster with HDF4 format from a polyline:
./coresyf_PolylineToRaster.py -n DN --width 3000 --height 3000 --o_format HDF4Image 
-r ../examples/PolylineToRaster/output_polyline.shp -l output_polyline -o output_raster.tif


@version: v.1.0
@author: RIAA

@change:
1.0
- First release of the tool.
'''

VERSION = '1.0'
USAGE = ('\n'
         'coresyf_PolylineToRaster.py [-n <FieldName>] [--width <Width>] [--height <Height>]'
         "[--o_format <OutputFormat>] [-r <InputPolyline>] [-l <Layer>] [-o <OutputRaster>] "
 #        "[--o_type=<DataType>]"
         "\n")

#DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
import subprocess
import sys
from optparse import OptionParser
import os

os.path.basename

from osgeo import gdal


def main():
    parser = OptionParser(usage=USAGE,
                          version=VERSION)

    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r',
                      dest="input_polyline", metavar=' ',
                      help="input polyline shapefile (GDAL supported file)", )
    parser.add_option('-o',
                      dest="output_raster", metavar=' ',
                      help=("output raster "
                            "(default: 'rasterized_raster')"),
                      default="rasterized_raster")
    parser.add_option('-n',
                      dest="fieldname", metavar=' ',
                      help=("Attribute field on the features to be used for a burn-in value "
                            "(default: 'DN')"),
                      default="DN")
    parser.add_option("--width", 
                      dest="width", metavar=' ',
                      help="Width of the output file")
    parser.add_option("--height", 
                      dest="height", metavar=' ',
                      help="Height of the output file")
    parser.add_option("-l", 
                      dest="layer", metavar=' ',
                      help="Layer of the input file to be used "
                      "(default: filename)")
    parser.add_option('--o_format',
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GeoTIFF')",
                      default="GTiff")

    #==============================#
    #   Check mandatory options    #
    #==============================#

    (opts, args) = parser.parse_args()

    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_polyline:
        print("No input polyline provided. Nothing to do!")
        print(USAGE)
        return
    if not opts.layer:
        #If no layer name is received, use the input filename
        opts.layer=os.path.split(opts.input_polyline.split('.')[0])[1]
        return

        #--------------------------------------#
        # Building gdal_translate command line #
        #--------------------------------------#
    gdal_exe = 'gdal_rasterize '
    output_opts = '-a %s -of %s -ts %s %s -l %s %s %s' % (opts.fieldname,
                                                 opts.output_format,
                                                 opts.width,
                                                 opts.height,
                                                 opts.layer,
                                                 opts.input_polyline,
                                                 opts.output_raster)
    gdal_rasterize_command = gdal_exe + output_opts


    #===========================#
    # Run gdal_rasterize command line #
    #===========================#
    #print ('\n' + gdal_rasterize_command)
    #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])

    try:
        process = subprocess.Popen(gdal_rasterize_command,
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
