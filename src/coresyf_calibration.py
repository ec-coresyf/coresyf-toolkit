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
import os
import zipfile
from argparse import ArgumentParser
from os import path
import shutil

''' PROGRAM MODULES '''
from gpt import call_gpt


TEMP_PATH_IN = os.path.abspath("temp_input") + "/"


'''
@summary: 
TBC

@example:
TBC          

@attention: 
TBC

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
    
    # Rename target file 
    os.rename(target + ".tif", target)


if __name__ == '__main__':
    main()
