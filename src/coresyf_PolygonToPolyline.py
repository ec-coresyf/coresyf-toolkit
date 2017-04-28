#!/usr/bin/env python
#==============================================================================
#                         <coresyf_PolygonToPolyline.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (polygon to polyline conversion tool)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line polygon to polyline conversion tool for GDAL supported 
#         shapefiles.
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
It uses the GDAL vector utility program "ogr2ogr" to convert a polygon to a 
polyline shapefile.
It can be used to create new shapefiles containing layers with polyline geometry.  


@example:

Example 1 - Convert a shapefile geometry from polygon to polyline: 
./coresyf_PolygonToPolyline.py -r ../examples/PolygonToPolyline/polygons_land_mask.shp -o my_polyline.shp


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_PolygonToPolyline.py [-r <InputPolygon>] [-o <OutputPolyline>]'
            "\n")


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
                      help="input polygon file (GDAL supported vector file)", )
    parser.add_option('-o', 
                      dest="output_polyline", metavar=' ',
                      help=("output raster file "
                            "(default: 'output_polyline.shp')"),
                      default="output_polyline.shp")
#     parser.add_option('--o_format', 
#                       dest="output_format", metavar=' ',
#                       help= ("GDAL vector format for output file, some possible formats are"
#                              " 'ESRI Shapefile', 'netCDF'  (default: 'ESRI Shapefile')"),
#                       default="ESRI Shapefile" )    

    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()
    
    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_polygon:
        print("No input polygon file provided. Nothing to do!")
        print(USAGE)
        return

    
    #============================================#
    # Building gdal_ogr2ogr_command command line #
    #============================================#
    gdal_exe    = 'ogr2ogr '
    
    output_opts = '-f "%s" -overwrite -nlt %s %s %s ' % ("ESRI Shapefile", #opts.output_format,
                                              'MULTILINESTRING',
                                              opts.output_polyline,
                                              opts.input_polygon ) 

    gdal_ogr2ogr_command = gdal_exe + output_opts
    
    #=======================================#
    # Run gdal_ogr2ogr_command command line #
    #=======================================#
    #print ('\n' + gdal_ogr2ogr_command)
    #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
    
    try:
        process = subprocess.Popen(gdal_ogr2ogr_command,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()
        print (stdout)
        print ("Done!")
        if stderr:      
            raise Exception (stderr)  # or  if process.returncode:
    except Exception as message:
        print( str(message) )
        sys.exit(process.returncode)


if __name__ == '__main__':
    main()
