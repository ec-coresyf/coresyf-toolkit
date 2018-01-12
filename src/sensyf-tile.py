#!/usr/bin/python
# -*- coding: utf-8 -*-

# ============================================================================
# $Id$
#
# $Revision$
# $Date$
# $LastChangedBy$
# ============================================================================
# DESCRIPTION
# ============================================================================
# PROJECT       : SenSyF
# COMPANY       : DEIMOS Engenharia S.A.
# COMPONENT     : Data Processing
# LANGUAGE      : Python
# ----------------------------------------------------------------------------
# PURPOSE
#
# This file contains the development of the sensyf-tile command.
# The command sensyf-tile generates tiles of GeoTIFF products according to 
# an input tile size and an optional offset pixels. The tool also supports
# SENTINEL-1 data (sensyf-tile >= 1.2.0).
#
# CHANGELOG
#
# 1.2.0
# - Update to support Sentinel-1 data.
#
# 1.1.0
# - Change of the flag -r <resolution> to -s <tile_size>.
# - Improvement of the flag -s to generate rectangular tiles (-s tile_width tile_height).
# - Addition of the flag -v or --version (to check the version of the tool).
# - Addition of the flag -h or -- help (to check how the tool works).
# - Change of the message shown when the command is wrong.
# - Addition of the flag -od (outputs on the destination directory without
#   any organization.
# - Addition of the flag -ullr (to select a working window - Xmin,Ymin;
#   Xmax,Ymax - to be tiled).
#
# 1.0.0
# - First release of sensyf-tile.
# ========================================================================== #

import os
import sys
from osgeo import gdal,gdal_array, ogr
import glob
import shutil
from xml.dom import minidom

#!                                                                                                                                                                                
# The function getNodeText gets the value of a node on
# the application.xml file.
#
# @param[in] node
#      Node to get the value
#
# @return
#      Text value correspondent to the node
#!

def getNodeText(node):

  nodelist = node.childNodes
  result = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      result.append(node.data)
  return ''.join(result)

#!
# The tile_S1_data function generates tiles for the Sentinel-1 products with a                                                                                                         
# tile size and with an offset of pixels, both given by argument.
# The outputs will be organized by product (default), by using the flag -od, the
# output tiles will be placed on the output directory without any organization
# and by using the flag -ot the outputs will be organized by tile.
#
# @param[in] xsize                                                                                                                                                            
#      Intended tile width
# @param[in] ysize                                                                                                                                                            
#      Intended tile height
# @param[in] offset
#      The number of the offset pixels that should be considered for each tile
# @param[in] ulx                                                                                                                                                            
#      Upper Left X coordinate of the working window
# @param[in] uly                                                                                                                                            
#      Upper Left Y coordinate of the working window
# @param[in] lrx                                                                                                                                            
#      Lower Right X coordinate of the working window
# @param[in] lry                                                                                                                                           
#      Lower Right Y coordinate of the working window
# @param[in] inputFilePath                                                                                                                                                              
#      Filepath to the input S1 product                                                                                                                  
# @param[in] dstDir                                                                                                                                                                
#      The path of the output directory        
# @param[in] od                                                                                                                                          
#      Variable to check the activation of the flag -od                                                                                                                                            
#                                                                                                                                                                                  
# @return                                                                                                                                                                          
#      There are no returns for this function                                                                                                                                      
#!

