#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


"""
=====================================================================================================
Gather all the utilities functions  
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: Nov/2017
=====================================================================================================
	ROI
					ResizeArray

	Conversion 	
					List2Array	Array2List	rads2deg

	ReadWrite	
					ReadPointsfromFile	WritePointstoFile
	
	Interpolation/Averaging
					find_nearest	groupedAvg
	
	Statistics
					RMSE		Correlation

	Peak Detection
					PeakDetection	CentroidPeakPosition	ClusterPeakPosition	DistributionFitPeakPosition	
					ThresholdCrossing	AboveThresholdValues	
	Statistical Fit Functions	objective_peak	objective_sin	
					RayleighDistribution	ChiDistribution
					fsin	fpositivesin
		
	Others
					sigma0
"""
#
import sys, os, re
#
import numpy as np
#
import cPickle as pickle
#
import CSAR_Classes as CL
#
import cv2
#
import itertools
#
import sklearn.cluster as skc
import scipy.cluster.vq as svq
from scipy.optimize import minimize

#*********************
#	ROI
#*********************
def ResizeArray(array, fac):
	return cv2.resize(array, (1200,1200), interpolation = cv2.INTER_NEAREST)

def List2Array(data):
        #--------------------------------------------------------------------------
        #
        # convert coordinate data in list into an workable numpy coordinate array
        #
        #---------------------------------------------------------------------------
	nx = data.shape[0];
	array  = np.zeros((nx,2))
	for i in range(data.shape[0]):
		array[i,0] = data[i].easting;  array[i,1] = data[i].northing;		
		
	return array

#***********************************
# save temporary computation files
#***********************************
def Unpickle_File(fname):
	#-----------------------------
	# load temporary file
	#-----------------------------
	#data=[];
	with open(fname,'rb') as f:
		data = pickle.load(f)
	return data

def Pickle_File(fname,data):
	#-----------------------------
	# save temporary file
	#-----------------------------
	with open(fname, 'wb') as f:
        	pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

def ListDichotomy(List,delimitertype='d'):
	#--------------------------------------------
	# divide filename in 2 list
	# possible criteria: digits, delimiter type 
	#--------------------------------------------
	FileList, ExceptionList = [], []

	if delimitertype=='digits' or delimitertype=='d':
		for L in List:
			num = re.findall('\d+', L)
			if num:
				FileList.append(L)
			else:
				ExceptionList=L
	else:
		sys.exit('Type of delimiter not allowed (yet)')


	return FileList, ExceptionList

def Create_Image_Parameters_TransferFile(Subsetparameters, ImageParameters, data):
	#----------------------------------------------------------
	# Create transfer file to save Image data and Information
	#----------------------------------------------------------
	# path
	cwd = os.getcwd()
	path = cwd+'/'
	
	#save image to a pickle file	
	filename = path + 'Image.out'	
	data.pickle(filename)
	
	#save parameters to pickle file
	#filename = path + 'parameters.out'
	#parameters.pickle(filename)

def Create_Subset_TransferFile(index, parameters, point, SubsetData, outlist):
	#-----------------------------------------------------------------------
	# Create transfer file to save grid point subsets data and information
	#------------------------------------------------------------------------
	# path and filename
	cwd = os.getcwd()
	path = cwd+'/'
	fname = 'subset'
	if outlist:
		transfer_file = path + outlist[index]
	else:
		transfer_file = path + fname + str(index) + '.out'
	# gather data	
	Subset = CL.SubsetTransferData(parameters, point, SubsetData)
	
	# save data
	Subset.pickle(transfer_file)
	
def Create_TransferFile(args, point, datatype):
	#----------------------------------------------------------------------------
	# Create transfer file to save : - grid point Spectrum and wavelength
	#				 - grid point information and depth estimate
	#----------------------------------------------------------------------------

	# path
	cwd = os.getcwd()
	path = cwd+'/'
	if (datatype=='Spectrum') or (datatype=='spectrum'):
		fname = 'Spectrum';
	elif (datatype=='Inversion') or (datatype=='inversion'):
		fname = 'Inversion';
	else:
		sys.exit('unknown tranfered data');
	
	#file name 
	if args.output:
		transfer_file = args.output
	else:
		num = re.findall('\d+', args.input)
		transfer_file = path + fname + str(num[0]) + '.out'

	#save data
	point.pickle(transfer_file)

