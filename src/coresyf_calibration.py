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
from argparse import ArgumentParser
from os import path
import os
import glob

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

DefaultAuxFilesLookup = ['Latest Auxiliary File', 'Product Auxiliary File', 'External Auxiliary File']

def main():
    parser = ArgumentParser(version=VERSION)

    # ==============================#
    # Define command line options  #
    # ==============================#
    parser.add_argument('--Ssource',
                      dest="Ssource", metavar='<filepath>',
                      help="Sets source to <filepath>",
                        required=True)
    parser.add_argument('--Pselector',
                        dest="Pselector", metavar='<glob>',
                        help="A glob to select the appropriate product files from a directory.")
    parser.add_argument('--Ttarget', metavar='<filepath>',
                        dest="Ttarget",
                        help="Sets the target to <filepath>")
    parser.add_argument('--PauxFile',
                      dest="PauxFile", metavar='<string>',
                      help="Value must be one of 'Latest Auxiliary File', 'Product Auxiliary File', "
                           "'External Auxiliary File'.",
                      default="Latest Auxiliary File",
                        choices=DefaultAuxFilesLookup)
    parser.add_argument('--PcreateBetaBand',
                      dest="PcreateBetaBand", metavar='<boolean>',
                      help="Create beta0 virtual band.",
                      type=bool,
                      default=False)
    parser.add_argument('--PcreateGammaBand',
                      dest="PcreateGammaBand", metavar='<boolean>',
                      help="Create gamma0 virtual band.",
                      default=False,
                      type=bool)
    parser.add_argument('--PexternalAuxFile',
                      dest="PexternalAuxFile", metavar='<file>',
                      help="The antenna elevation pattern gain auxiliary data file.")
    parser.add_argument('--PoutputBetaBand',
                      dest="PoutputBetaBand", metavar='<boolean>',
                      help="Output beta0 band.",
                      type=bool,
                      default=False)
    parser.add_argument('--PoutputGammaBand',
                      dest="PoutputGammaBand", metavar='<boolean>',
                      help="Output gamma0 band.",
                      type=bool,
                      default=False)
    parser.add_argument('--PoutputImageInComplex',
                      dest="PoutputImageInComplex", metavar='<boolean>',
                      help="Output image in complex.",
                      type=bool,
                      default=False)
    parser.add_argument('--PoutputImageScaleInDb',
                      dest="PoutputImageScaleInDb", metavar='<boolean>',
                      help="Output image scale.",
                      type=bool,
                      default=False)
    parser.add_argument("--PoutputSigmaBand", metavar='<boolean>',
                      dest="PoutputSigmaBand",
                      help="Output sigma0 band.",
                      type=bool,
                      default=True)
    parser.add_argument("--PselectedPolarisations", metavar='<string,string,string,...>',
                      dest="PselectedPolarisations",
                      help="The list of polarisations.")
    parser.add_argument("--PsourceBands", metavar='<string,string,string,...>',
                      dest="PsourceBands",
                      help="The list of source bands.")

    opts = vars(parser.parse_args())

    source = opts.pop("Ssource")
    selector = opts.pop("Pselector")
    target = opts.pop("Ttarget")

    if not os.path.exists(source):
        parser.error("%s does not exists." % source)
    if path.isfile(source) and glob:
        parser.error("Selectors should be used only for sources which are directories.")
    if path.isdir(source) and not glob:
        parser.error("Selector parameter is missing.")

    # ====================================#
    #  LOOP THROUGH ALL SELECTED PRODUCTS#
    # ====================================#
    product_files = []
    if path.isdir(source):
        product_files = [file for file in glob.glob(source + path.sep + selector)]
        print("selected files: %s%s" % (os.linesep, os.linesep.join(product_files)))
    else:
        product_files = [source]

    for i in product_files:
        print ("Applying calibration %s..." % i)
        call_gpt('Calibration', i, target, opts)


def parameter(prefix, value):
    format = ("-%s=\"%s\"" if isinstance(value, basestring) else "-%s=%s")
    return format % (prefix, value)


def call_gpt(operator, source, target, options):
    # ------------------------------------#
    # Building gpt command line #
    # ------------------------------------#
    gpt_options = ' '.join([parameter(key, value) for key, value in options.items() if value is not None])
    gpt_command = "gpt %s -f GeoTIFF -t \"%s\" -Ssource=\"%s\" %s" % (operator, target, source, gpt_options)
    # ------------------------------------#
    #    Run gpt command line   #
    # ------------------------------------#
    print ('\n invoking: ' + gpt_command)
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
        #sys.exit(1)  # or sys.exit(process.returncode)


if __name__ == '__main__':
    main()
