#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


"""
=====================================================================================================
Compute/estimate  Spectrum-Related distribution and parameters
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho
 Date: May/2017
 Last update: Nov/2017
=====================================================================================================
	DIRECTION ESTIMATE:		DirectionEstimate	MaskPlot	DirectionalProjection
	IMAGE SPECTRUM:			SpectrumRange	ImageSpectrum
	WAVE SERIES SPECTRA:		SubsetSpectrum	WavesMeanSpectrum
	RADIAL PROJECTION SPECTRUM:	RadialSpectrum RadialProjection
	FILTERS
					ButterworthEllipticFilter	ImageFilter
					imfft		imifft
	UTILITIES			Spectrum1D	DefineLine	FindOffsetPoints	dx	dy
					DetectLineEdge	Powerof2	resolutionpadding
					zerospadding	Distance4Line
"""
#
import re
#
import numpy as np
import matplotlib.pyplot as plt
#
#
import argparse
import ConfigParser
from datetime import datetime
#
import cv2
#
from scipy.optimize import minimize
from scipy import misc
from scipy.cluster.vq import kmeans2

#
from sklearn.cluster import KMeans
from sklearn.utils import shuffle
#
from skimage.measure import profile_line
#
import CSAR_Classes as CL
import CSAR_Utilities as UT
import CSAR_ImageProcessing as IP
#


###########################################################
#
#	    IMAGE SPECTRUM PROCESSING
#
###########################################################
#******************************************************
#	   INPUT Parameters
#******************************************************
def InputSpectrumParameters():
	#-----------------------------------------------
	# Image Processing input parameters
	#-----------------------------------------------
	# input output
	parser = argparse.ArgumentParser(description='Co-ReSyF: SAR Bathymetry Research Application')

	# input/ output files
	parser.add_argument('-a', '--param', help='Parameters file for Wings (.ini file)', default = 'Config_Spectrum.ini',required=False)
	parser.add_argument('-i', '--input', help='Input subset files (subsets#.out) for Spectrum and wavelength estimation', required=True)
	parser.add_argument('-o', '--output', help='Output transfer file (spectrum#.out)', required=False)

	# parameters for direction estimate
	parser.add_argument('-c', '--coast_orientation', help='Coast normal orientation (nautical convention ex: 270-> West facing)', default=270, required=False)

	# filter parameters
	parser.add_argument('-f', '--filter', help='Flag whether to filter subscenes. Filter type: ellipsoidd Butterworth Filter', default = True,required=False)

	#spectrum parameters
	parser.add_argument('-m', '--method', help='method for spectrum estimate: derived from wave series (subscene) or from radial projection of the subscene spectrum', required=True)
	parser.add_argument('-p', '--number_of_profiles', help='number of wave profiles derived required to estimate spectrum', default = 5, required=False)
	parser.add_argument('-d', '--offset_profiles', help='offset (m) in between wave profiles', default = 50, required=False)

	#comments
	parser.add_argument('-v','--verbose', help="comments and screen outputs", action="store_true")

	#store
	args = parser.parse_args()
	RunId = datetime.now().strftime('%Y%m%dT%H%M%S')

	#create config.ini file
	parOut = open(args.param, "w"); Config = ConfigParser.ConfigParser(); Config.add_section("Arguments")

	#input/output
	Config.set("Arguments", "Input_file", args.input);
	Config.set("Arguments", "Output_file", args.output);

	#spectrum parameters
	Config.set("Arguments", "Coast_Orientation", args.coast_orientation);
	Config.set("Arguments", "Filter_Flag", args.filter)
	Config.set("Arguments", "Spectrum_method", args.method);
	if args.method == 'Waves':
		Config.set("Arguments", "Number_of_profiles", args.number_of_profiles)
		Config.set("Arguments", "Offset_inbetween_profiles", args.offset_profiles)

	Config.add_section("Run")
	Config.set("Run", "Id", RunId)

	Config.write(parOut); parOut.close()

	# store parameters in classes
	# subset processing
	IP_Parameters = CL.SubsetProcessingParameters()
	# direction estimate
	DP_Parameters =  CL.DirectionEstimateParameters(float(args.coast_orientation))
	# Image Filter
	IF_Parameters = CL.FilterParameters(args.filter)
	# Spectra parameters
	WavesSpectrumParameters = CL.WaveSpectrumParameters(args.method, int(float(args.number_of_profiles)), float(args.offset_profiles)) if args.method == 'Waves' \
		else CL.WaveSpectrumParameters(args.method)

	# wavelength determination parameters (default)
	WavelengthEstimateParameters = CL.WavelengthEstimationParameters()
	# global wave spectrum and wavelength parameters
	SP_Parameters =	CL.SpectrumParameters(WavesSpectrumParameters, WavelengthEstimateParameters)
	# global parameters list
	parameters = CL.ComputingParametersSpectrum(IP_Parameters, DP_Parameters, IF_Parameters, SP_Parameters)

	return parameters, args

#******************************************************
#	    DIRECTION ESTIMATE
#******************************************************
def DirectionEstimate(parameters, subset, spectrum):
	#-------------------------------------------------------------------
	# Estimate main wave direction from image (radon) or image spectrum
	#-------------------------------------------------------------------

	direction = Direction_distribution(parameters, subset, spectrum)

	return direction


