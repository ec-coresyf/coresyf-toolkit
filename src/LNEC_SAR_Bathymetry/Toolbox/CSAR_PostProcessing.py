#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os,sys, re
#
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cmplt
import matplotlib.colors as pltcl
#
import CSAR_Utilities as UT
import CSAR_Classes as CL
"""
===============================================================================
Post-Processing and Plot of simulation results  

===============================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2016
 Last update: July/2017
===============================================================================
	LABEL
		LabelToString		ImageLabel	
"""

def LabelToString(x_label, y_label,rdi):
	#------------------------------------------------
	# convert image label into strings
	#------------------------------------------------
	xlabel=[]
	for i in x_label:
		if rdi>0:
			xlabel.append(str(np.round(i,rdi)))
		else:
			xlabel.append(str(int(i)))

	ylabel=[]
	for i in y_label:
		if rdi>0:
			ylabel.append(str(np.round(i,rdi)))
		else:
			ylabel.append(str(int(i)))	
	
	return xlabel, ylabel


def ImageLabel(img,east, north,nbl,rdi) :
	#------------------------------------------------
	# create plot labels
	#------------------------------------------------	
	# nbl: nb of output label
	# rdi: rouding parameter
	
	# create ticks 
	indexeast = np.linspace(0,img.shape[1],nbl)
	indexnorth = np.linspace(0,img.shape[0],nbl)

	# create ticks label
	East_labels=np.linspace(east[0], east[-1],nbl)
	North_labels=np.linspace(north[0],north[-1],nbl)
	
	# create label
	xlabel, ylabel = LabelToString(East_labels, North_labels, rdi)
	
	return indexeast, indexnorth, xlabel, ylabel

def data2array(points, flag):
	#------------------------------------------------
	# Transform list of data into processed array
	#------------------------------------------------
	coordinates = np.zeros((points.shape[0],2))
	data = np.zeros(points.shape[0])
	
	i=0;

	for point in points:
		coordinates[i,0] = point.easting; coordinates[i,1] = point.northing;
		
		if flag == 'a_priori_bathymetry':		
			data[i] = point.apriori_bathymetry
		elif flag == 'bathymetry':
			data[i] = point.bathymetry
		elif flag == 'residual_bathymetry':
			data[i] = point.apriori_bathymetry - point.bathymetry
		elif flag == 'residual_bathymetry_percentage':
			data[i] = 100*(point.apriori_bathymetry - point.bathymetry) / point.apriori_bathymetry
		elif flag == 'wavelength':
			data[i] = point.wavelength
		elif flag == 'direction':
			data[i] = point.Spectrum.WaveDirection
		elif flag == 'distribution':
			data[i] = point.DiscriminationFlag
		elif flag == 'wave_period':
			data[i] = point.Tp
		i=i+1

	return coordinates, data

def MergeSpectrumData(points):
	#---------------------------------------------------
	# gather all 2D spectrum data in exploitable arrays
	#---------------------------------------------------
	# get array size
	k, Spectra, SpectraStd = [point.Spectrum.WaveSpectrum.k for point in points], [point.Spectrum.WaveSpectrum.Spectrum for point in points], \
				[point.Spectrum.WaveSpectrum.StandardDeviation for point in points]
	
	# store and save data	
	fname = os.getcwd()+'/Output/Bathymetry/WaveSpectrum.out'
	data = CL.SpectrumProcessedData(np.asarray(k),np.asarray(Spectra), np.asarray(SpectraStd))
	data.pickle(fname)
	
	
	return k, Spectra
#############################################
#	After-Computation Post-Processing
#############################################
def MergeData(ExceptionPoints, BathymetryPoints):
	#------------------------------------------------
	# Merge all processed data for post-processing
	#------------------------------------------------

	ProcessedPoints=[]

	#Deep water points
	if len(ExceptionPoints.DeepWaterPoints)>0:
		DWPoints=np.asarray(ExceptionPoints.DeepWaterPoints)
		for point in DWPoints:
			ProcessedPoints.append(point)

	#global grid points
	BathymetryPoints=np.asarray(BathymetryPoints)
	if len(BathymetryPoints)>0:
		for point in BathymetryPoints:
			ProcessedPoints.append(point)

	#shallow water points
	if len(ExceptionPoints.ShallowWaterPoints)>0:
		SWPoints=np.asarray(ExceptionPoints.ShallowWaterPoints)
		for point in SWPoints:
			ProcessedPoints.append(point)

	return ProcessedPoints