def tile_S1_data(xsize, ysize, offset, ulx, uly, lrx, lry, inputFilePath, dstDir, od):

  annotation_file = glob.glob(inputFilePath + '/annotation/*.xml')[0]
  doc = minidom.parse(annotation_file)
  width = int(getNodeText(doc.getElementsByTagName("numberOfSamples")[0]))
  height = int(getNodeText(doc.getElementsByTagName("numberOfLines")[0]))

  inputProduct = os.path.basename(inputFilePath)
  inputFileName, extension = os.path.splitext(inputProduct)
  inputFilePath = inputFilePath + '/manifest.safe'

  if os.path.exists(str(os.environ['NEST_HOME']) + '/gpt.sh'):
    gpt_path = str(os.environ['NEST_HOME']) + '/'
  else:
    print "\nError: gpt.sh file not found. Set environment variable 'NEST_HOME' with the correct directory where is gpt.sh file."
    return

  tmp_subset = './subset_of_' + inputFileName + '.tif'
  if (ulx != 0) or (uly != 0) or (lrx != 0) or (lry != 0):
    ullon = ulx
    ullat = uly
    lrlon = lrx
    lrlat = lry
    print '\nCreating the working window defined...'
    os.system(gpt_path + 'gpt.sh Subset ' + inputFilePath + ' -t ' +  tmp_subset + ' "-PgeoRegion=POLYGON((' + str(ullon) + ' ' + str(ullat) + ', ' + str(lrlon) + ' ' + str(ullat) + ', ' + str(lrlon) + ' ' + str(lrlat) + ', ' + str(ullon) + ' ' + str(lrlat) + ', ' + str(ullon) + ' ' + str(ullat) + '))"')
    inputFilePath = tmp_subset
    inputProduct = os.path.basename(inputFilePath)
    inputFileName, extension = os.path.splitext(inputProduct)
    if not os.path.exists(tmp_subset):
      return
    ds = gdal.Open(inputFilePath)
    width = ds.RasterXSize
    height = ds.RasterYSize
    print '\nWorking window created.\n'

  if (od == 0):
    outputDir = dstDir + '/' + inputFileName + '/'
    if os.path.exists(outputDir):
      shutil.rmtree(outputDir)
      os.makedirs(outputDir)
    else:
      os.makedirs(outputDir)
  else:
    outputDir = dstDir + '/'

  print '\nTiling ' + inputProduct + '...'

  height_last_tile = int((height/float(ysize)-(height/ysize))*ysize)
  width_last_tile = int((width/float(ysize)-(width/ysize))*xsize)

  if height_last_tile <= offset:
    num_tiles_row = height/ysize
  else:
    num_tiles_row = height/ysize + 1
  if width_last_tile <= offset:
    num_tiles_column = width/xsize
  else:
    num_tiles_column = width/xsize + 1

  regionY = 0
  for i in range(num_tiles_row):
    regionX = 0
    for j in range(num_tiles_column):
      outputFilePath = outputDir + inputFileName + '_' + str(regionX) + '_' + str(regionY) + '.tif'
      os.system(gpt_path + 'gpt.sh Subset ' + inputFilePath + ' -PregionX=' + str(regionX) + ' -PregionY=' + str(regionY) + ' -Pwidth=' + str(xsize+offset) + ' -Pheight=' + str(ysize+offset) + ' -t ' + outputFilePath)
      regionX = regionX + xsize
    regionY = regionY + ysize

  if os.path.exists(tmp_subset):
    os.remove(tmp_subset)

  print 'Tiling process for product ' + inputProduct + ' complete.\n'

#!
# The tile_default_od function generates tiles of the input products with a                                                                                                         
# tile size and with an offset of pixels, both given by argument.
# The outputs will be organized by product (default) or, by using the flag -od,
# the output tiles will be placed on the output directory without any organization.
#
# @param[in] xsize                                                                                                                                                            
#      Intended tile width
# @param[in] ysize                                                                                                                                                            
#      Intended tile height
# @param[in] offset
#      The number of the offset pixels that should be considered for each tile
# @param[in] ulx                                                                                                                                                            
#      Upper Left X coordinate of the working window
# @param[in] uly                                                                                                                                            
#      Upper Left Y coordinate of the working window
# @param[in] lrx                                                                                                                                            
#      Lower Right X coordinate of the working window
# @param[in] lry                                                                                                                                           
#      Lower Right Y coordinate of the working window
# @param[in] fileList                                                                                                                                                              
#      The vector containing the filepaths for all input products                                                                                                                  
# @param[in] dstDir                                                                                                                                                                
#      The path of the output directory        
# @param[in] od                                                                                                                                          
#      Variable to check the activation of the flag -od
#                                                                                                                                                                           
# @return                                                                                                                                                                          
#      There are no returns for this function                                                                                                                                      
#!                                       