def Direction_distribution(parameters, subset, spectrum):
	#----------------------------------------------------------------------
	# estimate incident wave direction using projection in direction bins
	#----------------------------------------------------------------------
	# data
	Spectrum = spectrum.Spectrum
	k = spectrum.k

	# determine radius of influence
	Radius, Rm, R20 = Influence_Radius(spectrum)

	# create circular mask on data not to account for noise (which can biais directions)
	Spectrum = spectrum.Spectrum

	if parameters.masktype == 'circular':
		mask = MaskPlot(Radius, subset)
	elif parameters.masktype == 'disk':
		mask1, mask2 = MaskPlot(np.min(R20), subset), MaskPlot(np.max(R20), subset)
		dim = mask1.shape
		index = mask1.ravel() != mask2.ravel()
		mask = np.ones(mask1.shape, dtype=bool).ravel(); mask[index]=False;
		mask = np.reshape(mask, dim)
	Spectrum[mask] = 0

	#perform Directionnal Integration within the circle (cartesian reference)
	theta, distribution = DirectionalIntegration(Spectrum)

	#determine peak (main) direction
	Directions = DirectionPeak(parameters, theta, distribution, subset.FlagFlip)

	# direction in the nautical frame of reference
	Directions = UT.CartesianNautical(np.mod(360-Directions,360)) if subset.FlagFlip else UT.CartesianNautical(Directions)

	#solve 180-ambiguity
	direction = Direction180Ambiguity(Directions, parameters)

	#-------------------------
	#	 Figure
	#-------------------------
	flagplot = 0

	if flagplot>0:

		#parameters
		klimit = 0.05
		xl = [-klimit, klimit];
		k = spectrum.k; fac = np.pi/180; r = np.linspace(0,np.max(k),100)
		Spectrum[mask] = np.nan;

		#figure
		fig, ax = plt.subplots(nrows=1)
		# spectrum
		ax.imshow(Spectrum,cmap=plt.cm.jet, origin='upper', extent = [np.min(k), np.max(k), np.min(k), np.max(k)])
		directionplot = UT.CartesianNautical(direction)*fac; xr = r*np.cos(directionplot); yr = r*np.sin(directionplot)
		ax.plot(xr,yr,'r')
		ax.set_xlabel("Kx (rad/m)"); ax.set_ylabel("Ky (rad/m)");
		ax.set_xlim(xl); ax.set_ylim(xl);
		plt.show()

	return direction

#?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*
# direction (projection): bin method
#*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?
def DirectionalIntegration(spectrum):
    	"""
    	Estimate swell direction by spectrum directionnal integration.
    	remark: Radial Spectrum mask required
   	"""
	# image phase
	theta = ImagePhase(spectrum)

	# sort the directions (crescent)
   	ind = np.argsort(theta.flat)

   	theta_sorted = theta.flat[ind] # sorted radius
   	spectrum_sorted = spectrum.flat[ind] # sorted image pixels (same order)

   	# theta is integer (bin wise)
	theta_int = np.round(theta_sorted)

	"""
	fig, ((ax1,ax2), (ax3,ax4), (ax5,ax6)) = plt.subplots(3,2)
	ax1.imshow(theta)
	ax2.plot(spectrum.flat)
	ax3.plot(theta_sorted)
	ax4.plot(spectrum_sorted)
	ax5.imshow(spectrum)
	ax6.plot(theta_sorted, spectrum_sorted)
	plt.show()
	"""

	# unique r decomposition, indi reflect the direction bin
	thetau, ind, indi, count = np.unique(theta_int,return_index=True, return_inverse=True, return_counts=True)
 	csim = np.cumsum(spectrum_sorted, dtype=float)

	#verification number of non-zeros bins per direction
	countbin = np.zeros((thetau.shape[0]))
	for i in range(thetau.shape[0]):
		if i==1:
			tmp = spectrum_sorted[0:ind[1]-1]
		elif i == thetau.shape[0]-1:
			tmp = spectrum_sorted[ind[i]:-1]
		else:
			tmp = spectrum_sorted[ind[i]:ind[i+1]-1]

		countbin[i] = np.count_nonzero(tmp)

	# sum all the magnitude/imtensity of pixel with same direction
	tbin = np.zeros((thetau.shape[0]))
	tbin[:-1] = csim[ind[1:]-1]-csim[ind[:-1]]
	tbin[0] = csim[ind[1]]
	tbin[-1] = csim[-1]-csim[ind[-1]]

	# normalize by the number of pixel with same radius
	distribution = np.zeros((thetau.shape[0]))
	distribution[countbin>0] = tbin[countbin>0]/countbin[countbin>0]

	#figure: directional bin distribution
	flagplot = 0
	if flagplot>0:
		fig, (ax1, ax2, ax3) = plt.subplots(3)
		ax1.imshow(theta)
		ax2.imshow(spectrum)
		ax3.plot(thetau, distribution,'o')
		ax3.set_xlabel("Direction (deg)")
		ax3.set_ylabel("Intensity")
		plt.show()


	return thetau, distribution

def DirectionPeak(parameters, theta, distribution, Flag):
	#--------------------------------------------------------------------------
	# Determine peak direction depending on fitting or centroid/cluster method
	#--------------------------------------------------------------------------

	Directions = Direction_PeakDetection(parameters, theta, distribution, Flag)

	return Directions


def  Direction_PeakDetection(parameters, theta, distribution, Flag):

	#------------------------------------
	#	peak detection
	#------------------------------------
	# domain dichotomy
	angle = 360-UT.CartesianNautical(parameters.CoastNormalOrientation) if Flag else UT.CartesianNautical(parameters.CoastNormalOrientation)

	theta1, distribution1, theta2, distribution2 = DirectionDichotomy(theta, distribution, angle)

	Directions = np.zeros(2)
	# parameter for peak detection
	ratio = 20./100
	if parameters.submethod in {'clusterpower', 'ClusterPower', 'centroidpower','CentroidPower'}:
		power = 2
	else:
		power = 1

	PeakParameters = CL.PeakParameters(power,ratio)
	# data for peak detection
	DataDirection1 = CL.DataPeak(theta1, distribution1); DataDirection2 = CL.DataPeak(theta2, distribution2);

	# estimate mean direction
	Directions[0] = UT.PeakDetection(PeakParameters, parameters.submethod, DataDirection1)
	Directions[1] = UT.PeakDetection(PeakParameters, parameters.submethod, DataDirection2)

	flagplot=0
	if flagplot>0:
		fig, ax1 = plt.subplots(1)
		ax1.plot(theta1,distribution1,'o')
		ax1.plot(theta2,distribution2,'o')
		ax1.axvline(x=Directions[0]), ax1.axvline(x=Directions[1])
		ax1.axhline(y=ratio*np.max(distribution1)), ax1.axhline(y=ratio*np.max(distribution2))
	plt.show()

	return Directions




