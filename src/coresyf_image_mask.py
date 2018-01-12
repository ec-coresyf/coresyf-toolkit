#!/usr/bin/env python
#==============================================================================
#                         <coresyf_image_mask.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Image Mask)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line raster masking calculator for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - IMAGE MASK
It uses the GDAL raster utility program "gdal_calc.py" to calculate the final 
masked image.
It can take any raster file and use it as a mask to extract values from a 
geospatial image. The mask is a raster in which each pixel contains no-data or 
a single valid value. The no-data pixels on the mask are assigned as no-data 
values on the output raster. For the remaining pixels, the output raster 
contains the values extracted from the input image. Note that, there is the 
possibility of using the input image to create a mask on the fly.

@example:
An example might be the case of a raster with elevation values ranging from 
below sea level to mountain tops. If you are only interested in elevations 
below sea level, you can use this tool to apply a mask (defining below sea 
level areas) to the input raster to create a masked image with only the
regions of interest.  

Example 1 - Calculate masked image using a mask:
./coresyf_image_mask.py -r etopo_raster.tif -m mask_ocean.tif 
                        -o masked_image.tif 

Example 2 - Create a mask on the fly (with elevations below 0)
            and calculate masked image:
./coresyf_image_mask.py -r etopo_raster.tif -m etopo_raster.tif 
                       --m_range=:0  -o masked_image_onTheFly.tif

Example 3 - Create a mask on the fly (with elevations above 1000)
            and calculate masked image for all raster bands:
./coresyf_image_mask.py -r multiBandImage.tif -m multiBandImage.tif --m_range=1000:
                        -o multiBand_maskedImg.tif --all_bands            

@attention: 
- Note that both files (raster and mask) must have the same dimensions;
- No projection checking is performed. 


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( "\n"
            "coresyf_image_mask.py [-r <InputRaster>] [--r_band=<Value>]\n"
            "                      [-m <InputMask>] [--m_band=<Value>] [--m_range=<min1:max1,min2:max2...>]\n"
            "                      [-o <OutputRaster>] [--o_format=<OutputFileFormat>]\n"
            "                      [--o_type=<DataType>] [--no_data_value=<Value>]\n"
            "                      [--all_bands]" 
            "\n")

DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
from osgeo import gdal
import subprocess
import os


