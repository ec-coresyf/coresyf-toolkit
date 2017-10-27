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

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - CALIBRATION
 It uses the command line based Graph Processing Tool (GPT) to perform radiometric
callibration of mission products. The input must be the whole product (use either
 the 'manifest.safe' or the whole product in a zip file as input).

@example:

Example 1 - Calibrate a Sentinel product S1A:
./coresyf_calibration.py --Ssource S1A_EW_GRDM_1SDH_20171001T060648_20171001T060753_018615_01F62E_EE7F.zip 
                         --Ttarget myfile

@attention: 
    @todo
    - Add a product file to be used as example in 'examples' directory
    - Develop test script

@version: v.1.0

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'

DefaultAuxFilesLookup = ['Latest Auxiliary File', 'Product Auxiliary File', 'External Auxiliary File']


""" SYSTEM MODULES """
import os
import zipfile
from argparse import ArgumentParser
from os import path
import shutil

''' PROGRAM MODULES '''
from gpt import call_gpt


TEMP_PATH_IN = os.path.abspath("temp_input") + "/"


def main():
    parser = ArgumentParser(version=VERSION)

    # ==============================#
    # Define command line options  #
    # ==============================#
    parser.add_argument('--Ssource',
                        dest="Ssource", metavar='<filepath>',
                        help="Sets source to <filepath>",
                        required=True)
    parser.add_argument('--Ttarget', metavar='<filepath>',
                        dest="Ttarget",
                        help="Sets the target to <filepath>")
    parser.add_argument('--PauxFile',
                        dest="PauxFile", metavar='<string>',
                        help="Value must be one of 'Latest Auxiliary File', 'Product Auxiliary File', "
                             "'External Auxiliary File'.",
                        default="Product Auxiliary File",
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
    target = opts.pop("Ttarget")

    if not os.path.exists(source):
        parser.error("%s does not exists." % source)
    if zipfile.is_zipfile(source):
        myzip = zipfile.ZipFile(source, 'r')
        if not myzip.infolist():
            raise ("Input Zip file '%s' is empty!" % input_path)
        myzip.extractall( TEMP_PATH_IN )
        myzip.close()
        input_list = [os.path.join(TEMP_PATH_IN, x) for x in os.listdir(TEMP_PATH_IN)] # input 
        if input_list: 
            source = input_list[0]

    # ====================================#
    #  CALL GPT                           #
    # ====================================#
    print ("Applying calibration %s..." % source)
    call_gpt('Calibration', source, target, opts)
    
    # Cleaning temp data
    if os.path.isdir(TEMP_PATH_IN):
        print("Deleting temp data...")
        datafolder = os.path.dirname(TEMP_PATH_IN)
        shutil.rmtree( datafolder )


if __name__ == '__main__':
    main()