def DetectExceptionPoints(Points):
	#--------------------------------------------------------
	# Detect Points with anomaly in bathymetry (NaN)
	#--------------------------------------------------------
	NaNPoints = []

	for point in Points:
		if np.isnan(point.bathymetry):
			NaNPoints.append(point)
			
	return NaNPoints

################################################
# 	OUTPUT BATHYMETRY MAP CREATION 
################################################

def BathymetryMap(ProcessedPoints,OutputFile=None):
	
	#--------------------------------------------------------------------
	# Create bathymetry map (.txt and .tiff) file from Processed Points 
	#--------------------------------------------------------------------
		
	# sort points by coordinates
	Points = SortGridPoints(ProcessedPoints)

	# bathymetry text file
	BathymetryTextFile(Points,OutputFile)

	# bathymetry raster
	
def BathymetryTextFile(Points, OutputFile):
	#-------------------------------------------------------------------------
	# write bathymetry in a .txt file 
	# 		with: index, coordinates, direction, wavelength, bathy
	#-------------------------------------------------------------------------
	#path
	cwd = os.getcwd()
	path = cwd+'/Output/Bathymetry/'

	# output file name
	if OutputFile:	
		pattern=re.compile(".*(txt).*")
		filen = [m.group(0) for l in OutputFile for m in [pattern.search(l)] if m]
		filename = str(filen[0])
	else:
		filename='Bathymetry.txt'

	fname= path + filename	
	# write point information and bathy to file
	OutputFile=open(fname,"w")
	for n,point in enumerate(Points):
		OutputFile.write("%4d %16.3f %16.3f %10.3f %10.3f %10.3f %10.3f" % (n+1,point.easting, point.northing, point.Spectrum.WaveDirection, point.Tp, point.wavelength, point.bathymetry)+"\n")
	OutputFile.close()


def BathymetryRaster(Points,OutputFile):
	#-------------------------------------------------------------------------
	# write bathymetry in a georeferenced GeoTiff file
	#-------------------------------------------------------------------------
	#path
	cwd = os.getcwd()
	path = cwd+'/Output/Bathymetry/'

	# output file name
	if OutputFile:	
		pattern=re.compile(".*(tif).*")
		filen = [m.group(0) for l in OutputFile for m in [pattern.search(l)] if m]
		filename = str(filen[0])
	else:
		filename='Bathymetry.tif'

def SortGridPoints(ProcessedPoints):
	#-------------------------------------------------------------------------
	# sort grid points in geographical order (west to east, north to south)
	#-------------------------------------------------------------------------
	Points=[]
	npt = ProcessedPoints.shape[0]; 
	easting, northing = np.zeros(npt), np.zeros(npt)
	
	# create easting and northing vector
	for n, point in enumerate(ProcessedPoints):
		easting[n], northing[n] = point.easting, point.northing

	# sort the easting array in ascending order (west to east)
	Easting = np.unique(easting)
	for i, east in enumerate(Easting):
		ens = np.where( abs(easting-east) < 1 )
		ind = ens[0]
		Northing, indices = np.unique(northing[ind],return_index=True)
		for index in indices:
			pt = ProcessedPoints[ind[index]]
			Points.append(pt)
	Points = np.asarray(Points)
	
	return Points
