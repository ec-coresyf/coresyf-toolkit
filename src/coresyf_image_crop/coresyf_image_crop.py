#!/usr/bin/python2
from osgeo import ogr

from coresyftools.tool import CoReSyFTool
from sridentify import Sridentify


def get_shapefile_polygon_extent(shapefile_path):
    '''Retrieves the extent of the grid represented as OGR:Polygon.'''
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.Open(shapefile_path, 0)
    layer = data_source.GetLayer()
    extent = layer.GetExtent()

    # Create a Polygon from the extent tuple
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(extent[0], extent[2])
    ring.AddPoint(extent[1], extent[2])
    ring.AddPoint(extent[1], extent[3])
    ring.AddPoint(extent[0], extent[3])
    ring.AddPoint(extent[0], extent[2])
    ogr_polygon = ogr.Geometry(ogr.wkbPolygon)
    ogr_polygon.AddGeometry(ring)
    return ogr_polygon


class CoresyfImageCrop(CoReSyFTool):

    def run(self, bindings):
        pass
        # get_shapefile_crs(shapefile_path) - retrieves the ESPG code of the shapefile CRS.
        # get_shapefile_polygon_extent(shapefile_path) - retrieves the extent of the grid represented as OGR:Polygon.
        # crop_raster(raster_path, output_path, extent_polygon, output_crs) - applies the crop to the input image by executing gdal_warp in command line.
