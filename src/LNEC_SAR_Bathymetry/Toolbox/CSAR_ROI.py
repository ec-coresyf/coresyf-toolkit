#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


"""
=====================================================================================================
Definition of Region of Interest: mandatory preprocessing to get grid scatter points and dimensions  
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: June/2017
 Last update: August/2017
=====================================================================================================
"""
#
import os, sys
import time
#
import numpy as np
import matplotlib.pyplot as plt
#
import CSAR_Classes as CL
import CSAR_Utilities as UT
import CSAR_ImageProcessing as IP
#
import cv2
#
from scipy.interpolate import griddata, Rbf
#
#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%
#		IMAGE ROI
#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%

#**********************
#	MAIN
#**********************
def DefineComputationGrid(parameters, data):
	#----------------------------------------------------------------------------------------
	#
	# Create Computation Grid according to user-defined parameters
	#
	# Possible inputs: PointsFileName -> file containing sets of predefined grid points
	# 		   PolygonFileName -> file gathering predefined polygon corner points  
	# 		   GridResolution -> Grid resolution / dx in meters
	#----------------------------------------------------------------------------------------	
	#
	# get the grid spatial Resolution
	ResolutionPixels, ResolutionMeters = IP.ResolutionPixel(parameters, data)	
	
	# easting and northing coordinates
	easting = data.coordinates.easting[0,:]; northing = data.coordinates.northing[:,0];
	
	# create global image grid with the given grid resolution in pixels		
	GlobalGridPoints = GetImageGridPoints(data, ResolutionPixels)
	

	# define ROI corner points
	ROIParameters = parameters.ROI_Definition_Parameters
	
	if (ROIParameters.PolygonFileName == None) or (not os.path.isfile(ROIParameters.PolygonFileName)):
		ROIPoints = DefinePolygonalROI(data)
	else:
	        ROIPoints = UT.ReadPointsfromFile(ROIParameters.PolygonFileName)

	# save points
	UT.WritePointstoFile(ROIPoints, 'Polygon.txt')
	
	# find points belonging to the selected domain
        DomainPoints = DomainGridPoint(ROIPoints, GlobalGridPoints)
	
	# plot subsets borders
	E = data.coordinates.easting[0,:]; N = data.coordinates.northing[:,0];
        
	flagplot = False
	if flagplot:
		fig, ax = plt.subplots(1)
		ax.imshow(data.image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(E), np.max(E), np.min(N), np.max(N)])
	
		for i in range(ROIPoints.shape[0]):
			ax.plot(ROIPoints[i].easting, ROIPoints[i].northing,'sb')

		for i in range(GlobalGridPoints.shape[0]):
			ax.plot(GlobalGridPoints[i].easting, GlobalGridPoints[i].northing,'or')
	
		for i in range(DomainPoints.shape[0]):
			ax.plot(DomainPoints[i].easting, DomainPoints[i].northing,'xg')	

	# plot & close windows
	plt.show()

	return DomainPoints

#************************************
#	GLOBAL GRID DEFINITION
#************************************
def GridSubSamplingIndices(n,resolution):
	#-----------------------------------
	# create subsampling 1D grid indices	
	#-----------------------------------
	# grid index	
	GridIndex = np.arange(n);

	# subsampling 
	Ind = GridIndex[::resolution]
	
	# recenter subsampling
	fac = np.floor(0.5*(n-np.max(Ind)))
	Ind = Ind + fac

	Indices = Ind.astype(int)	
	return Indices

def GetImageGridPointsIndices(data, ResolutionPixels):
	#----------------------------------------------------------------------------------------
	#
	# Create Grid according to the image dimension and user-defined resolution
	#
	#----------------------------------------------------------------------------------------
	GlobalGridPoints = []
	
	# get image dimension
	easting = data.coordinates.easting[0,:]; northing = data.coordinates.northing[:,0];
	nx = easting.shape[0]; ny = northing.shape[0]
		
	# create points indices arrays
	IndicesX = GridSubSampling(nx,ResolutionPixels)
	IndicesY = GridSubSampling(ny,ResolutionPixels)
	X, Y = np.meshgrid(IndicesX, IndicesY)
	# flatten the arrays for fast computation
	indx = X.flatten()
	indy = Y.flatten()
	
	# gather all information about grid points
	for i in range(indx.shape[0]):
		indexx = indx[i]; indexy = indy[i]
		east = easting[indexx]; north = northing[indexy];
		Point = CL.GridPoints(east, north)	
		GlobalGridPoints.append(Point)
	
	# array format
	GlobalGridPoints = np.asarray(GlobalGridPoints)

	return GlobalGridPoints


