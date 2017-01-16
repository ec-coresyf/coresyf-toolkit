#!/usr/bin/env python
#==============================================================================
#                         <coresyf_image_splitting.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Image Splitting)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line raster splitting tool for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - IMAGE SPLITTING
It uses the GDAL raster utility program "gdal_translate.py" to split the bands 
of an input raster into different output raster files.  

@example:
Example 1 - Generate different raster images for all bands of the input raster
            file:
./coresyf_image_splitting.py -r image_2bands.tif -o band.tif --all_bands 

Example 2 - Generate raster image only for 2nd band of the input raster file:
./coresyf_image_splitting.py -r image_2bands.tif --r_band=2 -o band.tif
 
@attention: 
 

@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( "\n"
            "coresyf_image_splitting.py [-r <InputMultiBandRaster>] [--r_band=<Value>]\n"
            "                           [-o <OutputRaster>] [--o_format=<OutputFileFormat>]\n"
            "                           [--o_type=<DataType>] [--no_data_value=<Value>]\n"
            "                           [--all_bands]"
            "\n")

DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
from osgeo import gdal
import subprocess


def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)
    
    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r', 
                      dest="input_raster", metavar=' ',
                      help="input multi-band raster file (GDAL supported file)",)
    parser.add_option('--r_band', 
                      dest="raster_band", metavar=' ',
                      help="band number of input raster file to be used for generating the output image (default: 1)",
                      default="1",
                      type=int )
    parser.add_option('-o', 
                      dest="output_raster", metavar=' ',
                      help=("basename for output files, where each one corresponds "
                            "to a separate band of the input raster file (default: 'image_band.tif')"),
                      default="image_band.tif")
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
    parser.add_option("--all_bands", 
                      dest="all_bands", action="store_true", 
                      help="generate different raster images for all bands of the input raster file")
    
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
    
    #==============================#
    #   Check data type option     #
    #==============================#
    if opts.data_type and opts.data_type not in DefaultTypesLookup:
        print('Incorrect output data type!') 
        print('Must be one of: "%s".' % '", "'.join(DefaultTypesLookup))
        print(USAGE)
        return
    
    #================================#
    #     Check all_bands option     #
    #================================#   
    r_bandsIDs = [opts.raster_band]
    output_files = [opts.output_raster]
    if opts.all_bands:
        try:
            r_bands = gdal.Open(opts.input_raster, gdal.GA_ReadOnly).RasterCount    
            r_bandsIDs = [i for i in range(1, r_bands+1)]
            output_files = [str(i) + '_' + opts.output_raster for i in range(1, r_bands+1)]
        except:
            print ("Unable to determine the number of bands of the input file!")
            sys.exit(1)    
    
    #====================================#
    #    LOOP THROUGH ALL RASTER BANDS   #
    #====================================#
    for i in range(0, len(r_bandsIDs)):
        print ("Creating output file for band #%d..." % r_bandsIDs[i])
        
        #--------------------------------------#
        # Building gdal_translate command line #
        #--------------------------------------#
        gdal_exe    = 'gdal_translate '
        raster_opts = '-b %d %s ' % (r_bandsIDs[i], opts.input_raster)
        
        output_opts = '%s -of %s ' % (output_files[i], opts.output_format) 
        if opts.data_type:
            output_opts += '-ot %s ' % (opts.data_type)
        if opts.no_data_value != None:
            output_opts += '-a_nodata %d ' % (opts.no_data_value)

        gdal_translate_command = gdal_exe + raster_opts + output_opts

        #------------------------------------#
        #  Run gdal_translate command line   #
        #------------------------------------#
        print ('\n' + gdal_translate_command)
        print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
        try:
            process = subprocess.Popen( gdal_translate_command,
                                        shell  = True,
                                        stdin  = subprocess.PIPE,
                                        stdout = subprocess.PIPE,
                                        stderr = subprocess.PIPE, )
            # Reads the output and waits for the process to exit before returning
            stdout, stderr = process.communicate()   
            print (stdout)
            if stderr:            raise Exception (stderr)  # or  if process.returncode:
        except Exception, message:
            print( str(message) )
            sys.exit(process.returncode)


if __name__ == '__main__':
    main()