#**************************
#	Conversion
#**************************
def Array2List(array):
        #---------------------------------------------------------------------
        #
        # convert numpy coordinate array coordinate into a list of data 
        #
        #----------------------------------------------------------------------
	data = []	
	for i in range(array.shape[0]):
		if array.shape[1] == 1:
			point = CL.GridPoints(array[i,0])
		elif array.shape[1] == 2:
			point = CL.GridPoints(array[i,0], array[i,1])			
		elif array.shape[1] == 3:
			point = CL.GridPoints(array[i,0], array[i,1], array[i,2])
		data.append(point)
	data = np.asarray(data)	

	return data

def rads2deg(radians):
	#----------------------------------
	# convert radian to degree
	#----------------------------------	
	return radians*(180/np.pi)

def CartesianNautical(angle):
	return np.mod((360-angle)+90,360)

#**************************
#	Read/Write
#**************************
def ReadPointsfromFile(filename):	        
	#----------------------------------------------------------------------
        #
        # read points from file (default format: ASCII)
        #
        #----------------------------------------------------------------------
	#read data from file	
	Points=np.loadtxt(filename)
	#convert to default list format
	points = Array2List(Points)
	
	return points

def WritePointstoFile(points, filename):
	#----------------------------------------------------------------------
        #
        # write points to file (default format: ASCII)
        #
        #----------------------------------------------------------------------
	# convert list of data into array	
	data = List2Array(points)

	# write in file
	np.savetxt(filename,data)


#***************************************************
#		Grid Points
#***************************************************

def ReadGridPoints(args,coordinates):
	#----------------------------------------------------------------------
        #
        # find image pixel that correspond to the grid point
        #
        #----------------------------------------------------------------------	
	# image coordinates
	Easting = coordinates.easting[0,:]; Northing = coordinates.northing[:,0]
	
	# grid points coordinates
	points, flagbathy =  ReadPointsfromGridFile(args.bathymetry)	

	# find correspondance grid / image
	Points = []	
	for point in points:	
		indE = np.argmin(np.abs(Easting-point.easting))		
		indN = np.argmin(np.abs(Northing-point.northing))
		data = CL.GridPointsData(indE, indN, Easting[indE], Northing[indN], point.apriori_bathymetry)
		Points.append(data)
	Points = np.asarray(Points)

	return Points, flagbathy

def ReadPointsfromGridFile(filename):	        
	#----------------------------------------------------------------------
        #
        # read points from file (default format: ASCII(txt) or npz)
        #
        #----------------------------------------------------------------------
	#read data from file
	if '.npz' in filename:
		npzfile = np.load(filename);
		Points = npzfile[npzfile.files[0]];		
	elif '.txt' in filename:	
		Points=np.loadtxt(filename);
	else:
		sys.exit("File extension not recognized, check your input Grid file (npz or txt accepted)")

	# bathy or not bathy?
	if Points.shape[1]<3:
		flagbathy = False
		ext=np.zeros((Points.shape[0],1))*np.nan
		Points = np.concatenate((Points, ext), axis = 1)
	elif np.mean(Points[:,2])==0 or np.mean(Points[:,2])==np.nan:
		flagbathy = False
		Points[:,2] = np.nan
	else:
		flagbathy = True

	#convert to default list format
	points = Array2List(Points);

	return points, flagbathy


#*********************************
#	Interpolation/Averaging
#*********************************
def find_nearest(array,value):
	#---------------------------------
	# find nearest array value index
	#---------------------------------	
	idx = (np.abs(array-value)).argmin()
	return array[idx],idx

def groupedAvg(myArray, N=6):
    result = np.nancumsum(myArray, 0)[N-1::N]/float(N)
    result[1:] = result[1:] - result[:-1]
    return result


#*******************************
# 	Statistics
#*******************************

def RMSE(signal, reference):
	#-----------------------------------------------------
	# compute rmse of an array to a reference value (mean)
	#-----------------------------------------------------
	if signal.shape[0] >  signal.shape[1]:
		signal = np.transpose(signal)	
	#initialization
	rmse = np.zeros(signal.shape[0])
	
	#compute rmse
	for i in range(signal.shape[0]):
		diff = np.sum((signal[i,:] - reference)**2)
		rmse[i] = np.sqrt(diff/signal.shape[0])

	return rmse