#?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?
# 	utilities
#*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*?*
def DirectionDichotomy(theta,distribution, angle):
	#------------------------------------
	# decompose directional domain into 2 domains according to coast orientation
	#------------------------------------
	# coast normal orientation (cartesian)
	#angle = UT.CartesianNautical(angle)

	#angular domain dichotomy
	angle1 = np.min([np.mod(angle - 90, 360), np.mod(angle + 90, 360)])
	angle2 = np.max([np.mod(angle - 90, 360), np.mod(angle + 90, 360)])

	# first domain
	theta1  = theta[(theta>=angle1) & (theta<=angle2)]
	distribution1 = distribution[(theta>=angle1) & (theta<=angle2)]

	# second domain
	theta2 = np.concatenate((theta[theta>=angle2], theta[theta<=angle1]+360),axis=0);
	distribution2 = np.concatenate((distribution[theta>=angle2], distribution[theta<=angle1]), axis=0)
	theta2, indices = np.unique(theta2, return_index=True); distribution2 = distribution2[indices];

	return theta1, distribution1, theta2, distribution2

def Influence_Radius(spectrum):
	#------------------------------------------------------------------
	# determine radius within which spectrum energy if concentrated
	#------------------------------------------------------------------
	# radial projection
	#print '1'
	R, RadialIntegration = RadialProjection(spectrum.Spectrum)
	#print '2'
	# corresponding wavenumber
	dk = np.sum(np.diff(spectrum.k))/(spectrum.k.shape[0]-1)
	kr = R*dk
	#print '3'
	#Radius with maximum energy
	Rm = 2*np.pi/kr[np.argmax(RadialIntegration)]

	# Radius with energy >20% of the maximum
	#print '4'
	thr = 20./100*np.max(RadialIntegration)
	index = np.where((RadialIntegration-thr)>0)
	R20 = np.array([np.round((2*np.pi/kr[index[0][0]])/10)*10, np.floor((2*np.pi/kr[index[0][-1]])/10)*10])
	#print '5'
	# radius including all spectrum energy
	# Detect crossing with 5 % of the maximum
	thr = 5./100*np.max(RadialIntegration)
	index = np.where((RadialIntegration-thr)>0)
	Radius = np.floor((2*np.pi/kr[index[0][-1]])/10)*10
	#print '6'
	return Radius, Rm, R20

def Direction180Ambiguity(Directions, parameters):
	#--------------------------------------------------------------------------
	# estimate incident wave direction by resolving 180-ambiguity
	#--------------------------------------------------------------------------
	# determine incident wave direction accounting for the 180-ambiguity to have a smoothed direction
	direction = 0.5*(np.min(Directions)+np.mod(np.max(Directions)+180,360))

	# withdraw 180-ambiguity accounting for coast orientation
	angle = parameters.CoastNormalOrientation
	D = np.array([direction, direction+180]); index = np.argmin(abs(D-angle));
	direction = D[index]

	return direction

def MaskPlot(radius, subset):
	"""
	create a mask for spectrum plot
	"""
	# estimate the location of the center of the image
	image = subset.image
	center = IP.ImageCenter(image)

	# create grid (same dimension as image)
	nx , ny = image.shape
	x = np.linspace(0, nx-1, nx) - round(center[0])
	y = np.linspace(0, ny-1, ny) - round(center[1])
	X,Y = np.meshgrid(x,y)

	# define cut off threshold
	Kmax = 2 * np.pi/radius
	Kres = 2 * np.pi / subset.resolution[1] / image.shape[1]
	thr = np.round(Kmax/Kres)

	#create polar mask
	mask = np.sqrt((X**2) + (Y**2))>thr
	mask = np.transpose(mask)

	return mask

def ImagePhase(img):
    	"""
    	Compute image phase (directions)
   	"""
	# indices of image center
	center = IP.ImageCenter(img)

	# image indices
   	y, x = np.indices(img.shape)

	# phase
   	theta = cv2.phase(np.float32(x - center[0]), np.float32(y - center[1]))

	#transform radian to degree
	theta = theta*180/np.pi

	return theta


#******************************************************
#	    IMAGE SPECTRUM
#******************************************************


def SpectrumRange(magnitude, kx, ky, SPthr) :

	# nbl: nb of output label
	# rdi: rouding parameter

	margin = 10
	# estimate image center
	center = IP.ImageCenter(magnitude)

	# zoom definition
	zoomx = np.array([center[0]-(SPthr+margin), center[0]+(SPthr+margin)])
	zoomy = np.array([center[1]-(SPthr+margin), center[1]+(SPthr+margin)])

	# zoomm in kx, ky
	Kx = np.max(kx[np.int_(zoomx[0]):np.int_(zoomx[1])])
	Ky = np.max(ky[np.int_(zoomy[0]):np.int_(zoomy[1])])
	kr = np.max([abs(Kx),abs(Ky)])

	return kr