"""
def array2raster(img, coordinates, EPSG, filein, fileout="ImgOut.tif"):
	#------------------------------------------------------------
	# convert 2D array into GDAL raster (GeoTiff)
	# 	General purpose: recreate raster after 
	#			- change in frame of reference
	#			- conserve the Projection system
	#------------------------------------------------------------
	# get input infos	
	_,Info = GetGtiffInformation(filein, EPSG)

	#process image
	img=ScaleImage(img,8)
	
	# get corner coordinates
	
	# coordinates
	easting = coordinates.easting; northing = coordinates.northing;

	# extrema
	xmin,ymin,xmax,ymax = [easting.min(),northing.min(),easting.max(),northing.max()]

	if len(img.shape)>2:
		nrows,ncols = np.shape(img[0,:,:])
	else:
		nrows,ncols = np.shape(img)
	# store dimension data
	Info.ncols = ncols; Info.nrows=nrows;
		
	#get the edges and recreate the corner coordinates for Geotransform raster properties
	xres = (xmax-xmin)/float(ncols); yres = (ymax-ymin)/float(nrows)
	geotransform = (xmin,xres,0,ymax,0, -yres); 

Info.Geotransform = geotransform;
	
	#create output raster
	CreateOutputGtiff(img, fileout, Info)
	
	return None
"""
	

#######################################
# 		FIGURES
#######################################

