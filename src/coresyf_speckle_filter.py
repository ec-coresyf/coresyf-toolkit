#!/usr/bin/env python
#==============================================================================
#                         <coresyf_speckle_filter.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Speckle Filter)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line tool for applying SAR speckle filter
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - SPECKLE FILTER
Speckle is caused by random constructive and destructive interference resulting
in salt and pepper noise throughout the image. Speckle filters can be applied 
to the data to reduce the amount of speckle at the cost of blurred features
or reduced resolution.
It uses the command line based Graph Processing Tool (GPT) to apply speckle
filter to SAR input images. The input can be a single image or a directory
with several images.


@example:
Speckle image reduction:


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
  @todo: 
  - test all features and parameters?


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_speckle_filter.py [-s <Inputdatasource>]\n'
            "                          [--PdampingFactor=<DampingValue>] [--PedgeThreshold=<EdgeThreshold>]\n"
            "                          [--Penl=<LooksNumber>] [--PestimateENL=<Boolean>]\n"
            '                          [--Pfilter=<FilterName>] [--PfilterSizeX=<KernelXdimension>] [--PfilterSizeY=<KernelYdimension>]\n'
            '                          [--PsourceBands="<BandName1>,<BandName2>,..."]'
            "\n")  

FilterNames  = [ 'Mean', 'Median', 'Frost', 'Gamma Map', 'Lee', 'Refined Lee']
BoolOptions = ['false', 'true']


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
    parser.add_option('-s', 
                      dest="Ssource", metavar=' ',
                      help="input SAR file",)
    parser.add_option('--PdampingFactor',
                      dest="PdampingFactor", metavar=' ',
                      help=("The damping factor (Frost filter only) "
                            "Valid interval is (0, 100). Default value is 2.") ,
                      default="2",
                      type=int)
    parser.add_option('--PedgeThreshold', 
                      dest="PedgeThreshold", metavar=' ',
                      help=("The edge threshold (Refined Lee filter only)"
                            "Valid interval is (0, *). Default value is 5000."),
                      default="5000",
                      type=float, )
    parser.add_option('--Penl', 
                      dest="Penl", metavar=' ',
                      help=("The number of looks. Valid interval is (0, *)."
                            "Default value is 1.0."),
                      default="1.0",
                      type=float)
    parser.add_option('--PestimateENL', 
                      dest="PestimateENL", metavar=' ',
                      help=("Sets parameter 'estimateENL' to <boolean>."
                            "Default value is 'false'."),
                      type='choice', choices=BoolOptions,
                      default="false",)
    parser.add_option('--Pfilter', 
                      dest="Pfilter", metavar=' ',
                      help=("Parameter filter name."
                            "Value must be one of: %s ."
                            "Default value is 'Mean'.") % FilterNames,
                      type='choice', choices=FilterNames,
                      default="Mean",)
    parser.add_option('--PfilterSizeX',
                      dest="PfilterSizeX", metavar=' ',
                      help=("The kernel x dimension. Valid interval is (1, 100]."
                            "Default value is '3'"),
                      default="3",
                      type=int)
    parser.add_option('--PfilterSizeY',
                      dest="PfilterSizeY", metavar=' ',
                      help=("The kernel y dimension. Valid interval is (1, 100]."
                            "Default value is '3'"),
                      default="3",
                      type=int)
    parser.add_option('--PsourceBands',
                      dest="PsourceBands", metavar=' ',
                      help="The list of source bands.",)
    
    
    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()
    
    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.Ssource:
        print("No input file provided. Nothing to do!")
        print(USAGE)
        return  
    
    #=================================#
    #    Building gpt command line    #
    #=================================#
    gpt_exe    = 'gpt Speckle-Filter '

    input = "-Ssource=%s " % opts.Ssource
    
    filter_opts = ""    
    if opts.Pfilter == 'Frost': 
        filter_opts += "-PdampingFactor=%s " % opts.PdampingFactor 
    if opts.Pfilter == 'Refined Lee': 
        filter_opts += "-PedgeThreshold=%s " % opts.PedgeThreshold
    if opts.Penl: 
        filter_opts += "-Penl=%s " % opts.Penl
    if opts.PestimateENL: 
        filter_opts += "-PestimateENL=%s " % opts.PestimateENL
    if opts.Pfilter: 
        filter_opts += "-Pfilter=%s " % opts.Pfilter
    if opts.PfilterSizeX: 
        filter_opts += "-PfilterSizeX=%s " % opts.PfilterSizeX
    if opts.PfilterSizeY: 
        filter_opts += "-PfilterSizeY=%s " % opts.PfilterSizeY     
    if opts.PsourceBands: 
        filter_opts += "-PsourceBands=%s " % opts.PsourceBands

    gpt_exe_command = gpt_exe + input + filter_opts

    
    #============================#
    #     Run gpt command line   #
    #============================#
    print('\n' + gpt_exe_command)
    
    try:
        process = subprocess.Popen( gpt_exe_command,
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