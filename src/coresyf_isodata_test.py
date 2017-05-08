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
# import os
# import zipfile
# from argparse import ArgumentParser
# from os import path
# 
# from product_selector import ProductSelector
# from gpt import call_gpt

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

'''
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
    if path.isfile(source) and selector and not zipfile.is_zipfile(source):
        parser.error("Selectors should be used only for sources which are directories or zips.")
    if path.isdir(source) and not selector:
        parser.error("Selector parameter is missing.")
    if path.isdir(source) and target:
        parser.error("Target should not be specified when multiple source files are selected from a dir.")

    ps = ProductSelector(selector)

    # ====================================#
    #  LOOP THROUGH ALL SELECTED PRODUCTS#
    # ====================================#
    if path.isdir(source):
        product_files = [path.join(source, fname) for fname in os.listdir(source)
                         if ps.isproduct(path.join(source, fname))]
        print("selected files: %s%s" % (os.linesep, os.linesep.join(product_files)))
    else:
        product_files = [source]

    for i in product_files:
        print ("Applying calibration %s..." % i)
        call_gpt('Calibration', ps.openproduct(i), target, opts)
'''

#if __name__ == '__main__':    
    #main()







from pyradar.classifiers.isodata import isodata_classification
from pyradar.core.equalizers import equalization_using_histogram
from pyradar.core.sar import create_dataset_from_path
from scipy import misc
import os
import Image
import numpy as np
#import datetime

#from pyradar.core.sar import save_image

def save_image(img_dest_dir, filename, img):
    """
    Save an image with date and time as it filename.
    Parameters:
            img_dest_dir: the destination of the image.
            filename: a name for the file. With no extension.
            image: a numpy matrix that contains the image.
    """
    name = filename
    if not filename:
        # Create a unique name based on time:
        time_format = '%d%m%y_%H%M%S'
        time_today = datetime.today()
        name = time_today.strftime(time_format)
 
    supported_extensions = ['tiff']
    extension = 'tiff'
    filename = name + '.' + extension
 
    assert extension in supported_extensions, "ERROR: save_image(). " \
                                              "format not valid."
    # Forge the path:
    img_dest_path = os.path.join(img_dest_dir, filename)
 
    # Convert the image from the numpy matrix using Image module:
    img_obj = Image.fromarray(img.astype(np.uint8))
 
    # And save it!
    img_obj.save(img_dest_path, extension)
    img_obj = None
 
    print 'File saved to "' + img_dest_path + '".'
    

params = {"K": 10, "I" : 100, "P" : 0, "THETA_M" : 1, "THETA_S" : 0.1,
          "THETA_C" : 2, "THETA_O" : 0.01}

IMAGE_PATH = "/home/rccc/Downloads/LC81360272014242LGN00_B1.TIF"
IMG_DEST_DIR = "/home/rccc/Downloads/"
# create dataset
#dataset = create_dataset_from_path(IMAGE_PATH)

dataset = misc.imread(IMAGE_PATH)


# run Isodata
class_image = isodata_classification(dataset, parameters=params)

# equalize class image to 0:255
class_image_eq = equalization_using_histogram(class_image)

# save it
save_image(IMG_DEST_DIR, "class_image_eq", class_image_eq)
# also save original image
image_eq = equalization_using_histogram(dataset)

# save it
save_image(IMG_DEST_DIR, "image_eq", image_eq)