def Correlation(signal, reference):
	#----------------------------------------------------------------
	# compute Correlation of an array to a reference value (mean)
	#----------------------------------------------------------------
	if signal.shape[0] >  signal.shape[1]:
		signal = np.transpose(signal)	
	#initialization
	correlation = np.zeros(signal.shape[0])
	
	#compute rmse
	for i in range(signal.shape[0]):
		C = np.corrcoef(signal[i,:], reference)
		correlation[i] = np.min(C)

	return correlation

#****************************
# 	Peak detection
#****************************


def PeakDetection(parameters, method, data):
	
	#--------------------------------------------------------------
	# 	Detect peak position in observation, data or spectrum
	#--------------------------------------------------------------
	# load data	
	x = data.x; y = data.y;
			
	if method in {'max', 'Max', 'maximum', 'Maximum'}:				# simple maximum detection
		I = np.argmax(y); peakposition = x[I];	

	elif method in {'Centroid', 'centroid', 'CentroidPower','centroidpower'}:	# Centroid method
		peakposition = CentroidPeakPosition(parameters, data)
	
	elif method in {'Cluster', 'cluster', 'ClusterPower','clusterpower'}:		# Cluster method
		peakposition = ClusterPeakPosition(parameters, data)

	elif method in {'RayleighDistribution', 'ChiDistribution'}:
		peakposition = DistributionFitPeakPosition(parameters, data)		# Fit with know distribution (Rayleigh)
	
	return peakposition


def CentroidPeakPosition(parameters, data):
	#------------------------------------------------------------------
	# compute position of the curve centroid taken as the peak value
	#-----------------------------------------------------------------	

	# bins with significant energy (> ratio)
	index = np.where(data.y> parameters.ratio*np.max(data.y))	
	x, y = data.x[index], data.y[index]

	# estimate weighted peak value
	peakposition = np.sum(np.multiply(x,y**parameters.power))/np.sum(y**parameters.power)
	
	return peakposition
	
def  ClusterPeakPosition(parameters, observations):
	#-----------------------------------------------------------------------------------------------------
	# compute position of centroid of cluster with highest y-value which is considered as the peak value 
	#-----------------------------------------------------------------------------------------------------
	#parameters
	niter = 50		# number of iterations
	ncl = 2			# number of clusters
	thrc = 1e-5		# threshold of acceptance
	KmeansMethod = 1	# 1: scipy, 2: scikit-learn

	# transform data
	data=np.zeros((observations.x.shape[0],2)); data[:,0] = observations.x; data[:,1] = observations.y**parameters.power
	
	#scipy
	if KmeansMethod == 1:
		center,_ = svq.kmeans2(data,ncl, iter=niter, thresh=thrc, minit='points', missing='warn') #scipy cluster
	else: 
		kmeans = skc.KMeans(n_clusters=ncl, init='random', n_init=10, max_iter=niter, tol=thrc).fit(data) # scikit-learn	
		center = kmeans.cluster_centers_.squeeze(); 
	I = np.argmax(center[:,1])
	peakposition = center[I,0]	
	
	return peakposition


def DistributionFitPeakPosition(parameters, data):
	#--------------------------------------------------------
	# compute wave number associated to Spectrum peak value
	# method: fit with common wave distribution
	#--------------------------------------------------------
	# find maximum and crossing of threshold
	M = np.max(data.y); thrs = parameters.ratio*M;
	x_roi, y_roi = AboveThresholdValues(data.x, data.y, thrs)
	
	# fit curve with given distribution
	FirstGuess=[1, 0.004]	
	func = RayleighDistribution
	fg = func(x_roi-x_roi[0], FirstGuess)	
	result = minimize(objective_peak, FirstGuess , args=(func, x_roi-x_roi[0], y_roi-y_roi[0]), method='Nelder-Mead', options={'disp': True})
	
	#find function maximum
	y = RayleighDistribution(x_roi-x_roi[0],result.x)
	I = np.argmax(y)
	peakposition = x_roi[I]
	"""
	plt.plot(x,y)
	plt.plot(x_roi, y_roi,'c')
	plt.plot(x_roi,fg+y_roi[0],'r')
	plt.axhline(thrs, color='k', linestyle='--')
	plt.plot(x_roi,y+y_roi[0],'b')
	plt.plot(peakposition,y[I]+y_roi[0],'ok')
	plt.show()
	"""
	return peakposition

