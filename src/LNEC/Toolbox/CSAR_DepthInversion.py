#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#
import sys, os
#
import numpy as np
#
from scipy.optimize import minimize
# 
import CSAR_Classes as CL
import CSAR_Utilities as UT

"""
=====================================================================================================
Depth Inversion Related functions
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: July/2017
=====================================================================================================
CONTENT:
	
"""

#***************************************************
#		Inversion Methods
#***************************************************

def DirectDepthInversion(point, Tp):
	#-------------------------------------------------------------------------------
        #
        # perform direct inversion (Tp known (hydrodynamic input or computed offshore))
        #
        #-------------------------------------------------------------------------------		
	
	# depth inversion
	depth = DepthEstimate(point.wavelength, Tp)

	# store data
	ComputedPoint = CL.GridPointsData(point.IndexEasting, point.IndexNorthing, point.easting, point.northing, point.apriori_bathymetry, 
						point.Spectrum, point.wavelength, point.DiscriminationFlag, Tp, -depth)
	
	return ComputedPoint

#****************************************************************************************
#		Parameters estimation using linear theory (Tp, depth)
#****************************************************************************************
def WavePeriodEstimate(Lambda, h):
	#---------------------------------------------------------------
	#	estimate wave period (given a wavelengh and depth) 
	#---------------------------------------------------------------
	g = 9.80665
	
	# test for deep water
	threshold_DW = 3;
	kh = h*2*np.pi/Lambda	
	
	# deep water conditions + intermediate water term
	num = 2*np.pi*Lambda/g
	
	# intermediate water term
	fac = 2*np.pi*h/Lambda	
	den = np.tanh(fac)

	Tp = np.sqrt(num/den) if (kh<threshold_DW) else np.sqrt(num) 
	
	return Tp

def DepthEstimate(Lambda, Tp):
	#---------------------------------------------------------------
	#	estimate depth (given a wavelengh and wave period)
	#---------------------------------------------------------------
	g = 9.80665

	k = 2*np.pi/Lambda
	
	T = Tp**2
	inv = 2*np.pi*Lambda/(g*T)

	depth=np.nan if abs(inv)>1 else np.arctanh(inv)/k
	
	#if abs(inv)>1:
	#	depth = np.nan
	#else :
	#	depth = np.arctanh(inv)/k

	return depth


#***************************************************
#	Grid Points Discrimination
#***************************************************
def DiscriminatedGroups(parameters, Points):
	#----------------------------------------------------------------------------------------
	# Gather points in groups (DW, nDW, SW or other) and affect a method for depth inversion		
	#----------------------------------------------------------------------------------------
	Points = np.asarray(Points);
	# look for exception points (Deep Water or shallow water)
	DWpoints, SWpoints, nDWpoints, Otherpoints, GlobalPoints = [], [], [], [], []
	for point in Points:	 
		flag = point.DiscriminationFlag
		if flag == 0:
			Tp = WavePeriodEstimate(point.wavelength, abs(point.apriori_bathymetry))
			pt = CL.GridPointsData(point.IndexEasting, point.IndexNorthing, point.easting, point.northing, 
						point.apriori_bathymetry, point.Spectrum, point.wavelength, flag, Tp, point.apriori_bathymetry) 
			DWpoints.append(pt)
		elif flag == -1:
			pt = CL.GridPointsData(point.IndexEasting, point.IndexNorthing, point.easting, point.northing, 
						point.apriori_bathymetry, point.Spectrum, point.wavelength, flag, 0, np.nan)
			SWpoints.append(pt)
		else:
			Otherpoints.append(point)
	# gather points
	DWpoints=np.asarray(DWpoints); SWpoints=np.asarray(SWpoints)
	ExceptionPoints = CL.ExceptionPoints(DWpoints,SWpoints)

	# if no deep water points look for near deep water point
	lDW = len(DWpoints)
	Otherpoints=np.asarray(Otherpoints)
	if lDW == 0 and parameters.InversionMethod != 'direct':
		nDWpoints = []; 
		for point in Otherpoints:
			flag = point.DiscriminationFlag
			if flag == 0.5:
				nDWpoints.append(point)
			else:
				GlobalPoints.append(point)
	else:
		GlobalPoints = Otherpoints

	#gather points
	nDWpoints = np.asarray(nDWpoints); GlobalPoints = np.asarray(GlobalPoints)
	ComputationPoints = CL.ComputationPoints(GlobalPoints, nDWpoints)
	 
	# sum up grid point status
	print 'total number of points', len(Points)
	print 'number exception points', len(DWpoints)+len(SWpoints)
	print '- number of deep water points', len(DWpoints)
	print '- number of shallow water points', len(SWpoints)
	print 'number Computation points', len(nDWpoints)+len(GlobalPoints)
	print '- number of quasi deep water points', len(nDWpoints)
	print '- number of normal computation points', len(GlobalPoints)
		
	# if no deep or near deep water points only direct method is used
	if (len(DWpoints)==0) and (len(nDWpoints)==0):
		method = 'direct'
	else:
		method = parameters.InversionMethod	

	return ExceptionPoints, ComputationPoints, method

