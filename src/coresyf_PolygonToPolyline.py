#!/usr/bin/env python
#==============================================================================
#                         <coresyf_PolygonToPolyline.py>
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
 - Polygon to Polyline
It uses the GDAL raster utility program "ogr2ogr" to produce a polyline 
from a polygon.


@example:
It may be useful for the user to convert a polygon file into a polyline.

Example 1 - Convert raster file into a polygon: 
./coresyf_PolygonToPolyline.py -r input_polygon.shp  
                        -o polylined_image.shp 


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
            'coresyf_PolygonToPolyline.py [-r <InputPolygon>]'
            "                      [-o <OutputPolyline>] [--o_format=<OutputFileFormat>]"
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
                      dest="input_polygon", metavar=' ',
                      help="input polygon file (GDAL supported file)", )
    parser.add_option('-o', 
                      dest="output_polyline", metavar=' ',
                      help=("output raster file "
                            "(default: 'polylined_image.shp')"),
                      default="polylined_image.shp")
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
    if not opts.input_polygon:
        print("No input polygon provided. Nothing to do!")
        print(USAGE)
        return

    
  
    #================================#
    # Building gdal_polygonize command line #
    #================================#
    gdal_exe    = 'ogr2ogr '
    

    
    output_opts = '%s -f "%s" %s %s ' % (opts.input_polygon,
                                     opts.output_format,
                                     opts.output_polyline,
                                     opts.output_polyline) 
    
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