def tile_default_od(xsize, ysize, offset, ulx, uly, lrx, lry, fileList, dstDir, od):

  for f in range(len(fileList)):
    inputFilePath = fileList[f]
    inputProduct = os.path.basename(inputFilePath)
    outputDir = dstDir + '/'
    first_time = 1

    inputFileName, extension = os.path.splitext(inputProduct)

    if len(extension) == 0:
      if os.path.isdir(inputFilePath):
	extension = 'dir'
      else:
	extension = 'no_extension'

    if (extension.lower() == '.safe') and (os.path.isdir(inputFilePath)):
      tile_S1_data(xsize, ysize, offset, ulx, uly, lrx, lry, inputFilePath, dstDir, od)

    elif (extension.lower() == '.tif') or (extension.lower() == '.tiff') or (extension == 'no_extension'):

      vector = get_new_off_coordinates(inputFilePath, inputProduct, xsize, ysize, offset, ulx, uly, lrx, lry, first_time)
     
      if vector[6] == 0: # left_product variable 0 - ok, 1 - no tile
	print '\nTiling ' + inputProduct + '...'
	if od == 0:
	  outputDir = outputDir + inputFileName + '/'
	  if os.path.exists(outputDir):
	    shutil.rmtree(outputDir)
	    os.makedirs(outputDir)
	  else:
	    os.makedirs(outputDir)

	for i in range(int(vector[0])):
	  for j in range(int(vector[1])):
	    tile_xoff = vector[2]+(j*xsize*vector[4])
	    tile_yoff = vector[3]+(i*ysize*vector[5])
	    tile_xend = vector[2]+((j+1)*xsize+offset)*vector[4]
	    tile_yend = vector[3]+((i+1)*ysize+offset)*vector[5]
	  
	    if extension == 'no_extension':
	      outputFilePath = outputDir + inputFileName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff))
	    else:
	      outputFilePath = outputDir + inputFileName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + extension
	    os.system('gdal_merge.py -o ' + outputFilePath + ' -of GTiff -ul_lr ' + str(tile_xoff) + ' ' + str(tile_yoff) + ' ' + str(tile_xend) + ' ' + str(tile_yend) + ' -q ' + inputFilePath)
      
	print 'Tiling process for product ' + inputProduct + ' complete.\n'

    elif extension == 'dir':

      if od == 0:
	productDir = outputDir + inputFileName + '/'
	if os.path.exists(productDir):
	  shutil.rmtree(productDir)
	  os.makedirs(productDir)
	else:
	  os.makedirs(productDir)

      listInDir = glob.glob(inputFilePath + "/*")

      for b in range(len(listInDir)):
	inputBandName, extension = os.path.splitext(os.path.basename(listInDir[b]))
	if (extension.lower() == '.tif') or (extension.lower() == '.tiff'):

	  if od == 0:
	    os.makedirs(productDir + inputBandName + '/')
	    outputDir = productDir + inputBandName + '/'      

	  vector = get_new_off_coordinates(listInDir[b], inputProduct, xsize, ysize, offset, ulx, uly, lrx, lry, first_time)
	  if first_time == 1 and vector[6] == 0:
	    print  '\nTiling ' + inputProduct + '...'
	  first_time = 0
	  if vector[6] == 0: # left_product variable 0 - ok, 1 - no tile
	    for i in range(int(vector[0])):
	      for j in range(int(vector[1])):
		tile_xoff = vector[2]+(j*xsize*vector[4])
		tile_yoff = vector[3]+(i*ysize*vector[5])
		tile_xend = vector[2]+((j+1)*xsize+offset)*vector[4]
		tile_yend = vector[3]+((i+1)*ysize+offset)*vector[5]

		outputFilePath = outputDir + inputBandName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + extension
		os.system('gdal_merge.py -o ' + outputFilePath + ' -of GTiff -ul_lr ' + str(tile_xoff) + ' ' + str(tile_yoff) + ' ' + str(tile_xend) + ' ' + str(tile_yend) + ' -q ' + listInDir[b])
      if vector[6] == 0:
	print 'Tiling process for product ' + inputProduct + ' complete.\n'
      else:
	if od == 0:
	  shutil.rmtree(productDir)

    else:

      print '\nError: Input product ' + inputProduct + ' got unknown format\n'

