#!/usr/bin/python2
import os
from osgeo import ogr, osr
from coresyftools.gpt_tool import GPTCoReSyFTool


DEGREE_CRS_CODE = 4326
METRE_CRS_CODE = 3857


class ShapefileNotFound(Exception):
    """Exception thrown when a shapefile cannot be found."""
    def __init__(self, dir_path):
        super(ShapefileNotFound, self).__init__(
                            "Shapefile not found in '{}'!".format(dir_path))


def read_shapefile(dir_path):
    '''
    It opens a folder with a shapefile and returns an handle to the
    OGRDataSource (a GDAL OGR object with the shapefile data).

    :param str dir_path: path of folder containing a shapefile.
    '''
    # Get main file of the shapefile
    input_list = [os.path.join(dir_path, x) for x in os.listdir(dir_path)
                  if x.endswith(".shp")]
    if not input_list:
        raise ShapefileNotFound(dir_path)
    shapefile_shp = input_list[0]

    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.Open(shapefile_shp, 0)  # 0 means read-only.
    if not data_source:
        raise IOError("Error. Unable to open shapefile at '%s'!" % dir_path)
    return data_source


def get_shapefile_polygon_extent(data_source):
    """
    Retrieves the extent of the shapefile represented as OGR:Polygon.

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


def apply_buffer_to_polygon(polygon, buffer, crs_buffer):
    '''
    Applies a specific buffer to a polygon geometry. It checks if polygon and
    buffer have the same Spatial reference, converts the buffer (if required)
    and apply it to the polygon geometry.
    :param obj polygon: OGR geometry with polygon extent.
    :param int buffer: buffer in buffer CRS units
    :param int crs_buffer: EPSG code of the buffer CRS.
    '''
    polygon_copy = polygon.Clone()
    sr_polygon = polygon_copy.GetSpatialReference()
    sr_buffer = osr.SpatialReference()
    sr_buffer.ImportFromEPSG(crs_buffer)

    if sr_buffer.IsSame(sr_polygon):
        polygon_with_buffer = polygon_copy.Buffer(buffer, 0)
    else:
        polygon_copy.TransformTo(sr_buffer)
        polygon_with_buffer = polygon_copy.Buffer(buffer, 0)
        polygon_with_buffer.TransformTo(sr_polygon)
    return polygon_with_buffer


class CoresyfPreProcessing(GPTCoReSyFTool):
    def run(self, bindings):
        grid_path = bindings['Sgrid']
        pbuffer = bindings['Pbuffer']

        grid_datasource = read_shapefile(grid_path)
        polygon_extent = get_shapefile_polygon_extent(grid_datasource)
        sr_geo_coordinates = osr.SpatialReference()
        sr_geo_coordinates.ImportFromEPSG(DEGREE_CRS_CODE)
        polygon_extent.TransformTo(sr_geo_coordinates)

        polygon_with_buffer = apply_buffer_to_polygon(polygon_extent, pbuffer,
                                                      METRE_CRS_CODE)

        envelope = polygon_with_buffer.GetEnvelope()
        # 'POLYGON ((xmin ymin, xmin ymax, xmax ymax, xmax ymin, xmin ymin))'
        bounds = "POLYGON (({} {}, {} {}, {} {}, {} {}, {} {}))".format(
                                    str(envelope[0]), str(envelope[2]),
                                    str(envelope[0]), str(envelope[3]),
                                    str(envelope[1]), str(envelope[3]),
                                    str(envelope[1]), str(envelope[2]),
                                    str(envelope[0]), str(envelope[2]))

        bindings['PgeoRegion'] = bounds
        del bindings['Sgrid']

        super(CoresyfPreProcessing, self).run(bindings)