def DiscriminateGridPoints(apriori_bathymetry, Lambda):
	#--------------------------------------------------------------------------
	# Check if grid points are in deep water or in quasi deep water
	# 
	# remark: Deep water conditions are fulfilled when tanh(kh)~1, i.e. kh~3
	#         nearly DW conditions: tanh(kh)~0.9, i.e. kh~1.5
	#	  shallow water conditions tankh = kh = 0.3
	# Flags: DW -> 0
	#        nDW -> 0.5
	#        SW -> -1
	#	 other -> 1		
	#---------------------------------------------------------------------------		
	threshold_DW, threshold_nDW, threshold_SW = 3, 1.5, 0.3 
	# kh estimate
	kh = -apriori_bathymetry*2*np.pi/Lambda	

	# discriminate again
	if kh>threshold_DW:
		Flag = 0
	elif kh<threshold_SW:
		Flag = -1
	elif kh<threshold_DW and kh>threshold_nDW:
		Flag = 0.5
	else:	
		Flag = 1

	return Flag

def DeepWaterWavePeriod(Lambda):
	#------------------------------------------
	#	estimate deep water wave period
	#------------------------------------------
	g = 9.80665

	return np.sqrt(2*np.pi*Lambda/g)

def  MeanDeepWaterWavePeriod(DeepWaterPoints):
	T = [];
	for point in DeepWaterPoints:
		T.append(point.Tp)
	return np.nanmean(T), np.nanstd(T)

def SelectDeepWaterPoints(ComputingParameters, DeepWaterPoints):
	#-----------------------------------------------------------------------------------------
	#	randomly Select a bunch of spectra to be used in the depth minimization algorithm  
	#-----------------------------------------------------------------------------------------		
	nb  =  ComputingParameters.InversionParameters.ReferenceSpectraNumber
	
	if DeepWaterPoints.shape[0] <= nb:
		Points = DeepWaterPoints
	else:
		indices = np.sort(sample(xrange(DeepWaterPoints.shape[0]), nb))
		Points = DeepWaterPoints[indices]

	return Points


def SpectrumBasedMinimizationDepthInversion(parameters, Points, DWPoints, criterion):
	#-------------------------------------------------------------------------------
        #
        # perform inversion with a minimization algorithm on depth 
	# 
	# method : match of an ensemble of offshore spectrum propagated to a wide range
	# 	   of depth and comparison with the local observed spectrum  
        #
        #-------------------------------------------------------------------------------
	
	"""	
	#
	#
	# CHECK IN SAR_Bathymetry_module FOR DEVELOPMENT
	#
	#
	SelectedPoints = SAR.SelectDeepWaterPoints(parameters.ComputingParameters, DWPoints)

	# deep water points vs quasi deep water points
	if criterion==0:
		 DWPoints = IterativeInversion(parameters, DWPoints)
	
	# randomly select n (user-defined) 'Deep Water' reference grid points
	SelectedPoints = SAR.SelectDeepWaterPoints(parameters.ComputingParameters, DWPoints);
	
	# perform depth minimization on those points	
	#if criterion == 0:
		# compute iterative inversion on selected points

	# compute minimization type of depth inversion on the rest of the points
	#for point in Points:		
	"""
	
	ProcessedPoint = Points
		
	return ProcessedPoint


def WavelengthBasedMinimizationDepthInversion(parameters, Points, DWPoints, criterion):
	#-------------------------------------------------------------------------------
        #
        # perform inversion with a minimization algorithm on depth 
	# 
	# method : match of an ensemble of offshore wavelength propagated to a wide range
	# 	   of depth and comparison with the local observed(estimated) wavelength
        #
        #-------------------------------------------------------------------------------
	
	"""	
	#
	#
	# CHECK IN SAR_Bathymetry_module FOR DEVELOPMENT
	#
	#
	SelectedPoints = SAR.SelectDeepWaterPoints(parameters.ComputingParameters, DWPoints)

	# deep water points vs quasi deep water points
	if criterion==0:
		 DWPoints = IterativeInversion(parameters, DWPoints)
	
	# randomly select n (user-defined) 'Deep Water' reference grid points
	SelectedPoints = SAR.SelectDeepWaterPoints(parameters.ComputingParameters, DWPoints);
	
	# perform depth minimization on those points	
	#if criterion == 0:
		# compute iterative inversion on selected points

	# compute minimization type of depth inversion on the rest of the points
	#for point in Points:		
	"""
	
	ProcessedPoint = Points
		
	return ProcessedPoint