def GridSubSampling(data,resolution):
	#-----------------------------------
	# create subsampling 1D grid indices	
	#-----------------------------------
	# grid index	
	
	# subsampling 
	coordinates = data[::resolution]
	
	# recenter subsampling
	fac = np.floor(0.5*(data[-1] - coordinates[-1]))
	coordinates = coordinates + fac
	
	return coordinates


def GetImageGridPoints(data, ResolutionPixels):
	#----------------------------------------------------------------------------------------
	#
	# Create Grid according to the image dimension and user-defined resolution
	#
	#----------------------------------------------------------------------------------------
	GlobalGridPoints = []
	
	# get image dimension
	easting = data.coordinates.easting[0,:]; northing = data.coordinates.northing[:,0];
	
		
	# create points indices arrays
	Easting = GridSubSampling(easting,ResolutionPixels) 
	Northing = GridSubSampling(northing,ResolutionPixels)
	E, N = np.meshgrid(Easting, Northing)
	# flatten the arrays for fast computation
	East = E.flatten()
	North = N.flatten()
	
	# gather all information about grid points
	for i in range(East.shape[0]):
		Point = CL.GridPoints(East[i], North[i])	
		GlobalGridPoints.append(Point)
	
	# array format
	GlobalGridPoints = np.asarray(GlobalGridPoints)

	return GlobalGridPoints



#************************************
#	ROI DEFINITION
#************************************

def CreatePolygon(indices, image, easting, northing):
	#----------------------------------------------
	# create a polygonial region of interest (ROI) 
	#----------------------------------------------
	ROI_points = []
	for i in range(indices.shape[0]):
		indx, indy = indices[i, 0], indices[i, 1]	        # indices
		East, North = easting[indx], northing[indy]	        # coordinates
		cv2.circle(image,(indx,indy),10,(255,255,255),-1)	# plot points
		point = CL.GridPoints(East, North)		
		# store points
		ROI_points.append(point)

	ROI_points = np.asarray(ROI_points)
	return ROI_points

def CreateRectangle(indices, image, easting, northing):
	#----------------------------------------------
	# create a rectangular region of interest (ROI) 
	#----------------------------------------------
	
	# create index array from the 2 points (diagonal) 
	index = np.zeros((4,2))
	index[0,:] = [np.min(indices[:,0]), np.min(indices[:,1])] 	# lower left corner
	index[1,:] = [np.min(indices[:,0]), np.max(indices[:,1])]		# upper left corner
	index[2,:] = [np.max(indices[:,0]), np.max(indices[:,1])]		# upper right corner
	index[3,:] = [np.max(indices[:,0]), np.min(indices[:,1])]		# lower right corner
	
	# rewrite indices array
	indices = index.astype(int);
	
	# create corner points
	ROI_points = CreatePolygon(indices, image, easting, northing)

	return ROI_points, indices

def DefinePolygonalROI(data):
	#-------------------------------------------------------------------------------------------------
	# create a polygonial region of interest (ROI) to crop the image and perform wavelength estimation
	#-------------------------------------------------------------------------------------------------

	# load data
	image = data.image; image = cv2.convertScaleAbs(image); 
	easting = data.coordinates.easting; northing = data.coordinates.northing

	# resize image parameters (reduce resolution)
	fac = 5
	dimension = (np.round(image.shape[0]/fac), np.round(image.shape[1]/fac))

	# resize image
	image = UT.ResizeArray(image, dimension); 
	northing = UT.ResizeArray(northing, dimension); easting = UT.ResizeArray(easting, dimension)

	# clone image
	clone = image.copy(); N = northing.copy(); E = easting.copy(); Northing = N[:,0]; Easting = E[0,:];
	
	# initialize list of points: reference points (corners) indices and coordinates
	ReferencePoints, ContourCoordinates = [], []

	# image attribute for cropping with OpenCV
	points = CL.StoreIndices()
	cv2.namedWindow('image',cv2.WINDOW_NORMAL);
	cv2.resizeWindow('image', 600,600)
	cv2.setMouseCallback('image', points.select_point)

	
	# display options
	print """
	####################################
	#   Press 'r' to reset points.     #
	#   Press 's' to save points.      #
	#   Press 'q' to quit.             #
	####################################
	"""
	# loop to create ROI
	while True:
		
		# display image
		cv2.imshow('image', image)
		key = cv2.waitKey(1) & 0xFF

		# reset
		if key == ord("r"):
			del points.indices[0:]; image = clone.copy()
		# quit
		elif key == ord("q"):
			cv2.destroyWindow("image")
			break
		
		# define and save ROI
		elif key == ord("s"):
			# save selected points
			indices=np.asarray(points.indices)

			# check the number of selected points (2-> rectangle, 3 or + -> polygon)			
			dimension = indices.shape[0]		
			if dimension < 3: 
				ROI_points,indices = CreateRectangle(indices, image, Easting, Northing)
			else:
				ROI_points = CreatePolygon(indices, image, Easting, Northing)


			#print domain edges
			cv2.polylines(image, [indices.reshape((-1,1,2))],True, (255, 255, 255),2)
			
			# change data format
       			
			
	return ROI_points


