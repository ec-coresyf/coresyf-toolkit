#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
===============================================================================
IMAGE Library for image reading, processing and filtering

===============================================================================
 Authors: Florent Birrien and Alberto Azevedo and Francisco Sancho
 Date: June/2016
 Last update: Nov/2017
===============================================================================
CONTENT:
	READ IMAGE
		ReadSARImg

	IMAGE INFORMATION/COORDINATES
		GetNorthingEasting	GetImgSize	GetCoords	GetImRes
		GetImgType		GetProjImgInfo	GetEPSG

	IMAGE PROCESSING
		ImageCenter

		ScaleImage		ContrastStretch		ContrastStretch2	ImageContrastStretch
		SlantRangeGTiFF		SlantRangeCorrection

		LabelToString		ImageLabel

		UnibandTransform	Convert1BandTiff

		ReadGtiffRaster		GetGtiffInformation	CreateOutputGtiff	array2raster	CreateGTiFF

		ImagePadding		ResolutionPixels

	MASK
		CreateBandMask


"""

import os,sys,re
import glob
#
import argparse
import ConfigParser
#
import numpy as np
import matplotlib.pyplot as plt
#
import cv2
from skimage import exposure
from osgeo import gdal, osr
#
import CSAR_Classes as CL
import CSAR_Utilities as UT
import CSAR_ROI as ROI
#
from datetime import datetime
#
import warnings
warnings.filterwarnings("ignore")
#

###########################################################
#
#	    READ SAR IMAGE
#
###########################################################
def InputSubsetParameters():
	#-----------------------------------------------
	# Image Processing input parameters
	#-----------------------------------------------

	#input arguments
	parser = argparse.ArgumentParser(description='Co-ReSyF: SAR Bathymetry Research Application')
	#image
	parser.add_argument('-a', '--param', help='Parameters file for Wings (.ini file)', default='Config_Image.ini',required=False)
	parser.add_argument('-i', '--input', help='Input image (to be processed)', required=True)
	parser.add_argument('-b','--bathymetry', help='Bathymetric grid in a txt or npz file or ESRI shapefile',required=True)
	parser.add_argument('-p', '--processing', nargs='+', help='Image Processing Filters (Slant Range Correction, ContrastStretch)', default="contrast slant")
	#parser.add_argument('-ri', '--reference_system_in', help='Spatial Reference system EPSG code (Selected Image and Projection, cf. gdalinfo for image information and \
	#			http://spatialreference.org/ref/epsg/)', required=True)
	#parser.add_argument('-ro', '--reference_system_out', help='Spatial Reference system EPSG code (Selected Image and Projection, cf. gdalinfo for image information and \
	#			http://spatialreference.org/ref/epsg/)', required=True)

	#subscene
	parser.add_argument('-o', '--output', nargs='+', help='List with output file names (subsets#.out) for FFT determination (to be used by Wings)', required=False)
	parser.add_argument('-d', '--dimension', help='Dimension of the subscenes (meters, ideally 1000-2000m)', default=2000., required=False)
	parser.add_argument('-w', '--window', help='number of overlapping boxes for FFT computation', default=9, required=False)
	parser.add_argument('-s', '--shift', help='Overlapping boxes offset parameters for FFT computation. Values between (0.1-0.75). Default=0.5.',default=0.5, required=False)

	# peak wave period
	parser.add_argument('-T', '--Tp', help='mean peak wave period Tp', default=0, required=False)

	#comments
	parser.add_argument('-v','--verbose', help="comments and screen outputs", action="store_true")

	# store
	args = parser.parse_args()
	RunId = datetime.now().strftime('%Y%m%dT%H%M%S')


	# Get EPSG_in and ESPG_out from input image and grid, respectively (STeam):
	EPSG_In = GetDataProjectionSystem(args.input)
	EPSG_Out = UT.GetSpatialReferenceSystemFromGridShapefile(args.bathymetry)

	#create config.ini file
	parOut = open(args.param, "w"); Config = ConfigParser.ConfigParser(); Config.add_section("Arguments")
	#image
	Config.set("Arguments", "Input_image", args.input); Config.set("Arguments", "Bathymetry_file", args.bathymetry)
	Config.set("Arguments", "Image_processing_filters", args.processing)
	Config.set("Arguments", "Reference_systems", [EPSG_In, EPSG_Out])
	#subscene
	Config.set("Arguments", "Subscene_list", args.output); Config.set("Arguments", "Box_dimension", args.dimension)
	Config.set("Arguments", "Number_of_boxes", args.window); Config.set("Arguments", "Box_shift", args.shift)
	Config.add_section("Run")
	Config.set("Run", "Id", RunId)

	Config.write(parOut); parOut.close()

	# check which filters to apply
	Contrast_Stretch = True if (any("contrast" in s for s in args.processing) or any("contrast" in s for s in args.processing)) else False
	Slant_Correction = True if (any("slant" in s for s in args.processing) or any("Slant" in s for s in args.processing)) else False

	# store data in classes
	file_path_name = CL.File_path_name('', args.input, '', '')
	Point = np.zeros(2) + 1000; Point = Point.astype(int)
	LandMask_Parameters = CL.LandMaskParameters()
	ProcessingParameters = CL.Processing_Parameters('uint16',Slant_Correction, 1., Contrast_Stretch, LandMask_Parameters,1)
	SpatialReferenceSystem = CL.Spatial_Reference_System(EPSG_In, EPSG_Out)
	Subsetparameters = CL.SubsetParameters(Point, float(args.dimension), True, float(args.shift), int(float(args.window)))
	Image_Parameters = CL.ImageParameters(file_path_name, ProcessingParameters, SpatialReferenceSystem)

	return Subsetparameters, Image_Parameters, args, args.verbose

def ReadSARImg(parameters):

	#------------------------------------------------------------
	# Read/process SAR images and get related information
	#------------------------------------------------------------
	# define EPSG code according to frame of reference
	# (WGS84/4326: Geodesic, WGS84/32629: UTM zone 29N, ETRS89/3763: portugal projection)
	EPSG_in = GetEPSG(parameters.SpatialReferenceSystem.EPSG_Flag_In)
	EPSG_out = GetEPSG(parameters.SpatialReferenceSystem.EPSG_Flag_Out)

	# Input/Output path and files
	path_input = parameters.File_path_name.path_input; fname_input = parameters.File_path_name.fname_input;
	path_output = parameters.File_path_name.path_output;

	#path delimiter
	pattern ='/'
        if sys.platform=='win32':
                pattern =  '\\'
	#**************************
	# 	A) Raw image
	#**************************
	#-------------------------------------------------------------------------------------
	# PROCESS IMAGE

	# Get image specific format and dimension
	filein = fname_input; flin = path_input + filein;

	ImgType, ImgSize, ImgRes = GetImgType(flin), GetImgSize(flin), GetImRes(flin)

	# STeam commented this because these variables are never used
	#f, RasterBand, img = ReadGtiffRaster(flin,parameters.ProcessingParameters.DataType)

	# slant range correction
	if parameters.ProcessingParameters.SlantRangeCorrection_Flag:
		if (ImgType["ENVISAT"] or ImgType["ERS1/2"] or ImgType["GeoTIFF"]):
			fileout_slant  = fname_input[:-4]+"_Slant.tif"; fout = path_input + fileout_slant
			SlantRangeGTiFF(flin,fout)
			filein = fileout_slant

	# Scale image
	if parameters.ProcessingParameters.ScaleFactor!=1.:
		file_aux = filein[:-4].split(pattern)[-1]+"_scaled.tif"; flin = path_input + filein; fout = path_input + file_aux;
		dim = (int(ImgSize[1]*ScaleFactor), int(ImgSize[0]*ScaleFactor))
		if not os.path.isfile(fout):
			print "\nCreating an "+EPSG_flag+" image file..."
			os.system("gdalwarp -overwrite -srcnodata 0 -dstnodata 0 -r average -ts "+str(dim[0])+" "+str(dim[1])+" -t_srs EPSG:"+str(EPSG_in)+" "+flin+" "+fout)
		else:
			print file_aux," Already Exists..."
		filein = file_aux

	#-------------------------------------------------------------------------------------

	#**************************
	#  B) Projected image
	#**************************
	# IMAGE PROJECTION
	if EPSG_in != EPSG_out:
		file_aux = filein[:-4].split(pattern)[-1]+"_projected_EPSG"+str(EPSG_out)+".tif"; flin = path_input + filein; fout = path_output + file_aux;
		if not os.path.isfile(fout):
			os.system("gdalwarp -overwrite -srcnodata 0 -dstnodata 0 -r average -t_srs EPSG:"+str(EPSG_out)+" "+flin+" "+fout)
		else:
			print file_aux," Projected image Already Exists..."
		filein = file_aux
		path = path_output
	else:
		path = path_input
	# get Image type and dimensions
	flin = path + filein
	ImgType = GetImgType(flin); ImgSize = GetImgSize(flin);

	#-------------------------------------------------------------------------------------
	# GET IMAGE INFORMATION

	# get northing/easting and pixel resolution (m) from projected image
	northing, easting, res = GetProjImgInfo(flin)

	# gather all coordinates
	coordinates = CL.Coordinates(northing,easting)

	# read projected image and get raster image
	f, _, img = ReadGtiffRaster(flin)

	# close raster
	f = None
	#-------------------------------------------------------------------------------------
	# PROCESS IMAGE

	# stretch contrast (CS is the reference image)
	if parameters.ProcessingParameters.ContrastStretch_Flag:
		img = ImageContrastStretch(coordinates, img, flin, EPSG_out)
	else:
		flin = path + filein; fout = path_output + filein[:-4].split(pattern)[-1] + "_CS.tif"
		os.system("cp " + flin + " " + fout)

	#create land mask
	if parameters.ProcessingParameters.LandMaskParameters.LandMaskFlag:

		filename = filein[:-4].split(pattern)[-1]+"_Masked.tif"

		if not os.path.isfile(path+filename):
			# create image mask
			mask = CreateLandMask(flin, coordinates, parameters)
			ind = (mask>0)

			# save masked image
			array2raster(img, coordinates, EPSG_out, flin, path+filename)
		else:
			print filename," Masked image Already Exists..."
			f, _, mask = ReadGtiffRaster(path+filename); f = None;
			ind = (mask==0)

		# superpose mask on image
		img[ind] = 0
	else:
		LMaskFile = flin
		mask = img

	return coordinates, img, res


###########################################################
#
#		IMAGE INFORMATION
#
###########################################################

def GetNorthingEasting(filein):
	#---------------------------------------------
	# Get image coordinates
	#---------------------------------------------
	# image dimension
	ImgSize = GetImgSize(filein)
	# get domain corner coordinates
	Coords = GetCoords(filein)
	# initialization
	easting = np.zeros(ImgSize,dtype=np.float32)
	northing = np.zeros_like(easting)
	# get northing and easting
	North_vals = np.linspace(Coords[:,1].min(),Coords[:,1].max(),ImgSize[0])
	for i in xrange(ImgSize[0]):
		easting[i] = np.linspace(Coords[:,0].min(),Coords[:,0].max(),ImgSize[1])
		northing[i] = np.ones((ImgSize[1]))*North_vals[i]
 	northing = northing[::-1,:]
	return northing, easting

def GetImgSize(filein):
	#-------------------------
	# Get image dimension
	#-------------------------
	# gather image information using gdalinfo
	os.system("gdalinfo "+filein+" > Info_ImgSize.txt")
	# open file and read data
	fid = open("Info_ImgSize.txt", "r")
	data = fid.readlines()
	#find the dimension information
	for n,line in enumerate(data):
		if re.search("Size is ", line):
			LineSize=n
	y = np.int(data[LineSize].split(" is ")[1].split(",")[1])
	x = np.int(data[LineSize].split(" is ")[1].split(",")[0])
	#store dimension and close (remove) file
	ImgSize=[y,x]
	fid.close()
	os.system("rm -f Info_ImgSize.txt")
	return ImgSize

def GetCoords(filein):
	#-------------------------------------
	# Get corresponding image coordinates
	#-------------------------------------
	# gather image information using gdalinfo
	os.system("gdalinfo "+filein+" > Info_Coords.txt")
	# open file and read data
	fid = open("Info_Coords.txt", "r")
	data = fid.readlines()
	#find the corner points coordinates from information
	for n,line in enumerate(data):
		if re.match("Corner Coordinates:", line):
			LineCoords = n
	Coords = [  [np.float(data[LineCoords+1].split("(")[1].split(",")[0]),np.float(data[LineCoords+1].split("(")[1].split(",")[1].split(")")[0])],
        [np.float(data[LineCoords+2].split("(")[1].split(",")[0]),np.float(data[LineCoords+2].split("(")[1].split(",")[1].split(")")[0])],
        [np.float(data[LineCoords+3].split("(")[1].split(",")[0]),np.float(data[LineCoords+3].split("(")[1].split(",")[1].split(")")[0])],
        [np.float(data[LineCoords+4].split("(")[1].split(",")[0]),np.float(data[LineCoords+4].split("(")[1].split(",")[1].split(")")[0])]]

	#store dimension and close (remove) file
	fid.close()
	os.system("rm -f Info_Coords.txt")
	Coords = np.array(Coords)
	return Coords

def GetImRes(filein):
	#------------------------------------------------
	# Get the projected image resolution information
	#------------------------------------------------
	# gather image information using gdalinfo
	os.system("gdalinfo "+filein+" > Info_Coords.txt")
	# open file and read data
	fid = open("Info_Coords.txt", "r")
	data = fid.readlines()
	# get the x and y axis resolution from information
	for n,line in enumerate(data):
		if re.match("Pixel Size", line):
			LineRec = n
	line = data[LineRec]
	xres = round(np.float(line.split(",")[0].split("(")[1]),2)
	yres = round(np.abs(np.float(line.split(",")[1].split(")")[0])),2)
	ImgRes = [yres,xres]
	fid.close()
	os.system("rm -f Info_Coords.txt")
	return ImgRes


def GetImgType(filein):

	#------------------------------------------------
	# Get image format from gdal information
	#------------------------------------------------
	# gather image information using gdalinfo
	os.system("gdalinfo "+filein+" > Info_Type.txt")
	# open file and read data
	fid = open("Info_Type.txt", "r")
	data = fid.readlines()
	# look for format information
	for n,line in enumerate(data):
		if re.search("Driver:", line):
			type = line.split(":")[1].strip()

	ImgType = {"ERS1/2":False,"ENVISAT":False,"TSX":False,"GeoTIFF":False}

	if type == "ESAT/Envisat Image Format":
		ImgType["ENVISAT"] = True
	elif type == "SAR_CEOS/CEOS SAR Image":
		ImgType["ERS1/2"] = True
	elif type == "TSX/TerraSAR-X Product":
		ImgType["TSX"] = True
	elif type == "SAFE/Sentinel-1 SAR SAFE Product":
		ImgType["Sentinel1"] = True
	elif type == "GTiff/GeoTIFF":
		ImgType["GeoTIFF"] = True
	else:
		print "Unknown Driver..."
		pass
	# close & remove file and store format information
	fid.close()
	os.system("rm -f Info_Type.txt")
	return ImgType


def GetProjImgInfo(filein):
	#---------------------------------------------------------------------
	# Get the projected image resolution and easting/northing information
	#---------------------------------------------------------------------

	# get image resolution
	ImgRes = GetImRes(filein)

	# get projected coordinates
	Northing, Easting = GetNorthingEasting(filein)

	print "Image Resolution (northing/Easting): ",ImgRes

	return Northing, Easting, ImgRes

def GetEPSG(EPSG):

	#------------------------------------------------------------
	# Get EPSG code for input/output SAR images
	#------------------------------------------------------------
	return int(float(EPSG))


###########################################################
#
#	    IMAGE PROCESSING
#
###########################################################

def ImageCenter(img):
   	# image indices
   	y, x = np.indices(img.shape)

   	# estimate image center
   	center = np.array([(x.max()-x.min())/2.0, (x.max()-x.min())/2.0])

	return center

def ScaleImage(img, imgref):
	#------------------------------------------------------------
	# scale image to the selected format (8, 16 or 32 bits)
	#------------------------------------------------------------
	"""
	If type = 8 => dtype=np.uint8 => n_colors = 256 and range from 0 to 255
	If type = 16 => dtype=np.uint16 => n_colors = 65536 and range from 0 to 65535
	If type = 32 => dtype=np.float32 => n_colors = 1 and range from 0 to 1.
	"""
	typestr=str(imgref.dtype)
	if typestr == 'uint8':
		fac = 255.
	elif typestr == 'uint16':
		fac = 65536.
	elif typestr.find('float')>-1:
		fac = 1.

	img_new = np.array(img*fac/np.nanmax(img))

	return img_new.astype(imgref.dtype)


def ContrastStretch(img):
	#------------------------------------------------------------------
	# stretch image band (0->1, 0->255,...) depending on image format
	#------------------------------------------------------------------

	# equalize image histogram
	choice = 3

	if choice == 1:
		p2 = np.percentile(img, 2)
		p98 = np.percentile(img, 98)
		typestr=str(img.dtype)
		imgf = img_as_float(img) if typestr.find('float')>0 else img
		try:
			img_eq = exposure.rescale_intensity(imgf, in_range=(p2, p98), dtype=imgf.dtype)
		except:
			img_eq = exposure.rescale_intensity(imgf, in_range=(p2, p98))
	elif choice == 2:
		typestr=str(img.dtype)
		imgf = img_as_float(img) if typestr.find('float')>0 else img
		try:
			img_eq = exposure.equalize_hist(imgf, dtype=imgf.dtype)
		except:
			img_eq = exposure.equalize_hist(imgf)
	elif choice == 3:
		typestr=str(img.dtype)
		imgf = img_as_float(img) if typestr.find('float')>0 else img
		try:
			img_eq = exposure.equalize_adapthist(imgf, clip_limit=0.03, dtype=imgf.dtype)
		except:
			img_eq = exposure.equalize_adapthist(imgf, clip_limit=0.03)
	elif choice == 4:
		img_eq = (img - np.min(img)) / (np.max(img) - np.min(img))

	#figure (control)
	flagplot=0

	if flagplot > 0:
		fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(2,2)
		ax1.imshow(img, aspect='auto', cmap=plt.get_cmap('gray'))
		ax2.hist(img.ravel(),100)
		ax3.imshow(img_eq, aspect='auto', cmap=plt.get_cmap('gray'))
		ax4.hist(img_eq.ravel(),100)
		plt.show()

   	return img_eq


def ImageContrastStretch(coordinates, img, filein, EPSG, Band=1):
	#---------------------------------------------------------------------
	# stretch contrast of the image according to its type and save raster
	#---------------------------------------------------------------------

	# look if the file already exits
        pattern ='/'
        if sys.platform=='win32':
                pattern =  '\\'

	path = pattern.join(filein.split(pattern)[:-1]); pathf ='' if path=='' else  path + pattern # detect path
	fileext =  pathf + filein[:-4].split(pattern)[-1]; ext = "_CS.tif";  fileCS = glob.glob(fileext + ext) #output path

	if len(fileCS)==0:
		#A create file if it does not exist
		# Stretch contrast
		img = ScaleImage(ContrastStretch(img),img)
		#consider 1st band if multiband gray image
		if len(img.shape)==3:
			img = img[Band-1,:,:]

		# create the Gtiff output file
		fout = fileext + ext
		array2raster(img, coordinates, EPSG, filein, fout)
		f, RasterBand, _ = ReadGtiffRaster(fout)

	else:
		#B read Gtiff raster if file exist
		f, RasterBand, img = ReadGtiffRaster(fileCS[0])

		#consider 1st band if multiband gray image
		if len(img.shape)==3:
			img = img[Band-1,:,:]
	f= None

	return img

def SlantRangeGTiFF(filein,fileout):
	#------------------------------------------------------------
	# Perform slant range correction and create corrected image
	#------------------------------------------------------------

	# open file and get information
	img, Info = GetGtiffInformation(filein)
	# image processing
	img1 = ContrastStretch(img)		# stretch contrast
	img2 = SlantRangeCorrection(img1)	# Slant Range correction
	imgr = ScaleImage(img2, img)		# image scaling according to type
	# create Gtiff output image
	CreateOutputGtiff(imgr, fileout, Info)

	return None

def SlantRangeCorrection(img):

	#---------------------------------------------
	# perform slant range correction
	#---------------------------------------------
	fac = 0.15
	# get mean pixel intensity line (column-wise)
	slant_profile=np.mean(img, axis=0)

	# define filtering window according to image width
	width=img.shape[1]
	window=int(width*fac)

	# estimate intensity extremum value at the line (image) edge
	s_min,smax = np.nanmean(slant_profile[:window]), np.nanmean(slant_profile[-window:])

	# create correction vector
	slant_corr=np.linspace(s_min,smax,num=slant_profile.shape[0])
	slant_corr=slant_corr[::-1]

	#apply correction to the whole image
	img_corr=img*slant_corr[:,np.newaxis].transpose()

	return img_corr


def UnibandTransform(img,band):
	#------------------------------------------------------------------
	# convert multi-band raster into mono-band raster
	#------------------------------------------------------------------
	nb, nx, ny = img.shape

	if band < 4:
		img2 = img[band,:,:]
	else:
		img2 = np.mean(img[0:nb-1,:,:],0)

	img = img2
	return img

def Convert1BandTiff(filein,band):
	#------------------------------------------------------------------
	# write mono-band raster into GeoTiff file
	#------------------------------------------------------------------
	#file extension
	ext='.tif'

	# check nb of bands in input file
	f = gdal.Open(filein)
	RC = f.RasterCount
	print 'nb of band in input raster:', RC
	f = None

	#file name without extension
	filei = filein.split(ext,1)[0]
	# process image if multi-band
	if RC > 1:
		fileout = filei + '_processed' + ext
		CreateGTiFF(filein,fileout,band,EPSG=4326)
	return fileout


def ReadGtiffRaster(filein):

	# read projected image and get rasterband
	f = gdal.Open(filein); a = f.GetRasterBand(1)
	raster = f.ReadAsArray(0, 0, a.XSize, a.YSize)

	# reconstitute image from raster
	img = raster.astype(np.uint16) if str(raster.dtype).find('uint')>-1 else raster.astype(np.float32)

	# exceptions
	if (str(img.dtype)=='float32' and np.max(img)>1.):
		img=img/np.max(img)

	return f, a, img

def GetGtiffInformation(filein,EPSG=0):

	# open file and get information
	f, a, img = ReadGtiffRaster(filein)

	# metadata
	Metadata = f.GetMetadata()

	# dimension
	ncols, nrows = a.XSize, a.YSize

	# ground control points
	GCPs = f.GetGCPs()
	GCPs_projection = f.GetGCPProjection()

	# transformation info (coordinates and resolution)
	Geotransform = f.GetGeoTransform()

	# projection info (spatial reference system (EPSG related))
	if EPSG == 0:
		srs = osr.SpatialReference(wkt=f.GetProjection())
	else:
		srs = osr.SpatialReference(); srs.ImportFromEPSG(EPSG)

	#store information
	Infos = CL.GtiffInformation(Metadata, ncols, nrows, GCPs, GCPs_projection, Geotransform, srs)

	#deallocate raster
	f = None

	return img, Infos

def CreateOutputGtiff(img, fileout, GtiffInformation):

	#create the output Gtiff file
	ncols = GtiffInformation.ncols; nrows = GtiffInformation.nrows;
	output_raster = gdal.GetDriverByName('GTiff').Create(fileout,ncols, nrows, 1 ,gdal.GDT_Byte)  # Open the file

	# specify geotransform information (coordinates)
	output_raster.SetGeoTransform(GtiffInformation.Geotransform)

	# Ground Control Points information
	output_raster.SetGCPs(GtiffInformation.GCPs, GtiffInformation.GCPs_projection)

	#Metadata
	output_raster.SetMetadata(GtiffInformation.Metadata)

	# projection information
	output_raster.SetProjection( GtiffInformation.srs.ExportToWkt() )


	#print GtiffInformation.Metadata
	# write array in raster
	output_raster.GetRasterBand(1).WriteArray(img)
	output_raster.GetRasterBand(1).SetNoDataValue(0) # exception (dark)


	# deallocate raster
	output_raster = None;

	return None

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
	img=ScaleImage(img, img)

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
	Geotransform = (xmin,xres,0,ymax,0, -yres);
	Infos = CL.GtiffInformation(Info.Metadata, Info.ncols, Info.nrows, Info.GCPs, Info.GCPs_projection, Geotransform, Info.srs)

	#create output raster
	CreateOutputGtiff(img, fileout, Infos)

	return None


def CreateGTiFF(filein,fileout,band,EPSG=4326):

	# read Gtiff image and get information
	img, Info = GetGtiffInformation(filein)

	# image processing
	img = UnibandTransform(img,band)
	img = ScaleImage(img,img)

	# create output raster
	CreateOutputGtiff(img, fileout, Info)

	return None


def ImagePadding(parameters,subset):
	#---------------------------
	# perform image padding
	#---------------------------
	# image, dimension and center
	image = subset.image; dimension = image.shape; center = ImageCenter(image); center = center.astype(int)

	# closest power of 2 of image dimension
	power = Powerof2(image);

	# new dimension
	dimx = 2**(power[0]+parameters.ImagePadding); dimy = 2**(power[1]+parameters.ImagePadding);
	dimx = dimx.astype(int); dimy = dimy.astype(int);

	# new image and center
	Image = np.zeros((dimx,dimy))+np.mean(image); C =ImageCenter(Image); C = C.astype(int);


	# paste subset image in padding image
	indx = C[0]-center[0]; indy = C[1]-center[1];
	Image[indx:indx+dimension[0], indy:indy+dimension[1]]  = image

	return Image

def ResolutionPixel(parameters, data):
	#--------------------------------------------------------------------------------------------------------
	#
	# Estimate Resolution in Pixels corresponding to the user defined input grid resolution (rough estimate)
	# and re-estimate the grid Resolution
	#
	#--------------------------------------------------------------------------------------------------------
	# user-defined resolution
	ResolutionMeters = parameters.ROI_Definition_Parameters.GridResolution

	# image resolution(m/pix)
	ImageResolution = data.resolution

	# estimate grid resolution in pixel
	res = ResolutionMeters/ImageResolution[0];
	ResolutionPixels = np.round(res)
	ResolutionPixels = ResolutionPixels.astype(int)

	# re-estimate Grid Resolution
	ResolutionMeters = ResolutionPixels*ImageResolution[0]

	print 'Grid Resolution (px) vs (m)', ResolutionPixels, ResolutionMeters

	return ResolutionPixels, ResolutionMeters

def CheckImageOrientation(coordinates):
	#-------------------------------------------------------------------------------------------
	# check if image has been flipped by SAR preprocessor (to get right coastline orientation)
	# remark: it may affect direction estimate
	#-------------------------------------------------------------------------------------------
	# load coordinates
	northing = coordinates.northing[:,0]; easting = coordinates.easting[0,:];

	# check axis direction
	flagN = False; flagE=False
	if northing[0] > northing[-1]:
		flagN = True
	if easting[0] > easting[-1]:
		flagE = True

	# flag to determine whether the preprocessing flip will affect the direction estimate
	if flagN == flagE:
		flag = False
	else:
		flag = True

	return flag

###########################################################
#
#		LAND MASK
#
###########################################################
def CreateLandMask(filein, coordinates_image, parameters):
	#-----------------------------------------------------
	# create Land Mask using selected topography file
	#-----------------------------------------------------
	#*******************************************************
	# 0) get information on the output system of reference
	#*******************************************************
	EPSG_out = GetEPSG(parameters.SpatialReferenceSystem.EPSG_Flag_Out)
	kernel = np.ones((5,5),np.uint8)
	#**************************
	# A) band mask from image
	#**************************

	mask = CreateBandMask(filein)
	indexS = (mask>0); indexM = (mask==0)
	mask[indexS] = 0; mask[indexM] = 255										# create band mask
	northing, easting = GetNorthingEasting(filein)									# retrieve coordinates
	coordinates_image = CL.Coordinates(northing[:,0], easting[0,:])

	#process / dilate mask edge
	if parameters.ProcessingParameters.LandMaskParameters.FilterFlag:
		mask = cv2.dilate(mask, kernel,iterations = 2)

	# save raster to temporary file
	fileout_image = 'ImageMask.tif'; array2raster(mask, coordinates_image, EPSG_out, filein, fileout_image)

	#******************************
	# B) band mask for topography
	#******************************

	# read topography file
	Coordinates, Topography = ReadTopography(parameters)						#read topography

	# collocated topography
	coordinates, topography = ROI.CollocatedData(coordinates_image, Coordinates, Topography)	# find collocated topography (reference: image coordinates)
	indexS = (topography==0); indexL = (topography!=0)						# distinguish between
	topography[indexS] = 0; topography[indexL]  = 255						# create mask

	#process / dilate mask edge
	if parameters.ProcessingParameters.LandMaskParameters.FilterFlag:
		topography = cv2.dilate(topography, kernel,iterations = 2)

	# create mask raster
	fileout_mask='TopographyMask.tif'; array2raster(topography, coordinates, EPSG_out, filein, fileout_mask)

	#*********************
	# C) merge both masks
	#*********************
	filename = fileout_image								# the mask is pasted into the image mask file (mandatory for gdal_merge to keep dimensions)
	os.system("gdal_merge.py -n 0. -o "+fileout_image+" "+fileout_mask+" "+ filename)	# merge mask image using gdal_merge
	f, _, finalmask = ReadGtiffRaster(filename); f = None;			# read mask
	os.system("rm"+" "+fileout_mask+" "+fileout_image)					# clean directory


	"""
	#--------
	# figure
	#--------

	fig, (ax1,ax2,ax3) = plt.subplots(3)
	# image mask
	E = coordinates_image.easting; N = coordinates_image.northing;
	ax1.imshow(mask, cmap=plt.cm.jet, interpolation=None, aspect='auto', origin='upper', extent = [np.min(E), np.max(E), np.min(N), np.max(N)])

	# topography mask
	E = coordinates.easting; N = coordinates.northing;
	ax2.imshow(topography, cmap=plt.cm.jet, interpolation=None, aspect='auto', origin='upper', extent = [np.min(E), np.max(E), np.min(N), np.max(N)])

	#merge mask
	E = coordinates_image.easting; N = coordinates_image.northing;
	ax3.imshow(finalmask, cmap=plt.cm.jet, interpolation=None, aspect='auto', origin='upper', extent = [np.min(E), np.max(E), np.min(N), np.max(N)])


	plt.show()
	"""

	return finalmask



def CreateBandMask(filein):
	#-----------------------------------------------------
	# create mask from processed projected file
	#-----------------------------------------------------
	# get informtation from last processed image
	f, a, img = ReadGtiffRaster(filein)

	#bandmask
	BandMask = a.GetMaskBand()

	#create mask
	mask = BandMask.ReadAsArray()

	# deallocate raster
	f = None

	return mask

def ReadTopography(parameters):
	#-----------------------------------------------------
	# Read Topography file to extract
	#-----------------------------------------------------
	parameter = parameters.ProcessingParameters.LandMaskParameters
	filename = parameter.LandMaskFileName; path_input = parameter.LandMaskFilePath; path_output=parameters.File_path_name.path_output
	pattern ='/'
        if sys.platform=='win32':
                pattern =  '\\'

	# get projection information
	EPSG_in = GetDataProjectionSystem(path_input+filename)

	# reproject topography in the selected output reference coordinate system
	EPSG_out = GetEPSG(parameters.SpatialReferenceSystem.EPSG_Flag_Out)

	if EPSG_in != EPSG_out:
		file_aux = filename[:-4].split(pattern)[-1]+"_projected_EPSG"+str(EPSG_out)+".tif"; flin = path_input + filename; fout = path_output + file_aux;
		if not os.path.isfile(fout):
			os.system("gdalwarp -overwrite -srcnodata 0 -dstnodata 0 -r average -t_srs EPSG:"+str(EPSG_out)+" "+flin+" "+fout)
		else:
			print file_aux," Already Exists..."
		flin = file_aux
		path = path_output
	else:
		path = path_input

	# read raster
	filename= path + flin
	f, _, topography = ReadGtiffRaster(filename)
	f = None

	# process exception
	topography[np.isnan(topography)] = 0

	# get Coordinates
	northing, easting = GetNorthingEasting(filename)
	coordinates = CL.Coordinates(northing[:,0], easting[0,:])

	return coordinates, topography

def GetDataProjectionSystem(filename):
	#-----------------------------------------------------
	# get image spatial reference system using gdalinfo
	#-----------------------------------------------------
	os.system("gdalinfo "+filename+" > Info_Coords.txt")
	# open file and read data
	fid = open("Info_Coords.txt", "r")
	data = fid.readlines()
	for n,line in enumerate(data):
		if line.find("EPSG")>0:
			LineRec = n

	EPSG = re.findall('\d+', data[LineRec])[0]
	try:
		ESPG = int(EPSG)
	except:
		sys.exit("Error. Unable to get EPSG code from '%s'!" % filename)
	return EPSG
