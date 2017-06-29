#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
===============================================================================
Co-ReSyF Research Application - SAR_Bathymetry
===============================================================================
 Authors: 
 Date: June/2017
 Last update: June/2017
 
 Usage: ./CreateOutputGrid.py
 
 
 For help: ./CreateOutputGrid -h
===============================================================================
"""


import numpy as np
from osgeo import ogr
from pyproj import Proj, transform


# Set the spacing - defines how far the points are in map units (meters)
spacing = 500
# Set the inset - determine how close to the edge of the layer the points start, in map units (meters)
inset = 5
# Set CRS
crs_meters = '3763'
crs_degrees = '4326'

lon_vector_path = '/home/rccc/Downloads/lon_vector.txt'
lat_vector_path = '/home/rccc/Downloads/lat_vector.txt'

myfile = '/home/rccc/Downloads/Camada.kml'
driver = ogr.GetDriverByName('KML')
datasource = driver.Open(myfile)
layer = datasource.GetLayer()


######## CONVERTION COORDINATES BETWEEN CRS #############
def degrees2meters(lon, lat, inset=0):
    proj_in = Proj(init='epsg:'+crs_degrees)
    proj_out = Proj(init='epsg:'+crs_meters)
    x_meter, y_meter = transform(proj_in, proj_out, lon, lat)
    x_meter += inset
    y_meter += inset
    return x_meter, y_meter

def meters2degrees(x, y):
    proj_in = Proj(init='epsg:'+crs_meters)
    proj_out = Proj(init='epsg:'+crs_degrees)
    lon, lat = transform(proj_in, proj_out, x, y)
    return lon, lat


# Get the extent from the loaded layer
minLon, maxLon, minLat, maxLat = layer.GetExtent()
print "Layer extent is:"
print minLon, maxLon, minLat, maxLat

# Set the extent of the new layer (meters)
xmin, ymin = degrees2meters(minLon, minLat, inset)
xmax, ymax = degrees2meters(maxLon, maxLat, inset)

# Create the coordinates (in meters) of the points in the grid
#coords = [(x,y) for x in (i for i in numpy.arange(xmin, xmax, spacing)) for y in (j for j in numpy.arange(ymin, ymax, spacing))]

# Create vectors with unique lon and lat values (in degrees) 
lon_vector = [meters2degrees(x, ymax)[0] for x in (i for i in np.arange(xmin, xmax, spacing))]
lat_vector = [meters2degrees(xmax, y)[1] for y in (i for i in np.arange(ymin, ymax, spacing))]

print "lon is:"
print lon_vector
print "lat is:"
print lat_vector

# Saving lon and lat vectors into different files
lon_file = open(lon_vector_path, "w")
for value in lon_vector:
    lon_file.write("%f\n" % value)
lon_file.close()

lat_file = open(lat_vector_path, "w")
for value in lat_vector:
    lat_file.write("%f\n" % value)
lat_file.close()


############################################
# TODO: ADD THIS SECTION TO TILING
#############################################
#import matplotlib.mlab as mlab

#lon = np.loadtxt(lon_vector_path)
#lat = np.loadtxt(lat_vector_path)

#lon_mesh, lat_mesh = np.meshgrid(lon, lat)

#grid_values = mlab.griddata(lon_orig.ravel(), lat_orig.ravel(), image_values.ravel(), lon_mesh, lat_mesh, interp = 'nn') 




'''
###########################################################
### LOST CODE #############################################
###########################################################

############################################
########  CREATE A SHAPEFILE ###############
# Create a new vector point layer
points_layer = QgsVectorLayer('Point?crs=' + crs_degrees, 'grid', "memory")
prov = points_layer.dataProvider()

# Create the coordinates (in meters) of the points in the grid
coords = [(x,y) for x in (i for i in numpy.arange(xmin, xmax, spacing)) for y in (j for j in numpy.arange(ymin, ymax, spacing))]
 
# Add the coordinates (in degrees) in the new point layer
points = []
for x,y in coords:
    feat = QgsFeature()
    lon, lat = meters2degrees(x, y)
    point = QgsPoint(lon, lat)
    feat.setGeometry(QgsGeometry.fromPoint(point))
    points.append(feat)
prov.addFeatures(points)
points_layer.updateExtents()
'''