def DomainGridPoint(ROI, GridPoints):
        #----------------------------------------------------------------------
        #
        # Look for grid points within the user-defined ROI
        #
        #----------------------------------------------------------------------
        # initialization
        DomainPoints = []
	
	#transform ROI array
	ROI = UT.List2Array(ROI)
	CornerPoints = ROI.reshape((-1,1,2)).astype(np.float32)
        # list grid points within the ROI
        for i in range(GridPoints.shape[0]):
		# easting, northing coordinates
                easting, northing = GridPoints[i].easting, GridPoints[i].northing
		# corresponding indices                 
		isinROI=cv2.pointPolygonTest(CornerPoints,(easting,northing), False)
                if isinROI != -1.0:
                        DomainPoints.append(GridPoints[i])

        DomainPoints = np.asarray(DomainPoints)

        return DomainPoints

def RemoveLandGridPoints(Points, data):
	#------------------------------
        #
        # Remove Land Grid Points
        #
        #------------------------------
	#initialization step	
	npt = Points.shape[0]
	ind = np.zeros(npt)
	easting = data.coordinates.easting[0,:]; northing = data.coordinates.northing[:,0]

	Point = []
	# look for points on land
	for i in range(npt):
		point = Points[i]
		indE = np.nanargmin(abs(point.easting-easting)); indN = np.nanargmin(abs(point.northing-northing))
		if (data.image[indN,indE]>0):
			Point.append(point)
	
	Point = np.asarray(Point);

	return	Point
#************************************
#	a priori bathymetry
#************************************

def Get_apriori_bathymetry(parameters, points):

	# transform input data
	Coordinates = PointsList2Coordinates(points)
	
	# Find Collocated bathymetry
	coord, bathy = FindCollocatedBathymetry(parameters.BathymetryParameters, Coordinates)
	bathydata = CL.BathymetryData(coord, bathy)

	# interpolate bathymetry on the grid points
	Bathymetry_Data = InterpolateBathymetry(parameters.MiscellaneousParameters, Coordinates, bathydata)

	return Bathymetry_Data

def FindCollocatedBathymetry(parameters,Coordinates):

	#------------------------------------------------------------------------
	# Find Collocated bathymetry corresponding to the input data coordinates
	#------------------------------------------------------------------------

	# Read EMODnet bathymetry
	coord, bathy = ReadGtiffBathymetry(parameters)

	# find collocated bathymetry
	coordinates, bathymetry = CollocatedData(Coordinates, coord, bathy)
	
	return coordinates, bathymetry