def ImageSpectrum(parameters, subset):
	#----------------------------------------------
	# Compute Image Spectrum or Power Spectrum
	#----------------------------------------------
	image = subset.image 						# given subset image
	if parameters.MeanSubstractionFlag:
		image = image - np.mean(image)					# substract mean value
	Spectrum = imfft(image)   					# FFT of the given image
	mag = cv2.magnitude(Spectrum[:,:,0],Spectrum[:,:,1])
	if parameters.DecibelRepresentationFlag:
		mag = 20*np.log(mag)	# amplitude spectrum (sqrt(Im**2 +Re**2))


	#power Spectrum
	S = Spectrum[:,:,0] + 1j*Spectrum[:,:,1]
	mag2 = np.real(S*np.conjugate(S))
	if parameters.DecibelRepresentationFlag:
		mag2 = 20*np.log(mag2)
	#mag2 = np.abs(mag)**2

	# selected spectrum to be plotted
	if parameters.PowerSpectrumFlag == True:
		spectrum = mag2
	else:
		spectrum = mag

	#--------------------------------
	#    define the wavenumber axis
	#--------------------------------
	step =1/subset.resolution[0]
	freqs = np.linspace(0,(spectrum.shape[1]-1)*step/spectrum.shape[1],spectrum.shape[1])
	fCenter = 0.5 * (freqs[np.int(spectrum.shape[1]/2)] + freqs[np.int(spectrum.shape[1]/2)-1] )
	freqs =freqs - fCenter  # axis centered on 0
	k = 2*np.pi*(freqs)

	#store data
	ImageSpectrum = CL.SpectrumData(k, spectrum)

	return ImageSpectrum

###########################################################
#
#		WAVE SPECTRUM
#
###########################################################

def ComputeSpectrum(SubsetParameters, ComputingParameters, Subsets):
	#--------------------------------------------------------------------------
	# Estimate Subsets Spectra and directions and determine their mean values
	#--------------------------------------------------------------------------

	WaveSpectra, Directions, ImageSpectra = [], [], []

	for i in range(SubsetParameters.BoxNb):
		subset = Subsets[i]
		# Compute wave related spectrum
		if ComputingParameters.SpectrumParameters.WaveSpectrumParameters.SpectrumType in {'waves', 'Waves'}:
			# use a multiple of wave signal
			SpectrumComputedData = SubsetSpectrum(ComputingParameters, subset)
		elif ComputingParameters.SpectrumParameters.WaveSpectrumParameters.SpectrumType in {'radial', 'Radial'}:
			# use the radial integration of the Image Spectrum
			SpectrumComputedData = RadialSpectrum(ComputingParameters, subset)
		else:
			sys.exit("Method for Spectrum Estimation not defined")

		# store data
		Directions.append(SpectrumComputedData.WaveDirection);
		WaveSpectra.append(SpectrumComputedData.WaveSpectrum);
		ImageSpectra.append(SpectrumComputedData.ImageSpectrum);

	# compute mean directions
	direction = np.nanmean(Directions)

	# compute mean Spectrum
	K = np.zeros((SubsetParameters.BoxNb, WaveSpectra[0].k.shape[0]));
	WSP = np.zeros((SubsetParameters.BoxNb,WaveSpectra[0].Spectrum.shape[0]))
	for i in range(SubsetParameters.BoxNb):
		K[i,:] = WaveSpectra[i].k; WSP[i,:] = WaveSpectra[i].Spectrum
	k = np.mean(K,axis=0); spectrum = np.mean(WSP,axis=0); spectrumstd = np.std(WSP,axis=0)

	"""
	fig, ax = plt.subplots(1)
	for i in range(SubsetParameters.BoxNb):
		ax.plot(K[i,:], WSP[i,:])
	plt.show()
	"""

	# compute peak wavelength
	PeakWavelength = WavelengthEstimate(ComputingParameters, k, spectrum)

	# store processed data
	Spectrum = CL.SpectrumProcessedData(k, spectrum, spectrumstd, PeakWavelength)

	# post-processing data for figures and statistics
	SubscenesSpectrum = CL.SpectrumComputedData(Directions, WaveSpectra, ImageSpectra, Subsets)

	# store mean data
	ComputedSpectrumData = CL.SpectrumComputedData(direction, Spectrum)

	return ComputedSpectrumData, SubscenesSpectrum


def WavelengthEstimate(ComputingParameters, k, spectrum):
	#-----------------------------------------
	#	Estimate Peak Wavelength
	#----------------------------------------
	# parameters
	if ComputingParameters.SpectrumParameters.WaveSpectrumParameters.SpectrumType == 'Radial':
		kth = 0.01
		data = CL.DataPeak(k[np.where(k>kth)], spectrum[np.where(k>kth)])
	else:
		data = CL.DataPeak(k, spectrum)
	WavelengthParameters = ComputingParameters.SpectrumParameters.WavelengthEstimationParameters
	peak_parameters = CL.PeakParameters(WavelengthParameters.Power)

	# mean wavenumber estimate
	PeakWavenumber = UT.PeakDetection(peak_parameters, WavelengthParameters.PeakDeterminationMethod, data)

	# wavelength
	PeakWavelength = 2*np.pi/PeakWavenumber

	return PeakWavelength

#******************************************************
#	    WAVE SPECTRUM from Wave Series
#******************************************************

