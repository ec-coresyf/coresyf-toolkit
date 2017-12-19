#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
=====================================================================================================
 Co-ReSyF Research Application: Spectra and wavelengths estimation 
				 
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: Nov/2017
=====================================================================================================
"""
import os
#
import numpy as np
#
import Toolbox.CSAR_Classes as CL
import Toolbox.CSAR_Utilities as UT
import Toolbox.CSAR_Spectrum as SP
import Toolbox.CSAR_DepthInversion as INV
import Toolbox.CSAR_PostProcessing as POST

#********************************************
#  Spectrum and Peak Wavelength Computation
#********************************************

# input output
ComputingParameterSpectrum, args = SP.InputSpectrumParameters()


# read parameters, point and subset data
cwd = os.getcwd()
path = cwd+'/'
fname = path + args.input
index = int(filter(str.isdigit, fname))
Subset = UT.Unpickle_File(fname)
SubsetsParameters, point, Subsets = Subset.parameters, Subset.point, Subset.SubsetData

if args.verbose and index==0:
	print '|-------------------------------------------|'
	print '| Compute Spectra and estimate wavelengths  |'
	print '|-------------------------------------------|'

##################################
# pb here
##################################

# compute global subset spectrum
Spectrum, OutputSpectrumData = SP.ComputeSpectrum(SubsetsParameters, ComputingParameterSpectrum, Subsets) 
	
# create and store spectra and subsets figure for each grid point 
POST.Plot_Subset_Spectrum(index, OutputSpectrumData, Spectrum)
	
#********************************************
#  	Grid Point Distribution
#********************************************
# estimate wave number and determine offshore points
wavelength = Spectrum.WaveSpectrum.Wavelength
apriori_Bathymetry = point.apriori_bathymetry;

#discriminate grid points (deep water, near deep water, nearshore, other)
Flag = INV.DiscriminateGridPoints(apriori_Bathymetry, wavelength)

#********************************************
#  	Gather and save point information
#********************************************
#gather point information
pt =  CL.GridPointsData(point.IndexEasting, point.IndexNorthing, point.easting, point.northing, apriori_Bathymetry, Spectrum, wavelength, Flag)

#save point information
UT.Create_TransferFile(args,pt,'Spectrum')

#remove subsets info file
os.remove(args.input)