#!
# The tile_organized_by_tile function generates tiles of the input products, with a
# tile size and with an offset of pixels, both given by argument.
# The outputs are organize by tile.
#
# @param[in] xsize                                                                                                                                                            
#      Intended tile width
# @param[in] ysize                                                                                                                                                            
#      Intended tile height
# @param[in] offset
#      The number of the offset pixels that should be considered for each tile
# @param[in] ulx                                                                                                                                                            
#      Upper Left X coordinate of the working window
# @param[in] uly                                                                                                                                            
#      Upper Left Y coordinate of the working window
# @param[in] lrx                                                                                                                                            
#      Lower Right X coordinate of the working window
# @param[in] lry                                                                                                                                           
#      Lower Right Y coordinate of the working window
# @param[in] fileList                                                                                                                                                              
#      The vector containing the filepaths for all input products                                                                                                                  
# @param[in] dstDir                                                                                                                                                                
#      The path of the output directory
#
# @return
#      There are no returns for this function
#!

def tile_organized_by_tile(xsize, ysize, offset, ulx, uly, lrx, lry, fileList, dstDir):

  for f in range(len(fileList)):
    left_product = 0
    inputFilePath = fileList[f]
    inputProduct = os.path.basename(inputFilePath)
    outputDir = dstDir + '/'

    inputFileName, extension = os.path.splitext(inputProduct)

    if len(extension) == 0:
      if os.path.isdir(inputFilePath):
	extension = 'dir'
      else:
	extension = 'no_extension'

    if (extension.lower() == '.safe') and (os.path.isdir(inputFilePath)):
      print '\nError: The organization by tile (-ot) is not available to SENTINEL-1 data.\n'

    elif (extension.lower() == '.tif') or (extension.lower() == '.tiff') or (extension == 'no_extension'):

      inputFile = gdal.Open(inputFilePath)
      width = inputFile.RasterXSize
      height = inputFile.RasterYSize
      transform = inputFile.GetGeoTransform()
      pixel_size_x = transform[1]
      pixel_size_y = transform[5]*(-1)
      data_x_off = transform[0]
      data_y_off = transform[3]
      data_x_end = transform[0] + width*transform[1] + height*transform[2]
      data_y_end = transform[3] + width*transform[4] + height*transform[5] 

      if (ulx != 0) or (uly != 0) or (lrx != 0) or (lry != 0):
	if (lrx < data_x_off) or (ulx > data_x_end) or (uly < data_y_end) or (lry > data_y_off):
	  print '\n' + inputProduct + ' does not intersect the working window area.'
	  left_product = 1
	else:
	  if ulx > data_x_off:
	    data_x_off = ulx
	  if lrx < data_x_end:
	    data_x_end = lrx
	  if uly < data_y_off:
	    data_y_off = uly
	  if lry > data_y_end:
	    data_y_end = lry
      
      if left_product == 0:
	print '\nTiling ' + inputProduct + '...'
	rangeX = xsize*pixel_size_x
	rangeY = ysize*pixel_size_y

	i = 0
	while data_x_off > i*rangeX:
	  i += 1
	first_tile_xoff = (i-1)*rangeX

	i = 0
	while data_y_off > i*rangeY:
	  i += 1
	first_tile_yoff = i*rangeY

	i = 0
	while data_x_end > i*rangeX:
	  i += 1
	last_tile_xoff = (i-1)*rangeX

	i = 0
	while data_y_end > i*rangeY:
	  i += 1
	last_tile_yoff = i*rangeY

	num_tiles_row = int(round((first_tile_yoff - last_tile_yoff)/rangeY+1))
	num_tiles_column = int(round((last_tile_xoff - first_tile_xoff)/rangeX+1))
	
	for i in range(num_tiles_row):
	  for j in range(num_tiles_column):
	    tile_xoff = first_tile_xoff+(j*rangeX)-(offset/2)*pixel_size_x
	    tile_yoff = first_tile_yoff-(i*rangeY)+(offset/2)*pixel_size_y
	    tile_xend = first_tile_xoff+(j+1)*rangeX+(offset/2)*pixel_size_x
	    tile_yend = first_tile_yoff-(i+1)*rangeY-(offset/2)*pixel_size_y

	    if os.path.exists(outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'):
	      tileDir = outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'
	    else:
	      os.makedirs(outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/')
	      tileDir = outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'

	    if extension == 'no_extension':
	      outputFilePath = tileDir + inputFileName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff))
	    else:
	      outputFilePath = tileDir + inputFileName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + extension
	    os.system('gdal_merge.py -o ' + outputFilePath + ' -of GTiff -ul_lr ' + str(tile_xoff) + ' ' + str(tile_yoff) + ' ' + str(tile_xend) + ' ' + str(tile_yend) + ' -q ' + inputFilePath)
	print 'Tiling process for product ' + inputProduct + ' complete.\n'

    elif extension == 'dir':

      listInDir = glob.glob(inputFilePath + "/*")
      first_time = 1
      for b in range(len(listInDir)):
	inputBandName, extension = os.path.splitext(os.path.basename(listInDir[b]))
	if (extension.lower() == '.tif') or (extension.lower() == '.tiff'):

	  inputFile = gdal.Open(listInDir[b])
	  width = inputFile.RasterXSize
	  height = inputFile.RasterYSize
	  transform = inputFile.GetGeoTransform()
	  pixel_size_x = transform[1]
	  pixel_size_y = transform[5]*(-1)
	  data_x_off = transform[0]
	  data_y_off = transform[3]
	  data_x_end = transform[0] + width*transform[1] + height*transform[2]
	  data_y_end = transform[3] + width*transform[4] + height*transform[5] 

	  if (ulx != 0) or (uly != 0) or (lrx != 0) or (lry != 0):
	    if (lrx < data_x_off) or (ulx > data_x_end) or (uly < data_y_end) or (lry > data_y_off):
	      if first_time == 1:
		print '\n' + inputProduct + ' does not intersect the working window area.'
		left_product = 1
		first_time = 0
	    else:
	      if ulx > data_x_off:
		data_x_off = ulx
	      if lrx < data_x_end:
		data_x_end = lrx
	      if uly < data_y_off:
		data_y_off = uly
	      if lry > data_y_end:
		data_y_end = lry

	  if left_product == 0 and first_time == 1:
	    print '\nTiling ' + inputProduct + '...'
	    first_time = 0

	  if left_product == 0:
	    
	    rangeX = xsize*pixel_size_x
	    rangeY = ysize*pixel_size_y

	    i = 0
	    while data_x_off > i*rangeX:
	      i += 1
	    first_tile_xoff = (i-1)*rangeX

	    i = 0
	    while data_y_off > i*rangeY:
	      i += 1
	    first_tile_yoff = i*rangeY

	    i = 0
	    while data_x_end > i*rangeX:
	      i += 1
	    last_tile_xoff = (i-1)*rangeX

	    i = 0
	    while data_y_end > i*rangeY:
	      i += 1
	    last_tile_yoff = i*rangeY

	    num_tiles_row = int(round((first_tile_yoff - last_tile_yoff)/rangeY+1))
	    num_tiles_column = int(round((last_tile_xoff - first_tile_xoff)/rangeX+1))

	    for i in range(num_tiles_row):
	      for j in range(num_tiles_column):
		tile_xoff = first_tile_xoff+(j*rangeX)-(offset/2)*pixel_size_x
		tile_yoff = first_tile_yoff-(i*rangeY)+(offset/2)*pixel_size_y
		tile_xend = first_tile_xoff+(j+1)*rangeX+(offset/2)*pixel_size_x
		tile_yend = first_tile_yoff-(i+1)*rangeY-(offset/2)*pixel_size_y

		if os.path.exists(outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'):
		  tileDir = outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'
		else:
		  os.makedirs(outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/')
		  tileDir = outputDir + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + '/'

		outputFilePath = tileDir + inputBandName + '_' + str(int(tile_xoff)) + '_' + str(int(tile_yoff)) + extension
		os.system('gdal_merge.py -o ' + outputFilePath + ' -of GTiff -ul_lr ' + str(tile_xoff) + ' ' + str(tile_yoff) + ' ' + str(tile_xend) + ' ' + str(tile_yend) + ' -q ' + listInDir[b])

      if left_product == 0:
	print 'Tiling process for product ' + inputProduct + ' complete.\n'

    else:

      print '\nError: Input product ' + inputProduct + ' got unknown format\n'

#!                                                                                                                                                                                
# The function get_new_off_coordinates is called inside tile_default_od function.
# This funtion calculates the new off coordinates for each case, considering the
# necessary offset pixels to do the tiles and to guarantee that all tiles have
# the same dimensions.
#                                                                                                                                                                                 
# @param[in] inputFilePath
#      The filepath of each input GeoTIFF
# @param[in] inputProduct
#      The name of the input product
# @param[in] xsize                                                                                                                                                            
#      Intended tile width
# @param[in] ysize                                                                                                                                                            
#      Intended tile height
# @param[in] offset
#      The number of the offset pixels that should be considered for each tile
# @param[in] ulx                                                                                                                                                            
#      Upper Left X coordinate of the working window
# @param[in] uly                                                                                                                                            
#      Upper Left Y coordinate of the working window
# @param[in] lrx                                                                                                                                            
#      Lower Right X coordinate of the working window
# @param[in] lry                                                                                                                                           
#      Lower Right Y coordinate of the working window
# @param[in] first_time                                                                                                                                                              
#      Variable to avoid some repeated operations in case of products with a
#      GeoTIFF file per band
#
# @return
#      The funtion returns a vector containing the number of tiles per row (num_tiles_row),
#      the number of tiles per column (num_tiles_column), the new off coordinates (xoff_geo
#      and yoff_geo), the pixel dimensions (pixel_size_x and pixel_size_y) and a variable
#      which indicates if product's area does not intersect the working window (left_product)
#!         

def get_new_off_coordinates(inputFilePath, inputProduct, xsize, ysize, offset, ulx, uly, lrx, lry, first_time):

  left_product = 0
  inputFile = gdal.Open(inputFilePath)    
  width = inputFile.RasterXSize
  height = inputFile.RasterYSize

  if (ulx == 0) and (uly == 0) and (lrx == 0) and (lry == 0):
    num_tiles_row = height/ysize + 1
    num_tiles_column = width/xsize + 1

    new_width = (num_tiles_column*xsize)+offset+1
    new_height = (num_tiles_row*ysize)+offset+1

    borderx = (new_width-width)/2
    bordery = (new_height-height)/2

    transform = inputFile.GetGeoTransform()
    x_geo_in = transform[0] + borderx*transform[1] + bordery*transform[2]
    y_geo_in = transform[3] + borderx*transform[4] + bordery*transform[5]

    xoff_geo = transform[0]-(x_geo_in-transform[0])
    yoff_geo = transform[3]+(transform[3]-y_geo_in)
    
    pixel_size_x = transform[1]
    pixel_size_y = transform[5]
  else:
    transform = inputFile.GetGeoTransform()
    DataXOrigin = transform[0]
    DataYOrigin = transform[3]
    DataXEnd = transform[0] + width*transform[1] + height*transform[2]
    DataYEnd = transform[3] + width*transform[4] + height*transform[5] 

    if (lrx < DataXOrigin) or (ulx > DataXEnd) or (uly < DataYEnd) or (lry > DataYOrigin):
      if first_time == 1:
	print '\nError: No intersection with source product boundary ' + inputProduct
	left_product = 1
      else:
	left_product = 1
    else:
      if ulx < DataXOrigin:
	ulx = DataXOrigin
      if lrx > DataXEnd:
	lrx = DataXEnd
      if uly > DataYOrigin:
	uly = DataYOrigin
      if lry < DataYEnd:
	lry = DataYEnd

    pixel_size_x = transform[1]
    pixel_size_y = transform[5]

    window_width = int((lrx - ulx)/pixel_size_x + .5)
    window_height = int(-(uly - lry)/pixel_size_y + .5)

    num_tiles_row = window_height/ysize + 1
    num_tiles_column = window_width/xsize + 1
    new_window_width = (num_tiles_column*xsize)+offset+1
    new_window_height = (num_tiles_row*ysize)+offset+1

    borderx = (new_window_width-window_width)/2
    bordery = (new_window_height-window_height)/2

    x_geo_in = ulx + borderx*transform[1] + bordery*transform[2]
    y_geo_in = uly + borderx*transform[4] + bordery*transform[5]

    xoff_geo = ulx-(x_geo_in-ulx)
    yoff_geo = uly+(uly-y_geo_in)

  return [num_tiles_row, num_tiles_column, xoff_geo, yoff_geo, pixel_size_x, pixel_size_y, left_product]

#!                                                                                                                                                                                
# The function print_help prints the help message when the flag -h
# or --help is activated.
#
# @return
#      There are no returns for this function
#!

def print_help():

  help_message = """
  Usage: sensyf-tile -s <tile_size or tile_width tile_height> [-op offset_pixels] [-ullr ulx uly lrx lry / ullon ullat lrlon lrlat]
	 [-ot] [-od] [-h/--help] [-v/--version] src_dir dst_dir

  Options:

	 -s <tile_size>: intended tile size (in pixels) for the output tiles or <tile_width tile_height>: intended tile width and height (in pixels) for the output tiles

	 -op <offset_pixels>: intended offset (in pixels) for the output tiles

	 -ullr <ulx uly lrx lry> or <ullon ullat lrlon lrlat>: Select a working window. If not specified all the input file will be tiled
	       <ulx uly lrx lry> geocoordinates in meters (e.g. for Landsat data)
	       <ullon ullat lrlon lrlat> geocoordinates in decimal degrees for SENTINEL-1 data (sensyf-tile >= 1.2.0)

	 -ot: organize the outputs by tile instead of by product (not available for SENTINEL-1 data)

	 -od: place the output tiles on the output directory without any organization

	 -h/--help: print this help message

	 -v/--version: print the version of the tool

	 <src_dir>: input data directory

	 <dst_dir>: output directory

  """
  sys.exit(help_message)

#!                                                                                                                                                                                
# The function print_version prints the version of the sensyf-tile
# when the flag -v or --version is activated.
#
# @return
#      There are no returns for this function
#!

def print_version():

  version = '\nCopyright (C) DEIMOS Engenharia S.A.\n\nVersion: sensyf-tile 1.2.0\n'
  sys.exit(version)

#!                                                                                                                                                                                
# The function main checks the validity of the command given by the user in the
# command line.
#                                                                                                                                                                                 
# @param[in] args
#      Vector containing the command line arguments 
# 
# @return
#      There are no returns for this function
#!         

def main(args):

  wrong_use_message = "\nsensyf-tile: try 'sensyf-tile -h' or 'sensyf-tile --help' for more information\n"
  i = 1
  s = 0
  resolution = 0
  xsize = 0
  ysize = 0
  op = 0
  offset = 0
  od = 0
  ot = 0
  ulx = 0
  uly = 0
  lrx = 0
  lry = 0
  h = 0
  v = 0
  directories = []

  while i < len(args):
    if args[i] == '-s':
      s += 1
      i += 1
      try:
	xsize = int(args[i])
	if xsize <= 0:
	  sys.exit("\nError: Tile size values must be greater than zero.\n")
      except ValueError:
	sys.exit("\nError: Tile size values must be integers.\n")
      except IndexError:
	sys.exit(wrong_use_message)
      i += 1
      try:
	ysize = int(args[i])
	i += 1
	if ysize <= 0:
	  sys.exit("\nError: Tile size values must be greater than zero.\n")
      except ValueError:
	ysize = xsize
	if args[i] == '-op':
	  op += 1
	  try:
	    offset = int(args[i+1])
	    if offset <= 0:
	      sys.exit("\nError: Offset value must be greater than zero.\n")
	  except ValueError:
	    sys.exit("\nError: Offset value must be an integer.\n")
	  except IndexError:
	    sys.exit(wrong_use_message)
	  i += 1
	elif args[i] == '-ot':
	  ot = 1
	elif args[i] == '-od':
	  od = 1
	elif args[i] == '-ullr':
	  try:
	    ulx = float(args[i+1])
	    uly = float(args[i+2])
	    lrx = float(args[i+3])
	    lry = float(args[i+4])
	    i += 4
	  except ValueError:
	    sys.exit(wrong_use_message)
	  except IndexError:
	    sys.exit(wrong_use_message)
	elif args[i] == '-h' or args[i] == '--help':
	  h = 1
	elif args[i] == '-v' or args[i] == '--version':
	  v = 1
	elif os.path.exists(args[i]):
	  directories.append(args[i])
	else:
	  sys.exit(wrong_use_message)
	i += 1
      except IndexError:
	sys.exit(wrong_use_message)
    elif args[i] == '-op':
      op += 1
      i += 1
      try:
	offset = int(args[i])
	if offset <= 0:
	  sys.exit("\nError: Offset value must be greater than zero.\n")
      except ValueError:
	sys.exit("\nError: Offset value must be an integer.\n")
      except IndexError:
	sys.exit(wrong_use_message)
      i += 1
    elif args[i] == '-ot':
      ot = 1
      i += 1
    elif args[i] == '-od':
      od = 1
      i += 1
    elif args[i] == '-ullr':
      try:
	ulx = float(args[i+1])
	uly = float(args[i+2])
	lrx = float(args[i+3])
	lry = float(args[i+4])
	i += 5
      except ValueError:
	sys.exit(wrong_use_message)
      except IndexError:
	    sys.exit(wrong_use_message)
    elif args[i] == '-h' or args[i] == '--help':
      h = 1
      i += 1
    elif args[i] == '-v' or args[i] == '--version':
      v = 1
      i += 1
    elif os.path.exists(args[i]):
      directories.append(args[i])
      i += 1
    else:
      if len(directories) == 0 and ((args[i][0] == '.' and args[i][1] == '/') or args[i][0] == '/'):
	sys.exit("\nError: The input directory does not exist.\n")
      elif len(directories) == 1 and ((args[i][0] == '.' and args[i][1] == '/') or args[i][0] == '/'):
	sys.exit("\nError: The output directory does not exist.\n")
      else:
	sys.exit(wrong_use_message)

  if len(args) < 5 and len(args) != 2:
    sys.exit(wrong_use_message)
  elif len(args) == 2:
    if h == 1:
      print_help()
    elif v == 1:
      print_version()
    else:
      sys.exit(wrong_use_message)
  else:
    if len(directories) != 2:
      sys.exit(wrong_use_message)
    elif s != 1:
      sys.exit(wrong_use_message)
    elif v == 1:
      sys.exit(wrong_use_message)
    elif h == 1:
      sys.exit(wrong_use_message)
    elif ot == 1 and od == 1:
      sys.exit(wrong_use_message)
    elif ot == 0 and od == 0:
      fileList = glob.glob(directories[0] + "/*")
      if len(fileList) == 0:
	sys.exit("\nError: Input directory is empty.\n")
      else:
	dstDir = directories[1]
	tile_default_od(xsize, ysize, offset, ulx, uly, lrx, lry, fileList, dstDir, od)
    elif ot == 1 and od == 0:
      fileList = glob.glob(directories[0] + "/*")
      if len(fileList) == 0:
	sys.exit("\nError: Input directory is empty.\n")
      else:
	dstDir = directories[1]
	tile_organized_by_tile(xsize, ysize, offset, ulx, uly, lrx, lry, fileList, dstDir)
    elif ot == 0 and od == 1:
      fileList = glob.glob(directories[0] + "/*")
      if len(fileList) == 0:
	sys.exit("\nError: Input directory is empty.\n")
      else:
	dstDir = directories[1]
	tile_default_od(xsize, ysize, offset, ulx, uly, lrx, lry, fileList, dstDir, od)

  print '\n\nTile process completed.\n'

if __name__ == '__main__':

  main(sys.argv)