def SubsetSpectrum(parameters, subset_input):
	#--------------------------------------------------------------------------------------
	# function that process a given subset image estimate the wave incident direction
	# and compute the wave spectrum
        #--------------------------------------------------------------------------------------

	#--------------------------
	# A) Subset Processing
	#--------------------------subset_input.image
	# parameters
	IP_Parameters = parameters.SubsetProcessingParameters

	#stretch contrast
	if IP_Parameters.ConstrastStretchFlag:
		image = IP.ScaleImage(IP.ContrastStretch(subset_input.image, IP_Parameters.IntensityType), subset_input.image.astype('float32'))
		subset = CL.Subset(subset_input.CenterPoint, image, subset_input.coordinates, subset_input.resolution, subset_input.FlagFlip)
	else:
		image = IP.ScaleImage(subset_input.image, subset_input.image.astype('float32'))
		subset = CL.Subset(subset_input.CenterPoint, image, subset_input.coordinates, subset_input.resolution, subset_input.FlagFlip)
	#--------------------------
	# B) Subset Spectrum
	#--------------------------
	Image_Spectrum = ImageSpectrum(IP_Parameters, subset)

	#--------------------------
	# C) Direction Estimate
	#--------------------------
	DE_Parameters = parameters.DirectionEstimateParameters
	direction = DirectionEstimate(DE_Parameters, subset, Image_Spectrum)

	#--------------------------------------
	# D) Apply Butterworth Elliptic Filter
	#-------------------------------------
	IF_Parameters = parameters.FilterParameters;
	if IF_Parameters.FlagFilter:
		FilteredImage = ImageFilter(IF_Parameters, subset, direction)
		subset = CL.Subset(subset.CenterPoint, FilteredImage, subset.coordinates, subset.resolution, subset.FlagFlip)
		Image_Spectrum = ImageSpectrum(IP_Parameters, subset)

		#---------------------------
		# C1) Direction re-estimate
		#---------------------------
		DE_Parameters = parameters.DirectionEstimateParameters
		direction = DirectionEstimate(DE_Parameters, subset, Image_Spectrum)
	#---------------------------------------------
	# E) Extract Wave Series and Compute Spectrum
	#---------------------------------------------
	SP_Parameters = parameters.SpectrumParameters.WaveSpectrumParameters
	K, Ks, S, Sp, Sstd = WavesMeanSpectrum(SP_Parameters, subset, direction)
	#---------------------------------------------
	# F) Store data
	#---------------------------------------------
	Spectrum = CL.SpectrumData(Ks, Sp)
	subset_output = subset
	Spectrum_Computed_Data = CL.SpectrumComputedData(direction, Spectrum, Image_Spectrum, subset_output)

	return Spectrum_Computed_Data


def WavesMeanSpectrum(parameters, subset, direction):

	#----------------------------------------------------------------------------------
	#	Compute Wave mean Spectrum from a set of directionnal line from
	#
	#  variables :	- img: selected image
	#		- direction: wave direction estimate
	#  		- npr: nb of selected profiles for the computation
	#		- OffsetDistance: distance (m) in between the profiles
	#		- paddingextrapower: extension of the padding (2**(image_closest_Powerof2+paddingextrapower))
	#		- FlagMean: flag for mean computation (0: normal mean, 1: weighted mean (distance))
	#
	#----------------------------------------------------------------------------------
	# find line that pass by center
	image = subset.image
	center = IP.ImageCenter(image); center = np.round(center);
	linecenter = DefineLine(image, direction, center, FlagOrtho = 0)

	# image related direction
	direction = UT.CartesianNautical(direction)
	if subset.FlagFlip:
		direction = 360-direction

	# define its orthogonal
	ortholine = DefineLine(image, direction, center, FlagOrtho = 1)

	#define group of offset
	if np.mod(parameters.ProfileNumber,2)>0:
		parameters.ProfileNumber = parameters.ProfileNumber - 1  # even number (central profile included)

	# information for offset points estimate
	information = CL.offsetinformation(parameters.ProfileNumber, parameters.ProfileOffsetDistance, direction, subset.resolution)

	# find points on the orthogonal line
	points = FindOffsetPoints(center, information)

	# find closest power of 2 to image dimensions
	padding = resolutionpadding(image, parameters.PaddingExtraPower)

	#array initialization
	dim = points.shape[0]
	K = np.zeros((dim, np.int(padding/2))); S =  np.zeros((dim, np.int(padding/2)));  distance = np.zeros(dim);

	"""
	fig, (ax1,ax2,ax3) = plt.subplots(3)
	"""
	"""
	fig, ax = plt.subplots(1)
	ax.imshow(image,cmap=plt.cm.gray, aspect='equal', extent = [0,image.shape[0],image.shape[0],0]);
	"""

	# process the different lines in the selected ROI and compute mean spectrum
	for i in range(dim):
		liner = DefineLine(image, direction, points[i,:], FlagOrtho = 0)
		# find edge of different lines with the image
		edpt = DetectLineEdge(image, liner)

		"""
		ax.plot(liner.x,liner.y,'c');
		ax.plot(edpt.point1[0],edpt.point1[1],'ob',edpt.point2[0],edpt.point2[1],'ob');
		"""

		# extract profile and evaluate distance
		yline = profile_line(image, edpt.point1, edpt.point2, linewidth=1, order=2)
		yline = yline - np.mean(yline)
		xline = Distance4Line(yline,edpt,subset.resolution)
		dmax = np.max(xline)

		# perform zero padding (to get same dimension Spectrum from varying dimension lines and avoid interpolation)
		xline, yline = zerospadding(xline, yline, padding)

		# spectrum of the wave series
		ks, Spectrum = Spectrum1D(xline, yline, parameters.PowerSpectrumFlag);

		# store data
		K[i,:] = ks; S[i,:] = Spectrum; distance[i] = dmax;

		"""
		if i==2:
			ax1.plot(xline,yline)
			ax2.plot(ks,Spectrum)
		"""
	#plot

	"""
	xl = [0, image.shape[0]]; yl = [image.shape[1], 0];
	ax.set_xlim(xl); ax.set_ylim(yl); plt.axis('off');
	"""
	# compute weight Spectrum relative to the distance a line cover on the image

	SumDistance = np.sum(distance);
	if parameters.MeanMethod > 0:
		# mean weighted (distance of line segment) Spectrum
		Ks = np.dot(distance,K) / SumDistance; Sp = np.dot(distance,S) / SumDistance
	else:
		# mean Spectrum
		Ks = np.mean(K, axis=0); Sp = np.mean(S, axis=0)

	#standard deviation of the set
	Sstd = np.std(S, axis=0)
	"""
	ax3.plot(Ks, Sp)
	"""
	"""
	plt.show()
	"""

	return K, Ks, S, Sp, Sstd


