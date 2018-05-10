#!/usr/bin/python2
from osgeo import ogr
import zipfile
import sys
import os
import subprocess

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


def get_shapefile_crs(data_source):
    '''
    Retrieves the ESPG Code of the shapefile CRS (Coordinate Reference System).

    data_source: must be the result of GDAL Open applied to the respective OGR
    driver.
    '''
    try:
        in_layer = data_source.GetLayer()
        spatial_ref = in_layer.GetSpatialRef()
        ident = Sridentify(prj=spatial_ref.ExportToWkt())
        epsg_code = int(ident.get_epsg())
    except Exception as epsg_exception:
        print(epsg_exception)
        sys.exit("Error. Unable to get ESPG code of grid shapefile.")
    return epsg_code


def crop_raster(input_raster, output_raster_file, polygon_extent, dest_crs):
    '''
    Crops the image specified by input_raster using the limits defined in
    polygon_extent (buffer already applied).

    input_raster: path to the image to be cropped.
    output_raster_file: the output file path.
    polygon_extent: POLYGON object to be used for the crop limits.
    dest_crs: the CRS of the output raster.
    '''
    bounds = polygon_extent.GetEnvelope()
    command_opts = str(bounds[0]) + ' ' + str(bounds[2]) + ' ' \
        + str(bounds[1]) + ' ' + str(bounds[3])
    gdal_command = 'gdalwarp' + ' -t_srs EPSG:' + str(dest_crs) + ' -te ' \
                   + str(command_opts) + ' ' + input_raster \
                   + ' ' + output_raster_file
    try:
        process = subprocess.Popen(gdal_command,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        if process.returncode:
            raise Exception (stderr.decode())
        else:
            print(stdout.decode())
            print(stderr.decode())
    except Exception as crop_exception:
        print("ERROR: " + str(crop_exception))
        sys.exit(process.returncode)


class CoresyfImageCrop(CoReSyFTool):

    def run(self, bindings):
        pass
        # read_zip_shapefile(shapefile_zip_path)
        # get_shapefile_crs(ogr_datasource) - retrieves the ESPG code of the shapefile CRS.
        # get_shapefile_polygon_extent(ogr_datasource) - retrieves the extent of the grid represented as OGR:Polygon.
        # crop_raster(raster_path, output_path, extent_polygon, output_crs) - applies the crop to the input image by executing gdal_warp in command line.
