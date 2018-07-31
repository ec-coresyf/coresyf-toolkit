#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


"""
=====================================================================================================
Definition of all the classes used for Pre/post-processing, estimate spectrum and perform inversion
=====================================================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho 
 Date: July/2017
 Last update: Nov/2017
=====================================================================================================
CONTENT:
	ROI
		ROI_Parameters		ROI_Definition		GridPoints
		StoreIndices	

	IMAGE PROCESSING
		Coordinates			File_path_name		Processing_Parameters
		Spatial_Reference_System	GtiffInformation	

	SUBSETS

	SPECTRUM

	GLOBALPARAMETERS
	

"""
#
import	cv2 
# 
import cPickle as pickle
#
#**************************
#	ROI
#**************************
class ROI_Parameters:
	#------------------------------------------------------------
	# gather both image processing and ROI definition parameters
	#------------------------------------------------------------

	def __init__(self,  ImageParameters, ROI_Definition_Parameters, BathymetryParameters, Miscellaneous):
		self.ImageParameters =  ImageParameters; self.ROI_Definition_Parameters = ROI_Definition_Parameters;
		self.BathymetryParameters = BathymetryParameters; self. Miscellaneous = Miscellaneous;

class Miscellaneous:
	#------------------------------------------------------------
	# gather miscellaneous ROI parameters
	#------------------------------------------------------------	
	def __init__(self,  InterpolationMethod, CoastOrientation, Verbose):
		self.InterpolationMethod = InterpolationMethod; self.CoastOrientation = CoastOrientation;
		self.Verbose = Verbose;
	
class ROI_Definition:
	#-----------------------------------
	# gather ROI definition parameters
	#-----------------------------------
	def __init__(self,  PolygonFileName = '', PointsFileName = '' , GridResolution = 500):
		self.PolygonFileName = PolygonFileName; self.PointsFileName = PointsFileName; 
		self.GridResolution = GridResolution

class GridPoints:
	#-----------------------------------
	# gather Grid Points information
	#-----------------------------------
	def __init__(self, easting, northing, apriori_bathymetry=0):
		self.easting = easting; self.northing = northing; 
		self.apriori_bathymetry = apriori_bathymetry

class StoreIndices:
    def __init__(self):
        self.indices = []

    def select_point(self,event,x,y,flags,param):
            if event == cv2.EVENT_LBUTTONDOWN:
                #cv2.circle(image,(x,y),3,(255,0,0),-1)
                self.indices.append((x,y))

#***********************************
#	Bathymetry
#***********************************

class GridPointsData:
	#---------------------------------------------------------------------------------------------------------------
	# gather Grid points information coordinates, bathymetry(apriori and estimated), wavelength, spectrum, Tp,....
	#----------------------------------------------------------------------------------------------------------------
	def __init__(self, IndexEasting, IndexNorthing, easting, northing, apriori_bathymetry=0, Spectrum=None, wavelength=0, DiscriminationFlag=None, Tp=0, bathymetry=0):
		self.IndexEasting = IndexEasting; self.IndexNorthing = IndexNorthing; 
		self.easting = easting; self.northing = northing; 
		self.apriori_bathymetry = apriori_bathymetry
		self.Spectrum = Spectrum
		self.wavelength = wavelength
		self.DiscriminationFlag = DiscriminationFlag	
		self.Tp = Tp
		self.bathymetry = bathymetry
		

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)	

class BathymetryData:
	#---------------------------------
	# gather bathymetry data 
	#---------------------------------
	def __init__(self, Coordinates, Bathymetry):
		self. Coordinates =  Coordinates; self.Bathymetry =  Bathymetry;

class apriori:
	#-----------------------------------------------------
	# gather parameters for a priori bathy determination
	#-----------------------------------------------------
	def __init__(self, BathymetryParameters, MiscellaneousParameters):
		self.BathymetryParameters = BathymetryParameters; self.MiscellaneousParameters = MiscellaneousParameters
#***********************************
#	IMAGE PROCESSING
#***********************************
class ImageParameters:
	#------------------------------------------------------------
	# gather both image processing and ROI definition parameters
	#------------------------------------------------------------

	def __init__(self,  File_path_name, ProcessingParameters, SpatialReferenceSystem):
		self.File_path_name =  File_path_name; self.ProcessingParameters = ProcessingParameters;
		self.SpatialReferenceSystem = SpatialReferenceSystem

