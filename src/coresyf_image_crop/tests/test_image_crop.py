from unittest import TestCase
from osgeo import ogr, osr, gdal
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
            get_datasource_epsg, read_shapefile, apply_buffer_to_polygon, \
            get_raster_resolution


def create_polygon_geometry_4326():
    polygon = ogr.CreateGeometryFromWkt("POLYGON ((0.0 0.0 0," +
                                        "0.01808333 0.0 0," +
                                        "0.01808333 0.03616667 0," +
                                        "0.0 0.03616667 0," +
                                        "0.0 0.0 0))")
    sr_polygon = osr.SpatialReference()
    sr_polygon.ImportFromEPSG(4326)
    polygon.AssignSpatialReference(sr_polygon)
    return polygon


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_shapefile('test_data/grid_EPSG_3763')
        self.test_image = 'test_data/Aveiro_resampled.tif'
        self.image_datasource = gdal.Open(self.test_image)
        self.buffer_4326_units = 0.01808333
        self.buffer_3763_units = 2000
        self.expected_envelope_1 = (-0.017784821097606172, 0.03586646107971625,
                                    -0.01790423549555848, 0.054070905482337325)
        self.expected_envelope_2 = (-0.01808333, 0.03616666,
                                    -0.01808333, 0.05425)
        self.polygon_geo_in_4326 = create_polygon_geometry_4326()

    def tearDown(self):
        pass

    def test_get_shapefile_polygon_extent(self):
        polygon_extent_wkt = "POLYGON ((" + \
            "-61575.57812574980926 103754.81329901740537 0," \
            "-54172.937265817548905 103754.81329901740537 0," \
            "-54172.937265817548905 107225.478697661776096 0," \
            "-61575.57812574980926 107225.478697661776096 0,"\
            "-61575.57812574980926 103754.81329901740537 0))"

        extent_polygon = get_shapefile_polygon_extent(self.data_source)

        self.assertTrue(extent_polygon.IsValid())
        self.assertEqual(extent_polygon.ExportToWkt(), polygon_extent_wkt)

    def test_get_datasource_epsg(self):
        epsg_code = get_datasource_epsg(self.data_source)
        self.assertEqual(epsg_code, 3763)

    def test_apply_buffer_to_polygon_1(self):
        '''
        Applies a buffer of 2000 meters (in EPSG:3763), aproximately 0.01808333
        degrees in EPSG:4326, to a polygon in EPSG:4326 (units: degreee).
        In this case, the polygon is transformed to buffer Spatial Reference
        and back to the original one after applying the buffer.
        '''
        polygon_with_buffer = apply_buffer_to_polygon(self.polygon_geo_in_4326,
                                                      self.buffer_3763_units,
                                                      3763)

        self.assertEqual(polygon_with_buffer.GetEnvelope(),
                         self.expected_envelope_1)

    def test_apply_buffer_to_polygon_2(self):
        '''
        Applies a buffer of 0.01808333 degrees (in EPSG:4326) to a polygon in
        the same Spatial Reference system.
        In this case, no conversions between SRS are required.
        '''
        polygon_with_buffer = apply_buffer_to_polygon(self.polygon_geo_in_4326,
                                                      self.buffer_4326_units,
                                                      4326)

        self.assertEqual(polygon_with_buffer.GetEnvelope(),
                         self.expected_envelope_2)

    def test_get_raster_resolution(self):
        resolution = get_raster_resolution(self.image_datasource)
        self.assertEqual(resolution, 180)
        
    def test_get_raster_epsg(self):
        epsg_code = get_datasource_epsg(self.image_datasource)
        self.assertEqual(epsg_code, 3763)