def PostProcessing(Points, data):
	
	#----------------------------------------------------------------
	# Plot bathymetries and wavelength map superimposed on the image 
	#----------------------------------------------------------------
	path = './Output/Results/'
	sz = (6,5)
	
	#------------
	# Image
	#------------
	image = data.image; 
	easting = data.coordinates.easting[0,:]; northing = data.coordinates.northing[:,0];
	
	# NaN Exception points
	NaNPoints = DetectExceptionPoints(Points)	

	# spectrum data for postprocessing (statistics)
	MergeSpectrumData(Points)

	#*********************************
	# Image et points discrimination
	#*********************************
	#############################################################
	## Commented by STeam
	"""

	cl = np.array([-1, 1]); 
	cm = plt.get_cmap("jet")

	fig1, ax = plt.subplots(1, figsize=sz)
	#image
	#ax.imshow(image)
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])
	
	# a priori bathymetry
	coordinates, discriminationflag = data2array(Points,'distribution');
	ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=discriminationflag , cmap=cm, vmin=cl[0], vmax=cl[1])

	# exception NaN Points
	if NaNPoints:
		for point in NaNPoints:
			ax.plot(point.easting, point.northing,'ok',markersize=8)	

	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")	
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title('Point distribution (deep, quasi-deep, intermediate or shallow water)')
	#save figure
	filename = path + 'GridPointDistribution.png'
	plt.savefig(filename, dpi='figure')

	#******************************
	# Image et a priori bathymetry
	#******************************
	cl = np.array([-200, 0]); 
	cm = plt.get_cmap("jet")

	fig1, ax = plt.subplots(1, figsize=sz)
	#image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])
	
	# a priori bathymetry
	coordinates, apriori_bathymetry = data2array(Points,'a_priori_bathymetry');
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=apriori_bathymetry, cmap=cm, vmin=cl[0], vmax=cl[1])	
	plt.colorbar(cax)
	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")	
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title('a priori bathymetry (m)')
	#save figure
	filename = path + 'aprioriBathymetry.png'
	plt.savefig(filename, dpi='figure')	

	#********************************
	# Image et estimated bathymetry
	#********************************
	fig2, ax = plt.subplots(1, figsize=sz)

	# image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])
	
	# bathymetry	
	coordinates, bathymetry = data2array(Points,'bathymetry');
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=bathymetry, cmap=cm, vmin=cl[0], vmax=cl[1])	
	plt.colorbar(cax)

	# exception NaN Points
	if NaNPoints:
		for point in NaNPoints:
			ax.plot(point.easting, point.northing,'ok',markersize=8)
	

	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title('Estimated bathymetry (m)')
	#save figure	
	filename = path + 'Bathymetry.png'
	plt.savefig(filename, dpi='figure')

	#********************************
	# Image et residual bathymetry
	#********************************

	fig3, ax = plt.subplots(1, figsize=sz)

	# image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])

	# residual bathymetry
	coordinates, residual = data2array(Points,'residual_bathymetry');
	#cl = np.array([np.min(residual), np.max(residual)]); 
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=residual, cmap=cm, vmin=-50, vmax=50)		
	plt.colorbar(cax)
	# exception NaN Points
	if NaNPoints:
		for point in NaNPoints:
			ax.plot(point.easting, point.northing,'ok',markersize=8)

	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title('Residual (m)')
	#save figure	
	filename = path + 'Residual.png'
	plt.savefig(filename, dpi='figure')


	#********************************
	# Image et residual bathymetry
	#********************************

	fig4, ax = plt.subplots(1, figsize=sz)

	# image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])

	# residual bathymetry
	coordinates, residual = data2array(Points,'residual_bathymetry_percentage');
	#cl = np.array([np.min(residual), np.max(residual)]); 
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=residual, cmap=cm, vmin=-100, vmax=100)		
	plt.colorbar(cax)
	# exception NaN Points
	if NaNPoints:
		for point in NaNPoints:
			ax.plot(point.easting, point.northing,'ok',markersize=8)

	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title("Residual (%)")
	#save figure	
	filename = path + 'Residual_percentage.png'
	plt.savefig(filename, dpi='figure')
	
	#********************************
	# Image and wavelength 
	#********************************
	
	cl = np.array([250, 400]); 
	cm = plt.get_cmap("cool");

	fig5, ax = plt.subplots(1, figsize=sz)
	#image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])
	
	# wavelength and direction
	coordinates, wavelength = data2array(Points,'wavelength');	
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='.', c=wavelength, cmap=cm, alpha = 1, vmin=cl[0], vmax=cl[1])
	
	# directional arrows	
	coordinates, direction = data2array(Points,'direction');
	direction = (180+UT.CartesianNautical(direction))*np.pi/180
	convcol = 255*(wavelength-cl[0])/(cl[1]-cl[0]); col = cm(convcol.astype(int))
	Q = ax.quiver(coordinates[:,0], coordinates[:,1], np.cos(direction), np.sin(direction), color=col, scale=20)

	plt.colorbar(cax)
	plt.title('Directions and wavelengths')
	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	#save figure	
	filename = path + 'WavelengthDirection.png'
	plt.savefig(filename, dpi='figure')	
	

	#********************************
	# Image et wave period
	#********************************

	fig4, ax = plt.subplots(1, figsize=sz)

	# image
	ax.imshow(image, cmap=plt.cm.gray, interpolation=None, aspect='auto', origin='upper', extent=[np.min(easting), np.max(easting), np.min(northing), np.max(northing)])

	# residual bathymetry
	coordinates, residual = data2array(Points,'wave_period');
	#cl = np.array([np.min(residual), np.max(residual)]); 
	cax = ax.scatter(coordinates[:,0], coordinates[:,1], marker='o', c=residual, cmap=cm, vmin=14, vmax=18)		
	plt.colorbar(cax)
	# exception NaN Points
	if NaNPoints:
		for point in NaNPoints:
			ax.plot(point.easting, point.northing,'ok',markersize=8)

	ax.set_xlabel("Easting (m)")
	ax.set_ylabel("Northing (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	plt.title("Wave period Tp (s)")
	#save figure	
	filename = path + 'Tp.png'
	plt.savefig(filename, dpi='figure')
	
	#############################################################
	## Commented by STeam
	"""


	"""
	#***************************
	# Depth vs wavelength 
	#***************************
	fig5, ax = plt.subplots(1)
	ax.plot(-apriori_bathymetry, wavelength,'sr')
	ax.plot(-bathymetry, wavelength,'ob')
	ax.set_xlabel("depth (m)")
	ax.set_ylabel("wavelength (m)")
	ax.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	"""

	#plt.show()

#############################################
#	Spectra and Subsets at grid points
#############################################
def Plot_Subset_Spectrum(index,Spectrum, MeanSpectrum):
	#-------------------------------------------------------
	# Plot various Subsets and Spectra for each grid points 
	#-------------------------------------------------------

	#****************************************
	# Subsets and Directions
	#****************************************
	Plot_subscenes(index,Spectrum.WaveDirection, 'Subsets', Spectrum.SubsetData)
	#****************************************
	# Spectra and Directions
	#****************************************
	Plot_subscenes(index, Spectrum.WaveDirection, 'Spectra', Spectrum.ImageSpectrum)
	#**************************
	# Plot Main Spectrum
	#**************************	
	Plot_spectrum(index, MeanSpectrum)