class Coordinates:
	#------------------------------------------------
	# gather northing/easting coordinates
	#------------------------------------------------
	def __init__(self, northing, easting):
		self.northing = northing; self.easting = easting

class File_path_name:
	#--------------------------------------------
	# gather input/output files path & name
	#--------------------------------------------
	def __init__(self, path_input='', fname_input='', path_output='', fname_output=''):
		self.path_input = path_input; self.fname_input = fname_input
		self.path_output = path_output; self.fname_output = fname_output

class Processing_Parameters:
	#--------------------------------------------
	# gather processing parameters and flag
	#--------------------------------------------
	def __init__(self, DataType='uint16',SlantRangeCorrection_Flag=False, ScaleFactor=1., ContrastStretch_Flag=False, LandMaskParameters=None, Band=1):
		self.DataType = DataType
		self.SlantRangeCorrection_Flag = SlantRangeCorrection_Flag	
		self.ScaleFactor =  ScaleFactor
		self.ContrastStretch_Flag = ContrastStretch_Flag
		self.LandMaskParameters = LandMaskParameters
		self.Band = Band
		
		
class Spatial_Reference_System:
	#------------------------------------------------------------
	# gather image system of reference input/output codes (EPSG)
	#------------------------------------------------------------

	def __init__(self,  EPSG_Flag_In="WGS84G", EPSG_Flag_Out="WGS84P"):
		self.EPSG_Flag_In =  EPSG_Flag_In; self.EPSG_Flag_Out = EPSG_Flag_Out

class GtiffInformation:
	#--------------------------------------------------------
	# gather Gtiff image information (projection/GCP/Metadata...)
	#--------------------------------------------------------
	def __init__(self, Metadata, ncols, nrows, GCPs, GCPs_projection, Geotransform, srs):
		self.Metadata = Metadata
		self.ncols = ncols
		self.nrows = nrows
		self.GCPs = GCPs
		self.GCPs_projection = GCPs_projection
		self.Geotransform = Geotransform
		self.srs = srs

class LandMaskParameters:
	#--------------------------------------------
	# gather processing parameters and flag
	#--------------------------------------------
	def __init__(self, LandMaskFlag=False, LandMaskFilePath='', LandMaskFileName='', FilterFlag=True):
		self.LandMaskFlag = LandMaskFlag;  self.LandMaskFilePath = LandMaskFilePath;
		self.LandMaskFileName = LandMaskFileName; self.FilterFlag = FilterFlag;


#***********************************
#		SUBSETS
#***********************************

class Subset:
	#------------------------------------------------
	# gather subset data (image + coordinates)
	#------------------------------------------------
	def __init__(self, CenterPoint, image, coordinates, resolution, FlagFlip):
		self.CenterPoint = CenterPoint; self.image = image; self.coordinates =  coordinates; 
		self.resolution =  resolution; self.FlagFlip = FlagFlip;

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)			


class SubsetTransferData:
	#--------------------------------------------------
	# gather parameters, subset, point data to transfer 
	#--------------------------------------------------
	def __init__(self, parameters=[], point=[], SubsetData=[]):
		self.parameters=parameters; self.point=point; self.SubsetData=SubsetData;

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)			


class SubsetDimension:
	#---------------------------------------------------------
	# gather subset dimension (range and dimension in pixels)
	#---------------------------------------------------------
	def __init__(self, DimensionPixel, DimensionMeters, BoxRange):
		self. DimensionPixel =  DimensionPixel; self.DimensionMeters =  DimensionMeters	
		self.BoxRange =  BoxRange	

class SubsetParameters:
	#---------------------------------
	# gather subset parameters 
	#---------------------------------
	def __init__(self, Point, DomainDimension=1000., FlagPowerofTwo=True, Shift=0.5, BoxNb=5):
		self. Point =  Point; self.DomainDimension =  DomainDimension	
		self.FlagPowerofTwo =  FlagPowerofTwo; self.Shift =  Shift	
		self. BoxNb =   BoxNb
	
#***********************************
#		SPECTRUM
#***********************************