#************************************************************
#	    WAVE SPECTRUM from Spectrum Radial Integration
#************************************************************
def RadialSpectrum(parameters, subset_input):
	#--------------------------
	# A) Subset Processing
	#--------------------------

	# Parameters
	IP_Parameters = parameters.SubsetProcessingParameters
	#stretch contrast
	if IP_Parameters.ConstrastStretchFlag>0:
		image = IP.ScaleImage(IP.ContrastStretch(subset_input.image, IP_Parameters.IntensityType), subset_input.image.astype('float32'))
		subset = CL.Subset(subset_input.CenterPoint, image, subset_input.coordinates, subset_input.resolution, subset_input.FlagFlip)
	else:
		image = IP.ScaleImage(subset_input.image, subset_input.image.astype('float32'))
		subset = CL.Subset(subset_input.CenterPoint, image, subset_input.coordinates, subset_input.resolution, subset_input.FlagFlip)
	#--------------------------
	# B) Subset Spectrum
	#--------------------------
	Image_Spectrum = ImageSpectrum(IP_Parameters, subset)

	"""
	fig, (ax1,ax2) = plt.subplots(2)
	ax1.imshow(subset.image)
	ax2.imshow(Image_Spectrum.Spectrum)
	plt.show()
	"""
			
	#--------------------------
	# C) Direction Estimate
	#--------------------------
	# determine radius of influence
	R, _, _ = Influence_Radius(Image_Spectrum)
	#print 'test31'
	DE_Parameters = parameters.DirectionEstimateParameters
	direction = DirectionEstimate(DE_Parameters, subset, Image_Spectrum)
	#--------------------------------------
	# D) Apply Butterworth Elliptic Filter
	#-------------------------------------
	IF_Parameters = parameters.FilterParameters
	DE_Parameters = parameters.DirectionEstimateParameters
	if IF_Parameters.FlagFilter:
		FilteredImage = ImageFilter(IF_Parameters, subset, direction)
		subset = CL.Subset(subset.CenterPoint, FilteredImage, subset.coordinates, subset.resolution, subset.FlagFlip)
	#------------------------------
	# E) Perform Image Padding
	#------------------------------
	RI_Parameters = parameters.SpectrumParameters.WaveSpectrumParameters

	#---------------------------------------------------
	# F) Re-Compute Image Spectrum and wave direction
	#----------------------------------------------------
	Image_Spectrum = ImageSpectrum(IP_Parameters, subset)
	direction = DirectionEstimate(DE_Parameters, subset, Image_Spectrum)
	#------------------------------------------------
	# G) Process Spectrum
	#------------------------------------------------

	Spectrum = Image_Spectrum.Spectrum; k = Image_Spectrum.k;
	mask = MaskPlot(R, subset)
	Spectrum[mask] = 0
	#---------------------------------------------
	# H) Compute radial integration and
	#---------------------------------------------
	Rr, RadialIntegration = RadialProjection(Spectrum)

	#---------------------------------------------
	# I) Evaluate k-axis in agreement with Radius
	#---------------------------------------------
	dk = np.sum(np.diff(k))/(k.shape[0]-1)
	kr = Rr*dk

	"""
	fig, ax = plt.subplots(1)
	ax.plot(kr, RadialIntegration)
	ax.plot(kr, RadialIntegration,'or')
	plt.show()
	"""

	#---------------------------------------------
	# I) store data
	#---------------------------------------------
	Spectrum = CL.SpectrumData(kr, RadialIntegration)
	subset_output = subset
	Spectrum_Computed_Data = CL.SpectrumComputedData(direction, Spectrum, Image_Spectrum, subset_output)

	return Spectrum_Computed_Data

def RadialProjection(img):
    	"""
    	integrate the spectrum to create the averaged radial profile.
   	"""
	# indices of image center
	center = IP.ImageCenter(img)

	# image indices
   	y, x = np.indices(img.shape)

   	#radial axis
   	r = cv2.magnitude(np.float32(x - center[0]), np.float32(y - center[1]))

   	# sort the radius (crescent)
   	ind = np.argsort(r.flat)
   	r_sorted = r.flat[ind] # sorted radius
   	img_sorted = img.flat[ind] # sorted image pixels (same order)

   	# r is integer (bin wise)
	r_int = np.round(r_sorted)

	# unique r decomposition, indi reflect the radius bin
	ru, ind, indi, count = np.unique(r_int,return_index=True, return_inverse=True, return_counts=True)
 	csim = np.cumsum(img_sorted, dtype=float)

	# sum all the magnitude/imtensity of pixel with same radius
	tbin = np.zeros((ru.shape[0]))
	tbin[:-1] = csim[ind[1:]-1]-csim[ind[:-1]-1]
	tbin[0] = csim[ind[1]-1]
	tbin[-1] = csim[-1]-csim[ind[-1]-1]

	# normalize by the number of pixel with same radius
	radial_profile = tbin / count

	# store data
	Radius = ru; RadialIntegration = radial_profile

	return Radius, RadialIntegration

#######################################################
#
#	    IMAGE FILTERS
#
#######################################################

def ButterworthEllipticFilter(parameters, subset, angle):
	#-----------------------------------------------------------------------------------------------------------------------------------------------------
	# Butterworth elliptic directionnal low-pass filter (adapted from Peter Kovesi's code in matlab)
	#input arguments:
	#	- dimension : image dimension
	#	- cutoffM/m : the cutoff frequency on the major and minor axes of the ellipse (0 < cutoff <= 1)
	#	- n : order of the filter
	#	- angle : input probable wave angle
	#	- offsetx/y :  offsets in the x and y direction (offset=0 corresponds to the center and offset=1 corresponds to the edge of the filter)
	#-----------------------------------------------------------------------------------------------------------------------------------------------------
	# image related direction
	angle = UT.CartesianNautical(angle)
	if subset.FlagFlip:
		angle = 360-angle

	# get rows and column number from dimension
	dimension = subset.image.shape
	rows = dimension[0]; cols = dimension[1];

	# create vectors normalized in between +- 0.5
	tmp1 = np.linspace(1,cols,cols); tmp2 = np.linspace(1,rows,rows);
	a1 = 1./(cols-1); b1 = -0.5 *(cols+1)/(cols-1); a2 = 1./(rows-1); b2 = -0.5 *(rows+1)/(rows-1); # define substitution (1:dimension -> -0.5:0.5)
	tmp1 = a1 * tmp1 + b1; tmp2 = a2 * tmp2 + b2; # perform substitution

	#initialize x and y
	x = np.outer(np.ones(rows,),tmp1)
	y = np.outer(np.transpose(tmp2),np.transpose(np.ones(cols,)));

	# applies a linear transformation to rotate through alpha.
	angle = angle*np.pi/180
	x2 = (x*np.cos(angle) - y*np.sin(-angle));
	y2 = (x*np.sin(-angle) + y*np.cos(angle));

	#ellipse radius
	a = parameters.EllipseBigRadius/2;
	b = parameters.EllipseSmallRadius/2;

	#filter design
	Filter = 1./(1.+((x2/(a))**2 + (y2/(b))**2)**parameters.Power);

	return Filter

