#!/usr/bin/env python
# ==============================================================================
#                         <coresyf_calibration.py>
# ==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Radiometric Calibration)
# Language  : Python (v.2.6)
# ------------------------------------------------------------------------------
# Scope : Command line radiometric calibration for SNAP supported files
# Usage : (see the following docstring)
# ==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
# ==============================================================================

""" SYSTEM MODULES """
import subprocess
import sys
from optparse import OptionParser

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

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE = ("\n"
         "coresyf_calibration.py [-Ssource=<file>] [--PauxFile=<string>]\n"
         "                      [--PcreateBetaBand <boolean>] [--PcreateGammaBand <boolean>]\n"
         "                      [--PexternalAuxFile <file>] [--PoutputBetaBand <boolean>]\n"
         "                      [--PoutputGammaBand <boolean>] [--PoutputImageInComplex <boolean>]\n"
         "                      [--PoutputImageScaleInDb <boolean>] [--PoutputSigmaBand <boolean>]\n"
         "                      [--PselectPolarisations=<string,string,string,...> \n"
         "                      [--PsourceBands=<string,string,string,...>"
         "\n")

DefaultAuxFilesLookup = ['Latest Auxiliary File', 'Product Auxiliary File', 'External Auxiliary File']


def main():
    parser = OptionParser(usage=USAGE,
                          version=VERSION)

    # ==============================#
    # Define command line options  #
    # ==============================#
    parser.add_option('--Ssource',
                      dest="source", metavar='<filepath>',
                      help="Sets source 'source' to <filepath>", )
    parser.add_option('--PauxFile',
                      dest="aux_file", metavar='<string>',
                      help="Value must be one of 'Latest Auxiliary File', 'Product Auxiliary File', "
                           "'External Auxiliary File'.",
                      default="Latest Auxiliary File")
    parser.add_option('--PcreateBetaBand',
                      dest="create_beta_band", metavar='<boolean>',
                      help="Create beta0 virtual band.",
                      type=bool,
                      default=False)
    parser.add_option('--PcreateGammaBand',
                      dest="create_gamma_band", metavar=' ',
                      help="Create gamma0 virtual band.",
                      default=False,
                      type=bool)
    parser.add_option('--PexternalAuxFile',
                      dest="external_aux_file", metavar='<file>.',
                      help="The antenna elevation pattern gain auxiliary data file.")
    parser.add_option('--PoutputBetaBand',
                      dest="output_beta_band", metavar='<boolean>',
                      help="Output beta0 band.",
                      type=bool,
                      default=False)
    parser.add_option('--PoutputGammaBand',
                      dest="output_gamma_band", metavar='<boolean>',
                      help="Output gamma0 band.",
                      type=bool,
                      default=False)
    parser.add_option('--PoutputImageInComplex',
                      dest="output_image_in_complex", metavar='<boolean>',
                      help="Output image in complex.",
                      type=bool,
                      default=False)
    parser.add_option('--PoutputImageScaleInDb',
                      dest="output_image_in_scale_db", metavar='<boolean>',
                      help="Output image scale.",
                      type=bool,
                      default=False)
    parser.add_option("--PoutputSigma",
                      dest="output_sigma",
                      help="Output sigma0 band.",
                      type=bool,
                      default=True)
    parser.add_option("--PselectedPolarisations",
                      dest="selected_polarisations",
                      help="The list of polarisations.")
    parser.add_option("--PsourceBands",
                      dest="source_bands",
                      help="The list of source bands.")

    # ==============================#
    #   Check mandatory options    #
    # ==============================#
    (opts, args) = parser.parse_args()

    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.source:
        print("No input raster provided. Nothing to do!")
        print(USAGE)
        return

    # ==============================#
    #   Check data type option     #
    # ==============================#
    if opts.aux_file and opts.aux_file not in DefaultAuxFilesLookup:
        print("Incorrect output data type!")
        print("Must be one of %s." % DefaultAuxFilesLookup)
        print(USAGE)
        return

    # ====================================#
    #    LOOP THROUGH ALL SELECTED PRODUCTS#
    # ====================================#
    product_files = []
    for i in product_files:
        print ("Applying calibration %s..." % i)
        # ------------------------------------#
        # Building gpt command line #
        # ------------------------------------#
        gpt_exe = 'gpt'
        gpt_operator = 'Calibration'
        gpt_options = ''

        gpt_command = gpt_exe + gpt_operator + gpt_options

        # ------------------------------------#
        #    Run gpt command line   #
        # ------------------------------------#
        print ('\n invoking' + gpt_command)
        try:
            process = subprocess.Popen(gpt_command,
                                       shell=True,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, )
            # Reads the output and waits for the process to exit before returning
            stdout, stderr = process.communicate()
            print (stdout)
            if stderr:
                raise Exception(stderr)  # or  if process.returncode:
            if 'Error' in stdout:
                raise Exception()
        except Exception, message:
            print(str(message))
            sys.exit(1)  # or sys.exit(process.returncode)


if __name__ == '__main__':
    main()