def Plot_spectrum(index, Spectrum):
	#-------------------------------------------------------
	# Plot mean spectrum and associated standard deviation 
	#-------------------------------------------------------
	# read data
	WaveSpectrum = Spectrum.WaveSpectrum
	k, spectrum, Std, kp = WaveSpectrum.k, WaveSpectrum.Spectrum, WaveSpectrum.StandardDeviation, 2*np.pi/WaveSpectrum.Wavelength
	indp = np.argmin(abs(kp-k))
	# figure
	sz=(8,5)
	fig, ax = plt.subplots(1, figsize=sz)
	#spectrum	
	ax.plot(k,spectrum)

	#standard deviation	
	ax.fill_between(k, spectrum-Std, spectrum+Std, where=spectrum+Std>=spectrum-Std, Facecolor=(0.9,0.2,0.2,0.4), interpolate=True)
	
	#peak wave number 
	ax.axvline(k[indp], linestyle='--', c='0.75', ymin=0, ymax=spectrum[indp])

	ax.set_xlabel("k (rad/m)"); ax.set_ylabel("Spectra Amplitude"); ax.set_xlim([0,0.15])
	
	# save figure
	path = './Output/SubsetSpectra/'
	filename = path + 'WaveSpectrum' + str(index) + '.png'
	plt.savefig(filename, dpi='figure')
	plt.close()