def ImageFilter(parameters, subset, angle):
	#-----------------------------------------------------
	# Filter image:
	#             	- estimate image spectrum
	#               - apply filter in frequency domain
	#               - reconstitute image
	#----------------------------------------------------
	# image spectrum
	Spectrum = imfft(subset.image)
        # magnitude
	mag = 20*np.log(cv2.magnitude(Spectrum[:,:,0],Spectrum[:,:,1]))
	# define filter
	Filter1 = ButterworthEllipticFilter(parameters, subset, angle)
	Filter = np.tile(Filter1[...,None], (1,1,2))
	# apply filter
	Spectrum = np.multiply(Filter,Spectrum)
	# magnitude of filtered spectrum
	magf = 20*np.log(cv2.magnitude(Spectrum[:,:,0],Spectrum[:,:,1]))
	#image restitution
	image = imifft(Spectrum)

	"""
	fig,((ax1),(ax2),(ax3)) = plt.subplots(1,3)
	ax1.imshow(mag);ax1.axis('off');
	ax2.imshow(cv2.magnitude(Filter[:,:,0],Filter[:,:,1]));ax2.axis('off')
	ax3.imshow(magf);ax3.axis('off')
	"""
	return image

def imfft(image):
	#fft transform of 2D image with central low-frequencies
	return np.fft.fftshift(cv2.dft(np.float32(image),flags = cv2.DFT_COMPLEX_OUTPUT))

def imifft(Spectrum):
	#inverse fft transform of Spectrum to image
	f =  cv2.idft(np.fft.ifftshift(Spectrum))
	return cv2.magnitude(f[:,:,0], f[:,:,1])


#******************************************************
#	    WAVE SPECTRUM Utilities
#******************************************************
def Spectrum1D(xline, yline, PowerSpectrumFlag):
	#------------------------------------------------
	# estimate spectrum from intensity pixel lines
	#------------------------------------------------
	diml = yline.shape[0]; resl = np.sum(np.diff(xline))/(diml-1); step = 1./resl;
	# wavenumber axis
	freqs = np.linspace(0,(diml-1)*step/diml,diml); frqs =  freqs[range(diml/2)]
	ks = 2*np.pi*freqs; ks = ks[range(diml/2)]
	# fourier transform
	Y = np.fft.fft(yline); Y = Y[range(diml/2)]; YY = np.reshape(cv2.magnitude(np.real(Y),np.imag(Y)), (Y.shape[0]));
	if PowerSpectrumFlag:
		YY = Y*np.conjugate(Y)
	return ks, np.real(YY)

def DefineLine(img, direction, point, FlagOrtho):
	#-----------------------------------------------
	# Define line slope, offset and equation
	#-----------------------------------------------
	fac = np.pi/180

	# image dimension
	dim = img.shape

	# determine line coefficients
	a = np.tan(fac * direction);	# slope
	if FlagOrtho == 1:		# orthogonal slope a*a'=-1
		a = -1/a
	b = point[1] - a * point[0];	# constant

	# estimate line
	x = np.linspace(0,dim[0]-1,dim[0]); y = a * x + b

	# store data
	lined = CL.line(x, y, a, b)

	return lined

def FindOffsetPoints(center, information):
	#----------------------------------------------------
	# Find Offset points (given an offset in meters)
	#----------------------------------------------------
	#offset parameters
	fac = np.pi/180
	direction = fac*(90 + information.Direction);

	#pixelwise offset in the x/y direction according to the wave incident angle
	OffsetPixelx = information.OffsetDistance*np.cos(direction)/information.Resolution[0];
	OffsetPixely = information.OffsetDistance*np.sin(direction)/information.Resolution[1]

	# find points on the orthogonal line that correspond to the selected offset
	points = np.zeros((information.ProfileNumber+1,2));	# array initialization
	points[0,:] = center				# include center
	j=0

	for k in range(np.round(information.ProfileNumber/2)):
		i = j+1
		j = i+1;
		points[i,0] = center[0] + (k+1) *OffsetPixelx; points[i,1] = center[1] + (k+1) *OffsetPixely 	# 1st point
		points[j,0] = center[0] - (k+1) *OffsetPixelx; points[j,1] = center[1] - (k+1) *OffsetPixely	# 2nd point
	return points

def dy(distance, m):
    return m*dx(distance, m)

def dx(distance, m):
    return distance*np.sqrt((m**2+1))

def DetectLineEdge(img, lined):
	#------------------------------------------------------------
	# Detect intersection points of image edges by a given line
	#------------------------------------------------------------
	# initialization
	point1 = np.zeros(2); point2 = np.zeros(2); dim = img.shape;

	# Detect intersection with image edge
	m = np.min(lined.y); M = np.max(lined.y);

	if m < 0:
		point1[0] = np.int(np.rint(-lined.b/lined.a));  point1[1] = 0;
	else:
		point1[0] = 0; point1[1] = np.int(np.rint(lined.b));
	yy = dim[1]-1; xx = dim[0]-1;
	if M > yy:
		point2[1] = yy; point2[0] = np.int(np.rint((yy-lined.b)/lined.a));
	else:
		point2[0] = xx; point2[1] = np.int(np.rint(lined.a*xx+lined.b));

	# store data
	edpt = CL.edgepoint(point1,point2)

	return edpt