def InterpolateBathymetry(parameters, Coordinates, bathydata):
	
	#------------------------------------------------------------------------
	# Find Collocated bathymetry corresponding to the input data coordinates
	#------------------------------------------------------------------------
	#initialization	
	# grid points	
	easting = Coordinates.easting; northing = Coordinates.northing; 	
	npt = easting.shape[0]; bathymetry = np.zeros(npt);  
	
	# current bathymetry	
	coord = bathydata.Coordinates; bathy = bathydata.Bathymetry
	e, n = np.meshgrid(coord.easting, coord.northing)	
	
	
	#interpolate on the grid points
	
	if parameters.InterpolationMethod == 'multiquadric':
		rbfi = Rbf(e, n, bathy)
		bathymetry = rbfi(easting, northing) 
	else:
		bathymetry = griddata((e.ravel(),n.ravel()), bathy.ravel(), (easting,northing), method=parameters.InterpolationMethod)
	
	BathymetryData = CL.BathymetryData(Coordinates, bathymetry)


	"""
	fig, ax = plt.subplots(1)
	cl=np.array([-200,-20])
	ea = coord.easting; no = coord.northing;
	ax.imshow(bathy, cmap=plt.cm.jet, interpolation=None, aspect='auto', origin='upper', extent=[np.min(ea), np.max(ea), np.min(no), np.max(no)], vmin=cl[0], vmax=cl[1])	
	
	cm = plt.get_cmap("jet")
	for i in range(easting.shape[0]):
		convcol = 255*(bathymetry[i]-cl[0])/(cl[1]-cl[0]); col = cm(convcol.astype(int))
		ax.plot(easting[i], northing[i], color=col, marker='o',markeredgecolor='k');
	plt.show()
	"""	
	return BathymetryData

def data2array(points):
	#------------------------------------------------
	# Transform list of data into processed array
	#------------------------------------------------
	bathymetry = np.asarray(points.Bathymetry)	
	easting = np.asarray(points.Coordinates.easting); northing = np.asarray(points.Coordinates.northing)

	coordinates = np.zeros((bathymetry.shape[0],2))
	data = np.zeros(bathymetry.shape[0]);
	
	for i in range(easting.shape[0]):
		coordinates[i,0] = easting[i]; coordinates[i,1] = northing[i];
	
	
	return coordinates, bathymetry

def PointsList2Coordinates(points):
	#-----------------------------------------
	# Convert points list in Coordinates list
	#------------------------------------------
	
	easting, northing = [], []
	
	for point in points:
		easting.append(point.easting); northing.append(point.northing)
	
	easting = np.asarray(easting); northing = np.asarray(northing);		
	coordinates = CL.Coordinates(northing,easting)

	return coordinates

def ReadGtiffBathymetry(parameters):
	
	#-----------------------------------------
	#	READ EMODNET BATHYMETRY
	#-----------------------------------------

	# Read bathymetry (Gtiff format)
	coordinate, depth, _= IP.ReadSARImg(parameters)
	
	# process bathymetry
	# depth to bathymetry
	bathymetry = - depth
	# Land Mask	
	bathymetry[bathymetry>0]=np.nan

	# create vector coordinate (instead of )
	east = coordinate.easting[0,:]; north = coordinate.northing[:,0];
	coordinates = CL.Coordinates(north, east)
	
	return coordinates, bathymetry

def CollocatedData(Coordinates, coord, data):
	#-------------------------------------------------------------------------------------------------------------------
	#	ESTIMATE COLLOCATED COORDINATES AND data
	#	
	#	Remark: data (bathymetry/topography) domain should be bigger than image domain if grid points are different
	#--------------------------------------------------------------------------------------------------------------------	
	
	east = coord.easting; north = coord.northing; East = Coordinates.easting; North = Coordinates.northing;

	# check if image was flipped
	flagE = False; FlagN = False	
	if east[0] > east[-1]:
		flagE = True
	if north[0] > north[-1]:
		flagN = True

	# Image limit (Coordinate-wise, (W, E, S, N))
	W = np.min(East); E = np.max(East); S = np.min(North); N = np.max(North);

	# find nearest collocated coordinates
	iW = np.argmin(abs(W-east)); iE = np.argmin(abs(E-east));
	iS = np.argmin(abs(S-north)); iN = np.argmin(abs(N-north));

	# verify that bathymetry domain is bigger
	if east[iW] > W:
		if flagE:
			iW = iW + 1
		else:
			iW = iW - 1
	if east[iE] < E:
		if flagE:
			iE = iE - 1
		else:
			iE = iE + 1
	
	if north[iS] > S:
		if flagN:
			iS = iS + 1
		else: 
			iS = iS -1

	if north[iN] < N:
		if flagN:
			iN = iN - 1		
		else:
			iN = iN + 1
	
	# coordinates	
	easting = east[iW:iE+1]; northing = north[iN:iS+1];
	coordinates = CL.Coordinates(northing,easting)
	
	# bathymetry
	Data = data[iN:iS+1, iW:iE+1]	
	
	return coordinates, Data