def Plot_subscenes(index, Directions,Param, data):
	#-------------------------------------------------------
	# Create Sub-scene plots 
	#-------------------------------------------------------

	fig, ((ax1, ax2, ax3), (ax4, ax5, ax6), (ax7, ax8, ax9)) = plt.subplots(nrows = 3, ncols = 3, figsize=(8, 8))
	

	
	#global parameters
	r, alpha,Sc = 1, 0, 5.0
	fac = np.pi*1/180;
	MeanDirection, StdDirection, BoxNb = np.mean(Directions), np.std(Directions), len(Directions)
	Aspect = 'equal'
	
	if Param == 'Subsets':
		xlab, ylab = "Easting (m)", "Northing (m)";
		cma = plt.cm.gray;
	elif Param == 'Spectra':
		xlab, ylab = "k (rad/m)", "k (rad/m)"; 
		xl = [-0.05, 0.05]; cma = plt.cm.jet;
		FlagDecibel = False

	#************
	# subplot 1
	#************
	#preprocessing
	if Param == 'Subsets':
		Image, x, y = data[0].image, data[0].coordinates.easting, data[0].coordinates.northing
	elif Param == 'Spectra':
		Image, x, y  = data[0].Spectrum, data[0].k, data[0].k
		if FlagDecibel:
			Image = 20*np.log(Image) 
	direction = (180+UT.CartesianNautical(Directions[0]))*fac;
	xm, ym = np.mean(x), np.mean(y)	
	limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
	
	#plot	
	#image	
	ax1.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
	#direction
	xr = r*np.cos(direction); yr = r*np.sin(direction)
	ax1.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
	ax1.set_ylabel(ylab);
	
	if BoxNb == 5:
		ax1.set_xlabel(xlab); 
	else:
		ax1.tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off') 
	if Param=='Spectra':
		ax1.set_xlim(xl); ax1.set_ylim(xl);
	ax1.ticklabel_format(axis='y', style='sci', scilimits=(0,1))

	#************
	# subplot 2
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[1].image, data[1].coordinates.easting, data[1].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[1].Spectrum, data[1].k, data[1].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
	
		direction = (180+UT.CartesianNautical(Directions[1]))*fac;
		xm, ym = np.mean(x), np.mean(y)	
		limit = [np.min(x), np.max(x), np.min(y), np.max(y)]

		#plot
		#image
		ax2.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
		#direction
		xr = r*np.cos(direction); yr = r*np.sin(direction)
		ax2.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
		ax2.tick_params(axis='both', which='both', bottom='off', top='off',left='off', labelbottom='off', labeltop='off', labelleft='off', labelright='off') 	
 	else:
		ax2.axis('off')
	if Param=='Spectra':
		ax2.set_xlim(xl); ax2.set_ylim(xl);

	#************
	# subplot 3
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[2].image, data[2].coordinates.easting, data[2].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[2].Spectrum, data[2].k, data[2].k
			if FlagDecibel:
				Image = 20*np.log(Image) 	
		direction = (180+UT.CartesianNautical(Directions[2]))*fac;
		ax3.tick_params(axis='both', which='both', bottom='off', top='off',left='off', labelbottom='off', labeltop='off', labelleft='off', labelright='off') 
	else:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[1].image, data[1].coordinates.easting, data[1].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[1].Spectrum, data[1].k, data[1].k
			if FlagDecibel:
				Image = 20*np.log(Image) 

		ax3.set_ylabel(ylab); ax3.set_xlabel(xlab)
		ax3.ticklabel_format(axis='both', style='sci', scilimits=(0,1))	
		direction = (180+UT.CartesianNautical(Directions[1]))*fac;

	xm, ym = np.mean(x), np.mean(y)	
	limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
	
	#plot	
	#image
	ax3.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
	#direction
	xr = r*np.cos(direction); yr = r*np.sin(direction)	
	ax3.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
	if Param=='Spectra':	
		ax3.set_xlim(xl); ax3.set_ylim(xl);
	
	
	#************	
	# subplot 4
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[3].image, data[3].coordinates.easting, data[3].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[3].Spectrum, data[3].k, data[3].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
	
		direction = (180+UT.CartesianNautical(Directions[3]))*fac;
		xm, ym = np.mean(x), np.mean(y)	
		limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
		#plot
		#image
		ax4.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
		#direction
		xr = r*np.cos(direction); yr = r*np.sin(direction)
		ax4.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
		ax4.ticklabel_format(axis='y', style='sci', scilimits=(0,1)) 
		ax4.tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off', labeltop='off') 
	else:
		ax4.axis('off')
	if Param=='Spectra':
		ax4.set_xlim(xl); ax4.set_ylim(xl);
	ax4.set_ylabel(ylab);
	if BoxNb == 5:
		ax4.set_xlabel(xlab)

	#**************************
	# subplot 5: mean plot
	#**************************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[4].image, data[4].coordinates.easting, data[4].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[4].Spectrum, data[4].k, data[4].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[4]))*fac;
 		ax5.tick_params(axis='both', which='both', bottom='off', top='off',left='off', labelbottom='off', labeltop='off', labelleft='off', labelright='off') 
	else:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[2].image, data[2].coordinates.easting, data[2].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[2].Spectrum, data[2].k, data[2].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[2]))*fac;
		ax5.set_ylabel(ylab); ax5.set_xlabel(xlab)
		ax5.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	xm, ym = np.mean(x), np.mean(y)	
	limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
	#mean direction and standard deviation
	xr = r*np.cos(direction); yr = r*np.sin(direction)
	directionmean = (180+UT.CartesianNautical(MeanDirection))*fac; xrm = r*np.cos(directionmean); yrm = r*np.sin(directionmean);
	directionmin = (180+UT.CartesianNautical(MeanDirection-StdDirection))*fac; xrmin = r*np.cos(directionmin); yrmin = r*np.sin(directionmin);
	directionmax = (180+UT.CartesianNautical(MeanDirection+StdDirection))*fac; xrmax = r*np.cos(directionmax); yrmax = r*np.sin(directionmax);
	#plot
	#image
	ax5.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
	#directions	
	#ax5.quiver(xm+alpha, ym-alpha, xrmin, yrmin, color='w', scale=Sc);
	#ax5.quiver(xm+alpha, ym-alpha, xrmax, yrmax, color='w', scale=Sc);
	ax5.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
	ax5.quiver(xm+alpha, ym-alpha, xrm, yrm, color='w', scale=Sc);
	if Param == 'Spectra':
		ax5.set_xlim(xl); ax5.set_ylim(xl);
	

	#************
	# subplot 6
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[5].image, data[5].coordinates.easting, data[5].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[5].Spectrum, data[5].k, data[5].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[5]))*fac;
		xm, ym = np.mean(x), np.mean(y)	
		limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
		#plot
		#image
		ax6.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
		#direction
		xr = r*np.cos(direction); yr = r*np.sin(direction)
		ax6.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
		ax6.tick_params(axis='both', which='both', bottom='off', top='off',left='off', labelbottom='off', labeltop='off', labelleft='off', labelright='off') 
	else:
		ax6.axis('off')
	if Param == 'Spectra':
		ax6.set_xlim(xl); ax6.set_ylim(xl);
	
	#************	
	# subplot 7
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[6].image, data[6].coordinates.easting, data[6].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[6].Spectrum, data[6].k, data[6].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[6]))*fac; 
	else:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[3].image, data[3].coordinates.easting, data[3].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[3].Spectrum, data[3].k, data[3].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[3]))*fac;	
	xm, ym = np.mean(x), np.mean(y)	
	limit = [np.min(x), np.max(x), np.min(y), np.max(y)]	
	#plot
	#image
	ax7.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
	#direction	
	xr = r*np.cos(direction); yr = r*np.sin(direction)
	ax7.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
	if Param == 'Spectra':	
		ax7.set_xlim(xl); ax7.set_ylim(xl);
	ax7.set_xlabel(xlab); ax7.set_ylabel(ylab); ax7.ticklabel_format(axis='both', style='sci', scilimits=(0,1))

	#************	
	# subplot 8
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[7].image, data[7].coordinates.easting, data[7].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[7].Spectrum, data[7].k, data[7].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[7]))*fac;
		xm, ym = np.mean(x), np.mean(y)	
		limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
		#plot
		#image		
		ax8.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
		#direction
		xr = r*np.cos(direction); yr = r*np.sin(direction)
		ax8.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
		ax8.ticklabel_format(axis='x', style='sci', scilimits=(0,1))
		ax8.tick_params(axis='y', which='both', right='off', left='off', top='off', labelleft='off',labelright='off',labeltop='off')
	else:
		ax8.axis('off')
	if Param == 'Spectra':
		ax8.set_xlim(xl); ax8.set_ylim(xl);
	ax8.set_xlabel(xlab); 
	
	#************	
	# subplot 9   
	#************
	if BoxNb == 9:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[8].image, data[8].coordinates.easting, data[8].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[8].Spectrum, data[8].k, data[8].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[8]))*fac;
		ax9.ticklabel_format(axis='x', style='sci', scilimits=(0,1))
		ax9.tick_params(axis='y', which='both', right='off', left='off', top='off', labelleft='off',labelright='off',labeltop='off')
	else:
		#preprocessing
		if Param == 'Subsets':
			Image, x, y = data[4].image, data[4].coordinates.easting, data[4].coordinates.northing
		elif Param == 'Spectra':
			Image, x, y  = data[4].Spectrum, data[4].k, data[4].k
			if FlagDecibel:
				Image = 20*np.log(Image) 
		direction = (180+UT.CartesianNautical(Directions[4]))*fac;
		ax9.ticklabel_format(axis='both', style='sci', scilimits=(0,1))
	xm, ym = np.mean(x), np.mean(y)	
	limit = [np.min(x), np.max(x), np.min(y), np.max(y)]
	#plot
	#image
	ax9.imshow(Image, cmap=cma, interpolation=None, aspect=Aspect, origin='upper', extent=limit)
	#direction
	xr = r*np.cos(direction); yr = r*np.sin(direction)	
	ax9.quiver(xm+alpha, ym-alpha, xr, yr, color='r', scale=Sc);
	if Param == 'Spectra':
		ax9.set_xlim(xl); ax9.set_ylim(xl);
	ax9.set_xlabel(xlab); 
	if BoxNb == 5:
		ax9.set_ylabel(ylab)
	
	#************************
	#	save figure
	#************************
	path = './Output/SubsetSpectra/'
	filename = path + Param + str(index) + '.png'
	plt.savefig(filename, dpi='figure')
	plt.close()