def ThresholdCrossing(x, y, thr):
	if x.shape>2:
		x = np.delete(x,x[0:-2])
	return x[np.diff(np.sign(y-thr)) != 0]

def AboveThresholdValues(x, y, thr):
	return x[y>thr], y[y>thr]


#*******************************
#	Statistical Fit
#*******************************

def objective_peak(coef, f, k, spectrum):
	return 0.5*np.dot((f(k, coef) - spectrum), (f(k, coef) - spectrum))

def objective_sin(a0, f, theta, distribution):
	return 0.5*np.dot((f(theta, a0[0], a0[1], a0[-1]) - distribution), (f(theta, a0[0], a0[1], a0[-1]) - distribution))

def RayleighDistribution(x,coef): 
	f = (coef[0]/coef[1]**2)*x*np.exp(-x**2/(2*coef[1]**2))
	return f

def ChiDistribution(x,coef): 
	f = coef[0]*(2**(1-coef[1]/2))*(x**(coef[1]-1))*np.exp(-x**2/2)/ssp.gamma(coef[1]/2)
	return f

def fsin(theta, a, b, c):
	return a * np.sin(2 * np.pi * (theta + b) / 180) + c 

def fpositivesin(theta, a, b, c):
	f = a * np.sin(2 * np.pi * (theta + b) / 180) + c
	f[f<c]=c
	return  f


#*******************************
#	Others
#*******************************
def CreateDirectories(Main, Sub):
	for dir1, dir2 in itertools.product(Main, Sub):
		try: os.makedirs(os.path.join(dir1,dir2))
		except OSError: pass

def sigma0(img):
	#----------------------------
	# Estimate image sigma0 
	#----------------------------
	imgOut = 10.*np.log10(img) # sigma0
	return imgOut

def detect_peaks(x, mph=None, mpd=1, threshold=0, edge='rising', kpsh=False, valley=False, show=False, ax=None):

	"""Detect peaks in data based on their amplitude and other features.
	
	Author: Marcos Duarte
	
	Parameters
	----------
	x : 1D array_like
	data.
	mph : {None, number}, optional (default = None)
		detect peaks that are greater than minimum peak height.
	mpd : positive integer, optional (default = 1)
		detect peaks that are at least separated by minimum peak distance (in
		number of data).
	threshold : positive number, optional (default = 0)
		detect peaks (valleys) that are greater (smaller) than `threshold`
		in relation to their immediate neighbors.
	edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
		for a flat peak, keep only the rising edge ('rising'), only the
		falling edge ('falling'), both edges ('both'), or don't detect a
		flat peak (None).
	kpsh : bool, optional (default = False)
		keep peaks with same height even if they are closer than `mpd`.
	valley : bool, optional (default = False)
		if True (1), detect valleys (local minima) instead of peaks.
	show : bool, optional (default = False)
		if True (1), plot data in matplotlib figure.
	ax : a matplotlib.axes.Axes instance, optional (default = None).

	Returns
	-------
	ind : 1D array_like
		indices of the peaks in `x`.

	Notes
	-----
	The detection of valleys instead of peaks is performed internally by simply
	negating the data: `ind_valleys = detect_peaks(-x)`
    
	"""
	x = np.atleast_1d(x).astype('float64')

	if x.size < 3:
		return np.array([], dtype=int)
	if valley:
		x = -x

	# find indices of all peaks
	dx = x[1:] - x[:-1]
	# handle NaN's
	indnan = np.where(np.isnan(x))[0]
	if indnan.size:
		x[indnan] = np.inf
		dx[np.where(np.isnan(dx))[0]] = np.inf
	ine, ire, ife = np.array([[], [], []], dtype=int)
	if not edge:
		ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
	else:
		if edge.lower() in ['rising', 'both']:
			ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
		if edge.lower() in ['falling', 'both']:
			ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    
	ind = np.unique(np.hstack((ine, ire, ife)))
   
	 # handle NaN's
	if ind.size and indnan.size:
	# NaN's and values close to NaN's cannot be peaks
		ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1))), invert=True)]
	# first and last values of x cannot be peaks
	if ind.size and ind[0] == 0:
		ind = ind[1:]
	if ind.size and ind[-1] == x.size-1:
		ind = ind[:-1]
	# remove peaks < minimum peak height
	if ind.size and mph is not None:
		ind = ind[x[ind] >= mph]
	# remove peaks - neighbors < threshold
	if ind.size and threshold > 0:
		dx = np.min(np.vstack([x[ind]-x[ind-1], x[ind]-x[ind+1]]), axis=0)
		ind = np.delete(ind, np.where(dx < threshold)[0])
	# detect small peaks closer than minimum peak distance
	if ind.size and mpd > 1:
		ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
		idel = np.zeros(ind.size, dtype=bool)	
		for i in range(ind.size):
			if not idel[i]:
				# keep peaks with the same height if kpsh is True
				idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
				& (x[ind[i]] > x[ind] if kpsh else True)
				idel[i] = 0  # Keep current peak
		# remove the small peaks and sort back the indices by their occurrence
		ind = np.sort(ind[~idel])

	if show:
		if indnan.size:
			x[indnan] = np.nan
		if valley:
			x = -x
		_plot(x, mph, mpd, threshold, edge, valley, ax, ind)

	return ind

