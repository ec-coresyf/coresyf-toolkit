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




files_list=args.input

print (args.input)
output_file = open(args.output, 'w')

for i in range (0, len(files_list)):
    input_file = open(files_list[i], 'r')
    for line in input_file:
        output_file.write(line)
    
    input_file.close()

output_file.close()