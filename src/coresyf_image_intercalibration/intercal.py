#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CoReSyF Image Inter-calibration Tool
@summary:
This module runs the following Co-ReSyF tool:
    - IMAGE INTERCALIBRATION
It takes a raster image as reference and a raster image to correct.
Depending on input arguments it performs relative radiative normalisation
of the image to be corrected with the reference image.

@attention:
    - Note that both raster images must have the same dimensions.
"""

from tools.irmad import irmad
from tools.radcal import radcal
from tools.hmatch import hmatch
import tools.image
import tools.auxil
from tools.auxil import create_parser
import os, sys, logging

# create logger singleton
logger = logging.getLogger('intercal')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s:%(asctime)s - %(message)s', '%d-%m-%Y %H:%M:%S')
fh = logging.FileHandler('intercal.log', 'w')
fh.setFormatter(formatter)
logger.addHandler(fh)

def do_irmad_radcal(opts):
    # driver for the IR-MAD radcal algorithm
    logger.info("Performing IR-MAD radiometric normalization")
    irmad(opts)
    radcal(opts)
    logger.info("Completed IR-MAD radiometric normalisation")
    return

def do_histogram_match(opts):
    # driver for the histogram matching algorithm
    logger.info("Performing histogram matching")
    hmatch(opts)
    return

def main():
    parser = create_parser()
    opts = parser.parse_args()
    
    if opts.debug:
        logger.setLevel(logging.DEBUG)
    if opts.type == 'irmad':
        do_irmad_radcal(opts)    
    elif opts.type == 'match':
        do_histogram_match(opts)
    else:
        parser.error('The type method is not implemented')
    return

if __name__ == "__main__":
   
    main()
 
    for handler in logger.handlers:
        handler.close()
        logger.removeFilter(handler)