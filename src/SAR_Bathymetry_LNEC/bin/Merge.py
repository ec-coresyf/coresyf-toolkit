#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
===============================================================================
Co-ReSyF Research Application - SAR_Bathymetry
===============================================================================

===============================================================================
"""

import os
import argparse



########## Input arguments
parser = argparse.ArgumentParser(description='Co-ReSyF: Sar Bathymetry merging tool')
parser.add_argument('-i', '--input', nargs='+', help='List of Input text files...', required=True)
parser.add_argument('-o', '--output', help='Output file text file... ', required=True)
args = parser.parse_args()


# Creating temp folder (for temporary files)
#curdir = os.getcwd()
#if not os.path.exists(PathOut):
#    os.makedirs(PathOut)





files_list=args.input

print (args.input)

print (files_list [1])