def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)
    
    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r', 
                      dest="input_raster", metavar=' ',
                      help="input raster file (GDAL supported file)", )
    parser.add_option('--r_band', 
                      dest="raster_band", metavar=' ',
                      help="number of band for input raster file (default: 1)",
                      default="1",
                      type=int )
    parser.add_option('-m', 
                      dest="input_mask", metavar=' ',
                      help="input mask file (GDAL supported raster file)",)
    parser.add_option('--m_band', 
                      dest="mask_band", metavar=' ',
                      help="number of band for input mask file (default: 1)",
                      default="1",
                      type=int )
    parser.add_option('--m_range', 
                      dest="mask_range", metavar=' ',
                      help="range of pixel values to extract from mask" )
    parser.add_option('-o', 
                      dest="output_raster", metavar=' ',
                      help="output raster file with masked image (default: 'masked_image.tif')",
                      default="masked_image.tif")
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
                      help="mask all bands of the input raster file")
    
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
    if not opts.input_mask:
        print("No input mask provided. Nothing to do!")
        print(USAGE)
        return

    #==============================#
    #   Check data type option     #
    #==============================#
    if opts.data_type and opts.data_type not in DefaultTypesLookup:
        print("Incorrect output data type!") 
        print("Must be one of %s." % DefaultTypesLookup)
        print(USAGE)
        return
    
    #================================#
    # Check and convert range option #
    #================================#
    ranges_exp = ''
    if opts.mask_range:
        try:
            for part in opts.mask_range.split(','):
                part_exp = ''
                minV, maxV = part.split(':')
                if minV:
                    minV = int(minV)
                    part_exp += '(B>=%d)' % minV
                if maxV:
                    maxV = int(maxV)
                    if part_exp:  part_exp += ' & '
                    part_exp += '(B<=%d)' % maxV
                
                part_exp = '(' + part_exp + ')'    # ((B>=0) & (B<=10))
                if ranges_exp: ranges_exp += ' | '
                ranges_exp += part_exp   # ((B>=0) & (B<=10)) | ((B>=15) & (B<=16))
            
            ranges_exp = '(' + ranges_exp + ')'      
        except:
            print("Incorrect range! Use a valid range format!")
            print("Example: --m_range=0:100,150:160,200:")
            print(USAGE)
            return
    
    #================================#
    #     Check all_bands option     #
    #================================#   
    r_bandsIDs = [opts.raster_band]
    m_bandsIDs = [opts.mask_band]
    output_files = [opts.output_raster]
    if opts.all_bands:
        try:
            r_bands = gdal.Open(opts.input_raster, gdal.GA_ReadOnly).RasterCount
            m_bands = gdal.Open(opts.input_mask, gdal.GA_ReadOnly).RasterCount
            
            if r_bands <= 1: # Single-band raster with single-band mask
                pass
            else:            # Multi-band raster...
                r_bandsIDs = [i for i in range(1, r_bands+1)]
                output_files = [str(i) + '_' + opts.output_raster for i in range(1, r_bands+1)]
                if r_bands == m_bands:  # ...with multi-band mask
                    m_bandsIDs = r_bandsIDs
                else:                   # ...with single-band mask
                    m_bandsIDs = [opts.mask_band]*r_bands
        except:
            print ("Unable to determine the number of bands of the input files (raster or mask)!")
            sys.exit(1)

    #====================================#
    #    LOOP THROUGH ALL RASTER BANDS   #
    #====================================#
    for i in range(0, len(r_bandsIDs)):
        print ("Applying mask band #%d to raster band #%d..." %(m_bandsIDs[i],
                                                                r_bandsIDs[i]) )
        #------------------------------------#
        # Building gdal_calc.py command line #
        #------------------------------------#
        gdal_exe    = 'gdal_calc.py '
        raster_opts = '-A %s --A_band=%d ' % (opts.input_raster, r_bandsIDs[i])
        mask_opts   = '-B %s --B_band=%d ' % (opts.input_mask, m_bandsIDs[i])
        
        expression = ''
        if opts.mask_range:
            expression = '--calc="A*' + ranges_exp + '" '
        else:
            expression = '--calc="A*B" '
        
        output_opts = '--outfile=%s --format=%s ' % (output_files[i], opts.output_format) 
        if opts.data_type:
            output_opts += '--type=%s ' % (opts.data_type)
        if opts.no_data_value != None:
            output_opts += '--NoDataValue=%d ' % (opts.no_data_value)
        
        gdal_calc_command = gdal_exe + raster_opts + mask_opts + expression + output_opts
        
        #------------------------------------#
        #    Run gdal_calc.py command line   #
        #------------------------------------#
        #print ('\n' + gdal_calc_command)
        #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
        try:
            process = subprocess.Popen( gdal_calc_command,
                                        shell  = True,
                                        stdin  = subprocess.PIPE,
                                        stdout = subprocess.PIPE,
                                        stderr = subprocess.PIPE, )
            # Reads the output and waits for the process to exit before returning
            stdout, stderr = process.communicate()   
            print (stdout)
            if stderr:            raise Exception (stderr)  # or  if process.returncode:
            if 'Error' in stdout: raise Exception() # Dummy! gdal_calc.py returncode is always 0!
        except Exception as message:
            print( str(message) )
            sys.exit(1)  # or sys.exit(process.returncode)
    
    #===============================#
    # Merge single-band output files#
    #===============================#
    if len(output_files) > 1:
        gdal_merge_command = ('gdal_merge.py -separate -o ' + opts.output_raster
                              + ' ' + ' '.join(output_files) )
        print ("Merging all bands into one output file...")
        #print ('\n' + gdal_merge_command)
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
        except Exception as message:
            print( str(message) )
            sys.exit(process.returncode)
        
        for outfile in output_files:
            os.remove(outfile)

if __name__ == '__main__':
    main()