class ComputingParameters:
	#-------------------------------------------------------------------------------------------------------------------------------------
	# gather parameters for subset Processing and Spectrum, main direction determination, Filter (Butterworth) and waves Spectra estimate 
	#--------------------------------------------------------------------------------------------------------------------------------------
	def __init__(self, SubsetProcessingParameters, DirectionEstimateParameters, FilterParameters, SpectrumParameters, InversionParameters):
		self.SubsetProcessingParameters = SubsetProcessingParameters; self.DirectionEstimateParameters = DirectionEstimateParameters;
		self.FilterParameters = FilterParameters; self.SpectrumParameters = SpectrumParameters; self.InversionParameters = InversionParameters;

class ComputingParametersSpectrum:
	#-------------------------------------------------------------------------------------------------------------------------------------
	# gather parameters for subset Processing and Spectrum, main direction determination, Filter (Butterworth) and waves Spectra estimate 
	#--------------------------------------------------------------------------------------------------------------------------------------
	def __init__(self, SubsetProcessingParameters, DirectionEstimateParameters, FilterParameters, SpectrumParameters):
		self.SubsetProcessingParameters = SubsetProcessingParameters; self.DirectionEstimateParameters = DirectionEstimateParameters;
		self.FilterParameters = FilterParameters; self.SpectrumParameters = SpectrumParameters;	

class SubsetProcessingParameters:
	#-------------------------------------------------
	# gather parameters for subset Processing  
	#-------------------------------------------------
	def __init__(self, IntensityType=32, ConstrastStretchFlag=False, MeanSubstractionFlag=True, PowerSpectrumFlag=True, DecibelRepresentationFlag=False):
		self.IntensityType = IntensityType; self.ConstrastStretchFlag = ConstrastStretchFlag;
		self.MeanSubstractionFlag = MeanSubstractionFlag; self.PowerSpectrumFlag = PowerSpectrumFlag; 
		self.DecibelRepresentationFlag = DecibelRepresentationFlag

class DirectionEstimateParameters:
	#---------------------------------------------------
	# gather parameters for main direction determination  
	#---------------------------------------------------
	def __init__(self, CoastNormalOrientation, masktype='circular', submethod='CentroidPower'):
		self.CoastNormalOrientation = CoastNormalOrientation; self.masktype = masktype; self.submethod=submethod;
 
class FilterParameters:
	#---------------------------------------------------
	# gather parameters for Butterworth Filtering  
	#---------------------------------------------------
	def __init__(self, FlagFilter=True, EllipseBigRadius=0.25, EllipseSmallRadius=0.1, Power=2):
		self.FlagFilter = FlagFilter; self.EllipseBigRadius = EllipseBigRadius; self.EllipseSmallRadius = EllipseSmallRadius; self.Power = Power; 

class WaveSpectrumParameters:
	#---------------------------------------------------
	# gather parameters for Waves Spectrum estimate  
	#---------------------------------------------------
	def __init__(self, SpectrumType = 'Waves', ProfileNumber=5, ProfileOffsetDistance=100., PaddingExtraPower=1, MeanMethod=1, PowerSpectrumFlag=True):
		self.SpectrumType = SpectrumType; self.ProfileNumber = ProfileNumber; self.ProfileOffsetDistance = ProfileOffsetDistance;
		self.PaddingExtraPower = PaddingExtraPower; self.MeanMethod = MeanMethod; self.PowerSpectrumFlag = PowerSpectrumFlag;

class WavelengthEstimationParameters:
	#--------------------------------------------------------------
	# gather all parameters for peakwavelength Estimation
	#--------------------------------------------------------------
	def __init__(self, PeakDeterminationMethod='CentroidPower', Power=5):
		self.PeakDeterminationMethod = PeakDeterminationMethod; self.Power = Power;

class SpectrumParameters:
	#---------------------------------------------------------------
	# gather parameters for Waves Spectrum and wavelength estimate  
	#---------------------------------------------------------------
	def __init__(self, WaveSpectrumParameters, WavelengthEstimationParameters):
		self.WaveSpectrumParameters = WaveSpectrumParameters; self.WavelengthEstimationParameters = WavelengthEstimationParameters;

class line:
	#-------------------------------------------------------
	# gather line information (slope, offset, 2D layout) 
	#-------------------------------------------------------
	def __init__(self, x, y, a, b):
		self.x = x ; self.y = y; self.a = a; self.b = b;
