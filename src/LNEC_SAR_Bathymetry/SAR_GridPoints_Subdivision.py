#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
=====================================================================================================
 Co-ReSyF Research Application: Point Subdivision 
				 
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: Nov/2017
=====================================================================================================
"""

import os
#
import shutil
#
import argparse
import ConfigParser
from datetime import datetime
#
import cPickle as pickle
#
import numpy as np
#
import Toolbox.CSAR_Classes as CL
import Toolbox.CSAR_Utilities as UT
import Toolbox.CSAR_DepthInversion as INV

print '|------------------------------------------------------------------------------|'
print '| Perform point subdivision (Deep water, Shallow water, regular grid points)   |'
print '|------------------------------------------------------------------------------|'

############################
# input parameters and data
############################
parser = argparse.ArgumentParser(description='Co-ReSyF: SAR Bathymetry Research Application')
#input output
parser.add_argument('-a', '--param', help='Parameters file for Wings (.ini file)', default = 'Config_Inversion.ini',required=False)
parser.add_argument('-i', '--input', nargs='+', help='Input grid point files (spectrum.out) for point subdivision', required=False)
parser.add_argument('-o', '--output', help='Output transfer file (exception.out & Computation#.out)', required=False)
#inversion parameters
parser.add_argument('-l', '--tide', help='Tide level for depth correction', default=0,  required=False)
parser.add_argument('-T', '--Tp', help='Peak Wave Period (buoys or model data)', default=12,  required=False)
parser.add_argument('-m', '--method', help='method used for depth Inversion (inversion of relation dispersion or minimization algorithm)', default='direct',  required=False)
parser.add_argument('-w', '--wave_theory', help='Wave Theory in use (linear/nonlinear)', default='linear',  required=False)

#comments
parser.add_argument('-v','--verbose', help="comments and screen outputs", action="store_true")

args = parser.parse_args()

RunId = datetime.now().strftime('%Y%m%dT%H%M%S')

#create config.ini file
parOut = open(args.param, "w"); Config = ConfigParser.ConfigParser(); Config.add_section("Arguments")

#input/output	
Config.set("Arguments", "Input_file", args.input);
Config.set("Arguments", "Output_file", args.output); 

#inversion parameters
Config.set("Arguments", "Tide", args.tide); 
Config.set("Arguments", "Peak_Period_Tp", args.Tp)
Config.set("Arguments", "Inversion_method", args.method); 
Config.set("Arguments", "Wave_Theory", args.wave_theory); 
Config.add_section("Run")
Config.set("Run", "Id", RunId)
Config.write(parOut); parOut.close()

#store data
HydroParameters = CL.HydrodynamicParameters(args.tide, args.Tp)
parameters = CL.InversionParameters(HydroParameters, args.method, args.wave_theory)

# merge all the spectrum data in an array
ComputationPoints = []

if args.input:
	FileList = args.input
else:
	FileList = [x for x in os.listdir('./') if x.startswith("Spectrum")]

for fname in FileList:
	point = UT.Unpickle_File(fname)
	ComputationPoints.append(point)

#####################
# domain division
#####################

# divide domain in between exception (deep/shallow water) and real computation points
ExceptionPoints, ComputationPoints, method = INV.DiscriminatedGroups(parameters, ComputationPoints)

# redefine inversion parameters if change in method
InversionParameters_global = CL.InversionParameters(parameters.HydrodynamicParameters, method, parameters.WaveTheory)
InversionParameters_reference = CL.InversionParameters(parameters.HydrodynamicParameters, 'direct', parameters.WaveTheory)

# store exception points and dispatch other points

#exception points
if len(ExceptionPoints.DeepWaterPoints)>0 or len(ExceptionPoints.ShallowWaterPoints)>0:
	fname = args.output
	UT.Pickle_File(fname, ExceptionPoints)

# global computation points
# Quasi Deep water points
if len(ComputationPoints.QuasiDeepWaterPoints)>0:
	InversionParameters = InversionParameters_reference
	filename = 'QuasiDeepwaterPoints'
	for i,point in enumerate(np.asarray(ComputationPoints.QuasiDeepWaterPoints)):
		fname = args.output
		data = CL.InversionData(InversionParameters, point) 
		data.pickle(fname)
# global points
if len(ComputationPoints.GlobalPoints)>0:
	filename = 'ComputationPoints'
	InversionParameters = InversionParameters_global
	for i,point in enumerate(np.asarray(ComputationPoints.GlobalPoints)):
		fname = args.output
		data = CL.InversionData(InversionParameters, point) 
		data.pickle(fname)


