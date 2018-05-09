#!/usr/bin/python2
from osgeo import ogr
import zipfile
import sys
import os

from coresyftools.tool import CoReSyFTool
from sridentify import Sridentify


def read_zip_shapefile(filepath, temp_path="temp_input"):
    '''
    It opens a zip file containing a shapefile and returns an handle to the
    OGRDataSource (a GDAL OGR object with the shapefile data).
    '''
    zip_file = zipfile.ZipFile(filepath, 'r')
    if not zip_file.infolist():
        sys.exit("Input Zip file with shapefile '%s' is empty!" % filepath)
    # Extract zip contents
    zip_file.extractall(temp_path)
    zip_file.close()
    # Get main file of the shapefile
    input_list = [os.path.join(temp_path, x) for x in os.listdir(temp_path)
                  if x.endswith(".shp")]
    if not input_list:
        sys.exit("Shapefile not found in '%s'!" % filepath)
    shapefile_shp = input_list[0]
    try:
        driver = ogr.GetDriverByName('ESRI Shapefile')
        data_source = driver.Open(shapefile_shp, 0)  # 0 means read-only.
        if not data_source:
            raise IOError()
    except IOError:
        sys.exit("Error. Unable to open shapefile '%s'!" % filepath)
    except Exception:
        sys.exit("Unexpected error when opening shapefile '%s'!" % filepath)
    return data_source


def get_shapefile_polygon_extent(data_source):
    """
    Retrieves the extent of the grid represented as OGR:Polygon.

    :param obj data_source: a shapefile represented as a OGR:DataSource object.
    """
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
        # read_zip_shapefile(shapefile_zip_path)
        # get_shapefile_crs(ogr_datasource) - retrieves the ESPG code of the shapefile CRS.
        # get_shapefile_polygon_extent(ogr_datasource) - retrieves the extent of the grid represented as OGR:Polygon.
        # crop_raster(raster_path, output_path, extent_polygon, output_crs) - applies the crop to the input image by executing gdal_warp in command line.
