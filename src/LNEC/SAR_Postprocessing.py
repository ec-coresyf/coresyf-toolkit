#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
=====================================================================================================
 Co-ReSyF Research Application: Post-processing step to get the bathymetry map
				 
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: Sept/2017
=====================================================================================================
"""

import os, glob, shutil
#
import argparse
#
import numpy as np
#
import Toolbox.CSAR_Classes as CL
import Toolbox.CSAR_Utilities as UT
import Toolbox.CSAR_PostProcessing as POST
#
import shutil

# input output
parser = argparse.ArgumentParser(description='Co-ReSyF: SAR Bathymetry Research Application')
parser.add_argument('-i', '--input',nargs='+', help='Input files for grid points with inverted depth (Inversion.out) for bathymetry mapping', required=False)
parser.add_argument('-o', '--output',nargs='+', help='Output file names', required=False)
parser.add_argument('-v', '--verbose', help='Screen comments', action="store_true")
args = parser.parse_args()

if args.verbose:
	print '|--------------------------------|'
	print '|	Post-Processing		 |'
	print '|--------------------------------|'

# get list of parameters and image data
fname2='Image.out'
data = UT.Unpickle_File(fname2)

# merge all computed point data in an array
BathymetryPoints = []

# get list of filenames () 
ExceptionList, ExceptionPoints = [], []
if args.input:
	List = args.input
	FileList, ExceptionList = UT.ListDichotomy(List)
else:
	FileList = [x for x in os.listdir('./') if x.startswith("Inversion")]
	ExceptionList = [x for x in os.listdir('./') if x.startswith("ExceptionPoints")] 

# load Exception Points

if len(ExceptionList)>0:
	fname = str(ExceptionList[0])
	if os.path.exists(fname):
		ExceptionPoints = UT.Unpickle_File(fname)

# load & gather all data from computation points
for filename in FileList:
	fname = filename
	point = UT.Unpickle_File(fname)
	BathymetryPoints.append(point)

# merge all data together

if ExceptionPoints:	
	ProcessedPoints = POST.MergeData(ExceptionPoints, BathymetryPoints);
else: 
 	ProcessedPoints = BathymetryPoints;

ProcessedPoints = np.asarray(ProcessedPoints);
if args.verbose:
	print 'number of Processed Points', len(ProcessedPoints)

# post-processing step
POST.BathymetryMap(ProcessedPoints, args.output)
#print 'OK1_Main'
POST.PostProcessing(ProcessedPoints, data)
#print 'OK2_Main'


# clean directory
if args.input:
	os.remove(args.input)
else:
	for filename in FileList:
		os.remove(filename)
[os.remove(L) for L in glob.glob('*.out')], [os.remove(L) for L in glob.glob('*.tif')]
