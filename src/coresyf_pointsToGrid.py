#!/usr/bin/env python
#==============================================================================
#                         <coresyf_pointsToGrid.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Points to Gridded)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line tool for generating a raster from scattered data(points)
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - POINT MEASUREMENTS TO GRIDDED MAPS
It uses the GDAL raster utility program "gdal_grid.py" to create a regular grid
(raster image) from scattered data (Point measurements) read from OGR 
datasource (http://www.gdal.org/ogr_formats.html). Input data will be 
interpolated to fill grid nodes with values. The user can choose from various
interpolation algorithms.

@example:
Example 1 - Create a raster TIFF from a shapefile with point measurements. The 
            X and Y coordinates are being taken from geometry and the Z values 
            are being taken from the "elev" field.
            NOTE: "elev_points.shp" must contain a layer named "elev_points" 
./coresyf_pointsToGrid.py -s elev_points.shp --s_field="elev" -a nearest
                          -o elev_raster_nearest.tif --o_xsize=500 --o_ysize=500
                        
Example 2 - Create a raster TIFF from a text file with a list of comma separated
            X, Y, Z values (.CSV file) with a virtual dataset header (.VRT file).
./coresyf_pointsToGrid.py -s points.vrt -a nearest
                          -o elev_raster_nearest_pts.tif --o_xsize=500 --o_ysize=500

@attention: 
  - The interpolation algorithm "nearest" seems to yield good results. Explore
    others... 
  - Besides the interpolation functionality "gdal_grid" can be used to compute 
    some data metrics using the specified window and output grid geometry.
  @todo: 
  - Add options for configuring the parameters of each interpolation algorithm.


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_pointsToGrid.py [-s <InputOGRdatasource>] [--s_field=<AttributeFieldName>]\n'
            '                        [-a <InterpolationAlgorithmName>]\n'
            "                        [-o <OutputRaster>] [--o_format=<OutputFileFormat>]\n"
            "                        [--o_xsize=<OutputSizeX>] [--o_ysize=<OutputSizeY>]\n"
            "                        [--o_type=<DataType>] [--no_data_value=<Value>]" 
            "\n")

DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']
InterpolationAlgo  = [ "invdist", "invdistnn", "average", "nearest", "linear"]


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import subprocess
import os


def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)
    
    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-s', 
                      dest="input_source", metavar=' ',
                      help=("input scattered data (OGR supported readable "
                            "datasource) containing a layer with the same name"
                            " and features with a point geometry.") ,)
    parser.add_option('--s_field',
                      dest="source_field", metavar=' ',
                      help=("Attribute field name on the features to be used "
                            "to get a Z value from.") ,)
    parser.add_option('-a', 
                      dest="interpolation_algorithm", metavar=' ',
                      help=("Interpolation algorithm name:                      " 
                            "'invdist': Inverse distance to a power (default);  "
                            "'invdistnn': Inv. dist. power with nearest neighbor; "
                            "'average' - Moving average algorithm;              "
                            "'nearest' - Nearest neighbor algorithm;            "
                            "'linear' - Linear interpolation algorithm.         "),
                      type='choice', choices=InterpolationAlgo,
                      default='invdist')
    parser.add_option('-o', 
                      dest="output_raster", metavar=' ',
                      help=("output raster file (default: 'grid_image.tif')"),
                      default="grid_image.tif")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GTiff')",
                      default="GTiff" )    
    parser.add_option('--o_type', 
                      dest="data_type", metavar=' ',
                      help= ("output data type must be one of %s "
                             "(default: uses the largest type of "
                             "the input files)")%DefaultTypesLookup,
                      type='choice', choices=DefaultTypesLookup )
    parser.add_option('--no_data_value', 
                      dest="no_data_value", metavar=' ',
                      help="output nodata value (default datatype specific value)",
                      type=int )
    parser.add_option('--o_xsize', 
                      dest="x_size", metavar=' ',
                      help="Set the X dimension size of the output file in pixels (default: 250)",
                      default="250",
                      type=int )
    parser.add_option('--o_ysize', 
                      dest="y_size", metavar=' ',
                      help="Set the Y dimension size of the output file in pixels (default: 250)",
                      default="250",
                      type=int )
 

    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()
    
    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_source:
        print("No input scattered data provided. Nothing to do!")
        print(USAGE)
        return

    #==============================#
    #   Check Source field option  #
    #==============================#
    if not opts.source_field:
        print("WARNING: No attribute field provided. Z value will be read from feature geometry!")  
    
    #=================================#
    # Building gdal_grid command line #
    #=================================#
    gdal_exe    = 'gdal_grid '

    algo_opts = '-a %s' % opts.interpolation_algorithm
    if opts.no_data_value != None:
        algo_opts += ':nodata=%d ' % opts.no_data_value
    else:
        algo_opts += ' '
    
    if opts.source_field:
        algo_opts += '-zfield "%s" ' % opts.source_field 

    output_opts = '-outsize %d %d -of %s ' % (opts.x_size,
                                              opts.y_size,
                                              opts.output_format)
    if opts.data_type:
        output_opts += '-ot %s ' % opts.data_type 

    input_opts = '-l %s %s ' % (os.path.splitext(os.path.basename(opts.input_source))[0],
                                opts.input_source)
    
    
    gdalgrid_command = gdal_exe + algo_opts + output_opts + input_opts + opts.output_raster
    
    #============================#
    # Run gdal_grid command line #
    #============================#
    print('\n' + gdalgrid_command)
    print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
    
    try:
        process = subprocess.Popen( gdalgrid_command,
                                    shell  = True,
                                    stdin  = subprocess.PIPE,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE, )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()   
        print (stdout) 
        if stderr:      raise Exception (stderr)  # or  if process.returncode:
    except Exception, message:
        print( str(message) )
        sys.exit(process.returncode)


if __name__ == '__main__':
    main()