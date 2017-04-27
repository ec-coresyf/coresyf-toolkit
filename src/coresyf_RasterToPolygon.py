#!/usr/bin/env python
#==============================================================================
#                         <coresyf_RasterToPolygon.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Image Crop)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line raster cropping tool for GDAL supported files
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
It uses the GDAL raster utility program "gdal_polygonize.py" to produce a polygon 
feature layer from a raster.
It creates vector polygons for all connected regions of pixels in the raster sharing 
a common pixel value. Each polygon is created with an attribute indicating the pixel
value of that polygon. A raster mask may also be provided to determine which pixels
are eligible for processing.

@example:
It may be useful for the user to convert a raster file into a polygon.

Example 1 - Convert raster file into a polygon: 
./coresyf_RasterToPolygon.py -r input_raster.tif  
                        -o polygonized_image.shp 


@attention: ???????????
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
            'coresyf_RasterToPolygon.py [-r <InputRaster>]'
            "                      [-o <OutputRaster>] [--o_format=<OutputFileFormat>]"
 #           "[--o_type=<DataType>]" 
            "\n")

#DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import subprocess


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
                      dest="output_polygon", metavar=' ',
                      help=("output polygon shapefile "
                            "(default: 'polygonized_image.shp')"),
                      default="polygonized_image.shp")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'ESRI Shapefile')",
                      default="ESRI Shapefile" )    

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

    
  
    #================================#
    # Building gdal_polygonize command line #
    #================================#
    gdal_exe    = 'gdal_polygonize.py '
    

    
    output_opts = '%s -f "%s" %s %s ' % (opts.input_raster,
                                     opts.output_format,
                                     opts.output_polygon,
                                     opts.output_polygon) 
    
    gdal_polygonize_command = gdal_exe + output_opts
    print (gdal_polygonize_command)
    #===========================#
    # Run gdal_polygonize command line #
    #===========================#
    #print ('\n' + gdal_polygonize_command)
    #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
    
    try:
        process = subprocess.Popen(gdal_polygonize_command,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()
        print (stdout)
        if stderr:      
            raise Exception (stderr)  # or  if process.returncode:
    except Exception as message:
        print( str(message) )
        sys.exit(process.returncode)


if __name__ == '__main__':
    main()
