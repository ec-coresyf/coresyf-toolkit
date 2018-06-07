#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


"""
=====================================================================================================
Definition of the different subset (and FFT Boxes) associated with the grid points   
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: May/2017
 Last update: August/2017
=====================================================================================================
	
	GetBoxDim	GetImageSubset		GetSubsetCenters	GetFFTBoxes
	CreateSubsetNPZ
	
"""
#
import os
#
import numpy as np
import matplotlib.pyplot as plt
#
import cv2
#
import CSAR_Classes as CL
import CSAR_ImageProcessing as IP
#

def GetBoxDim(subsetparameters, subset):
	#------------------------------------------------------------------
	# defined box dimension as a function of :
	#		- image resolution 
	#		- domain length (m) : 1000m<length<2000m
	#------------------------------------------------------------------
	# rough estimate of the box dimension in pixel 	
	DimensionPixel = np.int(np.round(((subsetparameters.DomainDimension)/subset.resolution[0])))

	# refine dimension for computation efficiency
	if subsetparameters.FlagPowerofTwo:
		# dimension as a functionnearest power of 2
		power = np.round(np.log(DimensionPixel)/np.log(2))
		DimensionPixel = 2**power
	else:
		# dimension as a combination of simple prime numbers (2,3,5,...)
		DimensionPixel = cv2.getOptimalDFTSize(DimensionPixel)
	
	# box dimension in meter
	DimensionMeters = DimensionPixel*subset.resolution[0]
	
	# range from center
	BoxRange = np.zeros(2) + np.int(np.round(DimensionPixel/2.))
	residual = np.mod(DimensionPixel,2)


	if residual>1:
		BoxRange[0] = np.int(np.round(DimensionPixel/2.))-1
	
	# store data
	dimension = CL.SubsetDimension(DimensionPixel, DimensionMeters, BoxRange)	

	return dimension


def GetImageSubset(subsetparameters, data, dimensions):
	#------------------------------------------------------------------
	# Create square image subset from predefined corner points
	#------------------------------------------------------------------	
	Point = subsetparameters.Point
        
        	
	# get and scale image subset
	BoxRange = dimensions.BoxRange; BoxRange = BoxRange.astype(int); 
	image = data.image[Point[1]-BoxRange[0]:Point[1]+BoxRange[1],Point[0]-BoxRange[0]:Point[0]+BoxRange[1]]

	# get and store corresponding coordinates	
	easting = data.coordinates.easting[Point[1]-BoxRange[0]:Point[1]+BoxRange[1],Point[0]-BoxRange[0]:Point[0]+BoxRange[1]]
	northing = data.coordinates.northing[Point[1]-BoxRange[0]:Point[1]+BoxRange[1],Point[0]-BoxRange[0]:Point[0]+BoxRange[1]]
	coordinates = CL.Coordinates(northing, easting)
	
	#store subset data
	FlagFlip = IP.CheckImageOrientation(coordinates)
	subset = CL.Subset(Point, image, coordinates, data.resolution, FlagFlip)	
	
	return subset

def GetSubsetCenters(Point, offset, BoxNb):
	#----------------------------------------------------------
	# Define list of centers of the overlapping subsets
	#----------------------------------------------------------
	if BoxNb == 5:
		subset_centers=[(np.int(Point[0]-np.ceil(offset[0])),	np.int(Point[1]-np.ceil(offset[0]))),
				(np.int(Point[0]+np.ceil(offset[1])),	np.int(Point[1]-np.ceil(offset[0]))),
				(Point[0],Point[1]),
				(np.int(Point[0]-np.ceil(offset[0])),	np.int(Point[1]+np.ceil(offset[1]))),
				(np.int(Point[0]+np.ceil(offset[1])),	np.int(Point[1]+np.ceil(offset[1])))]


	elif BoxNb == 9:
		subset_centers=[(np.int(Point[0]-np.ceil(offset[0])),	np.int(Point[1]-np.ceil(offset[0]))),
				(np.int(Point[0]) 		,	np.int(Point[1]-np.ceil(offset[0]))),
				(np.int(Point[0]+np.ceil(offset[1])),	np.int(Point[1]-np.ceil(offset[0]))),
				(np.int(Point[0]-np.ceil(offset[0])),	np.int(Point[1])),	
				(np.int(Point[0])		,	np.int(Point[1])),
				(np.int(Point[0]+np.ceil(offset[1])),	np.int(Point[1])),
				(np.int(Point[0]-np.ceil(offset[0])),	np.int(Point[1]+np.ceil(offset[1]))),
				(np.int(Point[0])		,	np.int(Point[1]+np.ceil(offset[1]))),
				(np.int(Point[0]+np.ceil(offset[1])),	np.int(Point[1]+np.ceil(offset[1])))]
	return subset_centers

def GetFFTBoxes(subsetparameters, data, dimension):

	#---------------------------------------------------------------------------------------------------------------
	# Create list of overlapping subset images to estimate spectrum at a given grid point (center of main subset) 
	#---------------------------------------------------------------------------------------------------------------
	# initialisation	
	#images, northings, eastings= [],[],[]
	Subsets=[]
	# Get the various subset images centers (box defined with an offset from the main subset, the overlapping is controlled by the offset) 
	offset = subsetparameters.Shift*dimension.BoxRange; 
	subset_centers =  GetSubsetCenters(subsetparameters.Point, offset, subsetparameters.BoxNb)
	# get information on subsets (coordinates, image footprint)
	for i in subset_centers:
		# get subset	
		subsetparameters.Point = i
		subset = GetImageSubset(subsetparameters, data, dimension)
		# get coordinates
		coordinates = CL.Coordinates(subset.coordinates.northing, subset.coordinates.easting)
		FlagFlip = IP.CheckImageOrientation(coordinates)
		subsets = CL.Subset(i, data.image, coordinates, data.resolution, FlagFlip) 
		Subsets.append(subsets)	
		"""
		# concatenate data
		images.append(image); eastings.append(subset.coordinates.easting); northings.append(subset.coordinates.northing)
		
	#store data
	coordinates = Coordinates(northings,eastings)
	subsets = Subset(subset_centers, images, coordinates, data.resolution) 
	"""
		
	return Subsets