def _plot(x, mph, mpd, threshold, edge, valley, ax, ind):
	"""Plot results of the detect_peaks function, see its help."""
	try:
		import matplotlib.pyplot as plt
	except ImportError:
		print('matplotlib is not available.')
	else:
		if ax is None:
			_, ax = plt.subplots(1, 1, figsize=(8, 4))
			ax.plot(x, 'b', lw=1)
		if ind.size:
			label = 'valley' if valley else 'peak'
			label = label + 's' if ind.size > 1 else label
			ax.plot(ind, x[ind], '+', mfc=None, mec='r', mew=2, ms=8,
			label='%d %s' % (ind.size, label))
			ax.legend(loc='best', framealpha=.5, numpoints=1)
		ax.set_xlim(-.02*x.size, x.size*1.02-1)
		ymin, ymax = x[np.isfinite(x)].min(), x[np.isfinite(x)].max()
		yrange = ymax - ymin if ymax > ymin else 1
		ax.set_ylim(ymin - 0.1*yrange, ymax + 0.1*yrange)
		ax.set_xlabel('Data #', fontsize=14)
		ax.set_ylabel('Amplitude', fontsize=14)
		mode = 'Valley detection' if valley else 'Peak detection'
		ax.set_title("%s (mph=%s, mpd=%d, threshold=%s, edge='%s')"
		% (mode, str(mph), mpd, str(threshold), edge))
                plt.show()
"""
#############################################
#	NPZ transfer files
#############################################
def CreateSubsetNPZ(index, parameters, point, SubsetData, outlist):
	#-----------------------------------------------------------------
	# Create NPZ file to save grid point subsets data and information
	#-----------------------------------------------------------------
	# path
	cwd = os.getcwd()
	path = cwd+'/Output/NPZ/Subsets/'
	fname = 'subset'	
	
	# list of output files
	if outlist:
		npz_file = path + outlist[index]
	else:
		npz_file = path + fname + str(index) + '.npz'

	#save subset data and parameters to npz files	
	np.savez(npz_file, parameters=parameters, point=point, Subsets=SubsetData)

def CreateSpectrumNPZ(args,pt):
	#-----------------------------------------------------------------
	# Create NPZ file to save grid point Spectrum and wavelength
	#-----------------------------------------------------------------
	# path
	cwd = os.getcwd()
	path = cwd+'/Output/NPZ/Spectrum/'
	fname = 'Spectrum'
	
	#file name 
	if args.output:
		npz_file = path + args.output
	else:
		num = re.findall('\d+', args.input)
		npz_file = path + fname + num + '.npz'
	
	#save point data	
	np.savez(npz_file, point=point)
	

def CreateImageParametersNPZ(parameters, ImageData):
	#----------------------------------------------------
	# Create NPZ file to save Image data and Information
	#----------------------------------------------------
	# path
	cwd = os.getcwd()
	path = cwd+'/Output/NPZ/Image/'
	
	#save image to npz file	
	filename = path + 'Image.npz'	
	np.savez(filename, ImageData=ImageData)
	
	#save parameters to npz file
	filename = path + 'parameters.npz'	
	np.savez(filename, parameters=parameters)
"""
