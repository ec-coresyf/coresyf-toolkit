#!/usr/bin/env python
#==============================================================================
#                         <coresyf_image_stacking.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Image Stacking)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line raster stacking tool for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - IMAGE STACKING
It uses the GDAL raster utility program "gdal_merge.py" to generate the final 
raster image, where each band corresponds to a separate input raster file.

@example: 
Example 1 - Generate a raster image with different bands from independent raster
            files:
./coresyf_image_stacking.py -r image_band1.tif image_band2.tif 
                            -o output_stack.tiff 
 

@attention: 
- All the images must be in the same coordinate system but they may be at
different resolutions.
- Input rasters with more than 1 band are allowed. 
 

@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( "\n"
            "coresyf_image_stacking.py [-r <InputRaster1> <InputRaster2> ...]\n"
            "                          [-o <OutputRaster>] [--o_format=<OutputFileFormat>]\n"
            "                          [--o_type=<DataType>] [--no_data_value=<Value>]"
            "\n")

DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


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
                      dest="input_rasters", metavar=' ',
                      help="input raster files (GDAL supported files)",)
    parser.add_option('-o', 
                      dest="output_raster", metavar=' ',
                      help=("output file with layer stack, where each band corresponds "
                            "to a separate input raster file (default: 'stack_image.tif')"),
                      default="stack_image.tif")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GTiff')",
                      default="GTiff" )    
    parser.add_option('--o_type', 
                      dest="data_type", metavar=' ',
                      help= ("output data type must be one of %s "
                             "(default: uses the largest type of "
                             "the input files)")%DefaultTypesLookup )
    parser.add_option('--no_data_value', 
                      dest="no_data_value", metavar=' ',
                      help="output nodata value (default datatype specific value)",
                      type=int )
    
    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()
    
    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_rasters:
        print("No input rasters provided. Nothing to do!")
        print(USAGE)
        return
    
    #=============================================#
    # Add remaining args to list of input rasters #
    #=============================================#
    list_input_rasters = [opts.input_rasters]
    if len(args) > 0:
        list_input_rasters.extend(args)
    
    #==============================#
    #   Check data type option     #
    #==============================#
    if opts.data_type and opts.data_type not in DefaultTypesLookup:
        print('Incorrect output data type!') 
        print('Must be one of: "%s".' % '", "'.join(DefaultTypesLookup))
        print(USAGE)
        return
    
    #==================================#
    # Building gdal_merge command line #
    #==================================#
    gdal_exe = 'gdal_merge.py ' 
    
    output_opts = '-separate -o %s -of %s '%(opts.output_raster, opts.output_format) 
     
    if opts.data_type:
        output_opts += '-ot %s ' % (opts.data_type)
    if opts.no_data_value != None:
        output_opts += '-a_nodata %d ' % (opts.no_data_value)
    
    gdal_merge_command = gdal_exe + output_opts + ' '.join(list_input_rasters)
        
    #================================#
    # Run gdal_merge.py command line #
    #================================#
    #print ('\n' + gdal_merge_command)
    #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])

    try:
        process = subprocess.Popen( gdal_merge_command,
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