def RemoveBathymetryException(parameters, Points, Bathymetry):
	#-------------------------------------------------------------------------------------------------------------------
	#
	#	Remove Grid points impacted with bathymetry exception 
	#
	#--------------------------------------------------------------------------------------------------------------------	
	
	#  remove NaN bathymetry values
	point, bathymetry, northing, easting = RemoveNanBathymetry(Points,Bathymetry)
	
	# remove land-sea interpolation artefacts
	#point, bathymetry, northing, easting = RemoveBathymetryAnomalies(parameters, point, bathymetry, northing, easting)

	
	coordinates = CL.Coordinates(northing, easting)	
	BathymetryData = CL.BathymetryData(coordinates, bathymetry)
	
	"""
	fig, ax = plt.subplots(1)
	for i in range(bathymetry.shape[0]):
		ax.plot(i, bathymetry[i],'or')
	"""		
	return point, BathymetryData
	

def SaveBathymetry(Bathymetry):
	#-----------------------------------------------------------
	#	Save bathymetry and grid points as array
	#-----------------------------------------------------------
	#read data	
	northing = Bathymetry.Coordinates.northing; easting = Bathymetry.Coordinates.easting;
	bathymetry = Bathymetry.Bathymetry
	
	# array initialization
	npt = northing.shape[0]
	data = np.zeros((npt,3))
	for i in range(npt):
		data[i,0] = easting[i]; data[i,1] = northing[i]; data[i,2] = bathymetry[i];

	# save array 	 	
	np.savez('bathymetry', x=data)


def RemoveBathymetryAnomalies(parameters, point, bathymetry, northing, easting):
	#-------------------------------------------------------------------------------------------------------------
	#	Remove grid points with nearshore bathymetry anomaly (in general the last point before the coastline)
	#-------------------------------------------------------------------------------------------------------------
	# determine processing properties according to Coast orientation
	CoastOrientation = parameters.MiscellaneousParameters.CoastOrientation
	FlagNorthing, FlagAscendingOrder = AnomalyRemovalParameters(CoastOrientation) 	
	
	"""
	# coast mainly facing West or East
	if not FlagNorthing:
		_, indices = np.unique(northing, return_index=True)
		indices = np.sort(indices); np.append(indices, northing.shape);
		for i in range(indices.shape[0]-1):
			
			
	# coast mainly facing North or South
	else: 
		E, indices = np.unique(easting, return_index=True)

	
	N, indices = np.unique(northing, return_index=True)
	print indices
	E, indices = np.unique(easting, return_index=True)
	print indices	
		
	indices = np.sort(indices); indices = np.append(indices, northing.shape)	
	
	
	fig, ax = plt.subplots(1)
	for i in range(indices.shape[0]-1):
		ax.plot(easting[indices[i]:indices[i+1]],bathymetry[indices[i]:indices[i+1]])						

	plt.show()	
	"""

	return point, bathymetry, northing, easting

def AnomalyRemovalParameters(CoastOrientation):
	#------------------------------------------------------------------------------
	#	parameters based on Coast Orientation that help to remove anomalies 
	#------------------------------------------------------------------------------
	if (CoastOrientation >= 225.) and (CoastOrientation <=315.):
		FlagNorthing = False; FlagAscendingOrder = True
	elif (CoastOrientation >= 45.) and (CoastOrientation <=135.):
		FlagNorthing = False; FlagAscendingOrder = False
	elif (CoastOrientation > 135.) and (CoastOrientation < 225.):
		FlagNorthing = True; FlagAscendingOrder = True
	else:
		FlagNorthing = True; FlagAscendingOrder = False

	return FlagNorthing, FlagAscendingOrder

def RemoveNanBathymetry(Points,Bathymetry):
	#------------------------------------------------------------------------------
	#	Remove Grid NaN bathymetry points
	#------------------------------------------------------------------------------
	point, bathymetry, easting, northing   = [], [], [], []	
	bathy = Bathymetry.Bathymetry; 
	east = Bathymetry.Coordinates.easting;  north = Bathymetry.Coordinates.northing;

	# remove NaN bathymetry values
	for i in range(Points.shape[0]):
		if (not np.isnan(bathy[i])):
			bathymetry.append(bathy[i]); point.append(Points[i])
			easting.append(east[i]); northing.append(north[i])
	
	# return arrays
	bathymetry=np.asarray(bathymetry); point = np.asarray(point); easting = np.asarray(easting); northing = np.asarray(northing);

	return point, bathymetry, northing, easting
