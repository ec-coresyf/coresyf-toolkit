#!/usr/bin/env python
#==============================================================================
#                       <coresyf_randRasterGen.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Random Raster Generator)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line tool for generating a random raster image
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - RANDOM RASTER GENERATOR
This tool generates a raster image with random values uniformly distributed over 
the half-open interval [low, high[ (includes low, but excluded high value).
Therefore, any value within the interval is equally likely to appear within the
raster image. 
It uses the "numpy" and "GDAL" Python modules to generate raster images in
different formats: GeoTIFF, IMG (Erdas file type) or netCDF and HDF.


@example:
Example 1 - Create a random raster image and save the output into GeoTIFF format:
./coresyf_randRasterGen.py --min=0 --max=1 -o myrandomraster.tif


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
            'coresyf_randRasterGen.py.py [--min=<Value>] [--max=<Value>]\n'
            "                            [-o <OutputRaster>] [--o_format=<OutputFileFormat>]\n"
            "\n")  

OutputFormatsList  = [ 'GTiff', 'IMG', 'netCDF', 'HDF' ]



''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import numpy.random.uniform

''' PROGRAM MODULES '''


################################################################################################################
## CONTINUE HERE ###############################################################################################
'''

def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)

    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-s', 
                      dest="Ssource", metavar=' ',
                      help="input SAR file",)
    parser.add_option('--Ttarget', metavar=' ',
                      dest="Ttarget",
                      help="Sets the output file path")
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
                      help=("Sets parameter 'estimateENL' to <boolean>. "
                            "Default value is 'false'."),
                      type='choice', choices=BoolOptions,
                      default="false",)
    parser.add_option('--Pfilter', 
                      dest="Pfilter", metavar=' ',
                      help=("Parameter filter name."
                            "Value must be one of: %s ."
                            "Default value is 'None'.") % FilterNames,
                      type='choice', choices=FilterNames,
                      default="None",)
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
    
    opts.Ssource = get_ProductFile(opts.Ssource)
    if not opts.Ssource:
        print("Readable input file not found!")
        return
    
    #===============================#
    # Remove non-applicable options #
    #===============================#
    if opts.Pfilter != 'Frost': 
        del opts.PdampingFactor 
        
    if opts.Pfilter != 'Refined Lee': 
        del opts.PedgeThreshold

    source = opts.Ssource
    del opts.Ssource
    
    target = ''
    if opts.Ttarget:
        target = opts.Ttarget
        del opts.Ttarget
    
    #============================#
    #    Run gpt command line    #
    #============================#
    call_gpt('Speckle-Filter', source, target, vars(opts))


if __name__ == '__main__':
    main()