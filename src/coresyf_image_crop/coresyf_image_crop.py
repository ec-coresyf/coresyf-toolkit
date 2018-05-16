#!/usr/bin/python2
import sys
import os
from osgeo import ogr, osr
from coresyftools.tool import CoReSyFTool
from sridentify import Sridentify


def read_shapefile(folder_path):
    '''
    It opens a folder with a shapefile and returns an handle to the
    OGRDataSource (a GDAL OGR object with the shapefile data).
    '''
    # Get main file of the shapefile
    input_list = [os.path.join(folder_path, x) for x in os.listdir(folder_path)
                  if x.endswith(".shp")]
    if not input_list:
        sys.exit("Shapefile not found in '%s'!" % folder_path)
    shapefile_shp = input_list[0]
    try:
        driver = ogr.GetDriverByName('ESRI Shapefile')
        data_source = driver.Open(shapefile_shp, 0)  # 0 means read-only.
        if not data_source:
            raise IOError()
    except IOError:
        sys.exit("Error. Unable to open shapefile '%s'!" % folder_path)
    except Exception:
        sys.exit("Unexpected error when opening shapefile '%s'!" % folder_path)
    return data_source


def get_shapefile_polygon_extent(data_source):
    """
    Retrieves the extent of the grid represented as OGR:Polygon.

    :param obj data_source: a shapefile represented as a OGR:DataSource object.
    """
    layer = data_source.GetLayer()
    extent = layer.GetExtent()
    polygon_spatial_ref = layer.GetSpatialRef()

    # Create a Polygon from the extent tuple
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(extent[0], extent[2])
    ring.AddPoint(extent[1], extent[2])
    ring.AddPoint(extent[1], extent[3])
    ring.AddPoint(extent[0], extent[3])
    ring.AddPoint(extent[0], extent[2])
    ogr_polygon = ogr.Geometry(ogr.wkbPolygon)
    ogr_polygon.AddGeometry(ring)
    ogr_polygon.AssignSpatialReference(polygon_spatial_ref)
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
        epsg_code = ident.get_epsg()
    except Exception as epsg_exception:
        print(epsg_exception)
        sys.exit("Error. Unable to get ESPG code of grid shapefile.")
    return epsg_code


def get_raster_crs(data_source):
    '''
    Retrieves the ESPG Code of the raster CRS (Coordinate Reference System).

    data_source: must be the result of GDAL Open applied to the respective GDAL
    driver.
    '''
    try:
        projection = data_source.GetProjectionRef()
        ident = Sridentify(prj=projection)
        epsg_code = ident.get_epsg()
    except Exception as epsg_exception:
        print(epsg_exception)
        sys.exit("Error. Unable to get ESPG code of raster.")
    return epsg_code


def apply_buffer_to_polygon(polygon_extent, buffer, crs_polygon, crs_buffer):
    '''
    Applies a specific buffer to a polygon geometry.
    polygon_extent: OGR geometry with polygon extent.
    buffer: buffer in buffer CRS units
    crs_polygon: EPSG code of the polygon CRS.
    crs_buffer: EPSG code of the buffer CRS.
    '''
    # Make copy of object to preserve original 'polygon_extent'
    polygon = polygon_extent.Clone()

    if crs_buffer != crs_polygon:
        sr_buffer = osr.SpatialReference()
        sr_buffer.ImportFromEPSG(crs_buffer)
        sr_polygon = osr.SpatialReference()
        sr_polygon.ImportFromEPSG(crs_polygon)

        polygon.TransformTo(sr_buffer)
        polygon_with_buffer = polygon.Buffer(buffer, 0)
        polygon_with_buffer.TransformTo(sr_polygon)
    else:
        polygon_with_buffer = polygon.Buffer(buffer, 0)

    return polygon_with_buffer


class CoresyfImageCrop(CoReSyFTool):

    def crop_raster(self, polygon_extent, output_crs):
        '''
        Crops the image specified by input_raster using the limits defined in
        polygon_extent.

        input_path: path to the image to be cropped.
        output_raster_file: the output file path.
        polygon_extent: POLYGON object to be used for the crop limits.
        dest_crs: the CRS of the output raster.
        '''
        envelope = polygon_extent.GetEnvelope()
        bounds = "{} {} {} {}".format(str(envelope[0]), str(envelope[2]),
                                      str(envelope[1]), str(envelope[3]))

        command_template = "gdalwarp -t_srs EPSG:{} -te {}".format(
            str(output_crs), bounds)
        command_template += ' {Ssource} {Ttarget}'
        self.invoke_shell_command(command_template, **self.bindings)

    def run(self, bindings):
        data_source = read_shapefile(bindings['Sgrid'])
        output_crs = get_shapefile_crs(data_source)
        polygon_extent = get_shapefile_polygon_extent(data_source)
        self.crop_raster(polygon_extent, output_crs)