def Powerof2(img):
	#--------------------------------------------------
	# determine closest power of 2 for both dimensions
	#--------------------------------------------------
	power = np.zeros(2)
	dim = img.shape;
	power[0] = np.round(np.log(dim[0])/np.log(2))
	power[1] = np.round(np.log(dim[1])/np.log(2))
	return power

def resolutionpadding(img,n):
	#----------------------------------------------------
	# compute power of 2, superior to the size of image
	#----------------------------------------------------
	return 2**(np.int(np.max(Powerof2(img))+n))

def zerospadding(x,y,powerof2):
	#-----------------------------------
	#perform zeros padding of a signal
	#-----------------------------------
	# y
	yz = np.zeros(powerof2); yz[:x.shape[0]] = y; # zeros padding
	# x
	res = np.sum(np.diff(x))/(x.shape[0]-1)
	xz = np.linspace(0,res*(powerof2-1), powerof2)
	return xz,yz

def Distance4Line(y,points,res):
	#-----------------------------------------------
	# Define distance axis
        #-----------------------------------------------
	dim = y.shape[0]
	distance = np.sqrt( (points.point2[0]-points.point1[0])**2 + (points.point2[1]-points.point1[1])**2)
	x = np.linspace(0, distance, dim)*res[0]
	return x

#******************************************************
#	    TRASH for now
#******************************************************

def DetectLineEdgetest(img, direction, offset):
	#--------------------------------------------------------------------------------------------------------
	# function that find the intersection point between a line and a given image edges
	# remark: to be used to extract pixel intensity profiles with profile_line from skimage.measure toolbox
	#---------------------------------------------------------------------------------------------------------

	# initialization
	x1 = np.zeros(2); x2 = np.zeros(2)
	# get image dimension
	dim = img.shape
	# get image center
	center = IP.ImageCenter(img); center = np.round(center);
	# x and y axis
	x = np.linspace(0,dim[0]-1,dim[0]); y = np.linspace(0,dim[1]-1,dim[1])
	# x0 = np.linspace(0,0,dim[0]); x256 = np.linspace(dim[0],dim[0],dim[0]);
	# linear coefficient
	a = np.tan(direction*np.pi/180); b = center[1] - a * center[0];
	# line
	yline = a * (x-offset) + b
	# min and max
	m = np.min(yline); M = np.max(yline);
	if m < 0:
		x1[1] = 0; x1[0] = np.int(-b/a	+ offset)
	else:
		x1[0] = 0; x1[1] = np.int(a*(-offset) + b)
	yy = dim[1]-1; xx = dim[0]-1;
	if M > yy:
		x2[1] = yy; x2[0] = np.int((yy-b)/a+offset)
	else:
		x2[0] = xx; x2[1] = np.int(a*(xx-offset)+b)

	return x1, x2, yline

def MeanWaveSeriesSpectrum(image, direction, res, linewidth, paddingextrapower):
	#--------------------------------------------------------------------
	# extract wave series from mean direction line and compute Spectrum
	#--------------------------------------------------------------------

	# line segment (in selected direction) that passed by image center
	center = IP.ImageCenter(image); center = np.round(center);
	linecenter = DefineLine(image, direction, center, FlagOrtho = 0)

	# Detect intersection of the line with the image edges
	edpt = DetectLineEdge(image, linecenter)

	# extract
	yline = profile_line(image, edpt.point1, edpt.point2, linewidth, order=2);
	xline = Distance4Line(yline,edpt,res)

	# perform zero padding (to increase spectrum resolution)
	padding = resolutionpadding(image, paddingextrapower)
	xline1, yline1 = zerospadding(xline, yline, padding)

	# spectrum of the wave series
	ks, Spectrum = Spectrum1D(xline1, yline1,  0)
	"""
	#figure
	fig, ax = plt.subplots(1)
	xl = [0, image.shape[0]]; yl = [image.shape[1], 0];
	#image
	ax.imshow(image,cmap=plt.cm.gray, extent = [0,image.shape[0],image.shape[0],0])
	# line in the mean direction passing by the center of the image
	ax.plot(linecenter.x,linecenter.y,'c');
	# limit lines
	offset = np.int(np.rint(linewidth/2))
	point1=np.zeros(2); point1[1]=center[1]; point1[0] = center[0]-offset;
	point2=np.zeros(2); point2[1]=center[1]; point2[0] = center[0]+offset;
	line1 = DefineLine(image, direction, point1, FlagOrtho = 0)
	line2 = DefineLine(image, direction, point2, FlagOrtho = 0)
	ax.fill_between(linecenter.x,linecenter.y, line1.y, where=linecenter.y>=line1.x, Facecolor=(0.1,0.1,0.6,0.5), interpolate=True)
	ax.fill_between(linecenter.x,linecenter.y, line2.y, where=linecenter.y<=line2.x, Facecolor=(0.1,0.1,0.6,0.5), interpolate=True)
	ax.fill_between(linecenter.x,line1.y, linecenter.y, where=linecenter.y<=line1.x, Facecolor=(0.1,0.1,0.6,0.5), interpolate=True)
	ax.fill_between(linecenter.x,line2.y, linecenter.y, where=linecenter.y>=line2.x, Facecolor=(0.1,0.1,0.6,0.5), interpolate=True)
	ax.plot(line1.x,line1.y,'c', line2.x, line2.y,'c');
	ax.set_xlim(xl); ax.set_ylim(yl)
	plt.axis('off')
	plt.show()
	"""
	return xline,yline, ks, Spectrum