class edgepoint:
	#-------------------------------------------------------
	# gather intersection (line/image) points information
	#-------------------------------------------------------	
	def __init__(self, point1, point2):
		self.point1 = point1 ; self.point2 = point2;	
class dataline:
	#-------------------------------------------------------
	# gather series spectrum information
	#-------------------------------------------------------	
	def __init__(self, x, y, k, Spectrum, distance):
		self.x = x; self.y = y; self.k = k; self.Spectrum = Spectrum; self.distance = distance;
class offsetinformation:
	#-------------------------------------------------------
	# gather useful information for line Offset computation 
	#-------------------------------------------------------	
	def __init__(self, ProfileNumber, OffsetDistance, Direction, Resolution):
		self.ProfileNumber = ProfileNumber; self.OffsetDistance = OffsetDistance; 
		self.Direction = Direction; self.Resolution = Resolution;

class SpectrumData:
	#--------------------------------
	# gather spectrum standard Data 
	#--------------------------------
	def __init__(self, k, Spectrum):
		self.k = k; self.Spectrum = Spectrum; 

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)	

class SpectrumProcessedData:
	#---------------------------
	# gather spectrum Data 
	#---------------------------
	def __init__(self, k, Spectrum, StandardDeviation=0, Wavelength=0):
		self.k = k; self.Spectrum = Spectrum; 
		self.StandardDeviation=StandardDeviation; 
		self.Wavelength = Wavelength;
	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

class SpectrumComputedData:
	#--------------------------------
	# gather spectrum computed Data
	#---------------------------------
	def __init__(self, WaveDirection, WaveSpectrum, ImageSpectrum=None, SubsetData=None):
		self.WaveDirection = WaveDirection; self.WaveSpectrum = WaveSpectrum; 
		self.ImageSpectrum = ImageSpectrum; self.SubsetData = SubsetData;

#***********************************
#		INVERSION
#***********************************

class PeakParameters:
	#---------------------------------------------------------------
	# gather Peak determination Parameters for direction estimate
	#---------------------------------------------------------------	
	def __init__(self, power=2, ratio = 0.0):
		self.power = power; self.ratio = ratio

class DataPeak:
	#---------------------------------------------------------------
	# gather parameters for peak detection algorithm
	#---------------------------------------------------------------	
	def __init__(self, x, y):
		self.x = x; self.y = y

class HydrodynamicParameters:
	#---------------------------------------------------------------
	# gather Hydrodynamic parameters
	#---------------------------------------------------------------
		def __init__(self, tide=0, Tp=0, Hs=0):
			self.tide = tide; self.Tp = Tp; self.Hs = Hs;

class InversionParameters:
	#--------------------------------------------------------------
	# gather all parameters related to inversion
	#--------------------------------------------------------------
	def __init__(self, HydrodynamicParameters, InversionMethod='direct', WaveTheory='linear'):
		self.HydrodynamicParameters = HydrodynamicParameters; 
		self.InversionMethod = InversionMethod; 
		self.WaveTheory = WaveTheory;

		
class ComputationPoints:
	#--------------------------------------------------------------
	# gather grid points with depth to be estimated
	#--------------------------------------------------------------
	def __init__(self, GlobalPoints, QuasiDeepWaterPoints):
		self.GlobalPoints = GlobalPoints
		self.QuasiDeepWaterPoints = QuasiDeepWaterPoints

class ExceptionPoints:
	#--------------------------------------------------------------
	# gather deep or shallow water grid points 
	#--------------------------------------------------------------
	def __init__(self, DeepWaterPoints, ShallowWaterPoints):
		self.DeepWaterPoints = DeepWaterPoints
		self.ShallowWaterPoints = ShallowWaterPoints
	
class InversionData:
	#-----------------------------
	# gather inversion data
	#-----------------------------
	def __init__(self, InversionParameters, point):
		self.InversionParameters = InversionParameters; self.point=point;

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)		

#***********************************
#	GLOBAL PARAMETERS
#***********************************
class Global_Parameters:
	def __init__(self, ImageParameters, SubsetParameters, ComputingParameters):
		self.ImageParameters = ImageParameters; self.SubsetParameters = SubsetParameters;
		self.ComputingParameters = ComputingParameters;

	def pickle(self,fname):	
		with open(fname, 'wb') as f:
        		pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)		

