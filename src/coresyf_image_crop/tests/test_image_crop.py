from unittest import TestCase
from osgeo import ogr, osr
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_datasource_epsg, read_shapefile, apply_buffer_to_polygon

TEMP_PATH = "temp_path"


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_shapefile('test_data/grid_EPSG_3763')

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

    def test_apply_buffer_to_polygon(self):
        buffer_3763_units = 2000  # aprox. 0.01808333 degrees in EPSG:4326
        crs_buffer = 3763
        crs_polygon = 4326
        polygon_extent = ogr.CreateGeometryFromWkt(
                                                "POLYGON ((" +
                                                "0.0 0.0 0," +
                                                "0.01808333 0.0 0," +
                                                "0.01808333 0.03616667 0," +
                                                "0.0 0.03616667 0," +
                                                "0.0 0.0 0))")
        sr_polygon = osr.SpatialReference()
        sr_polygon.ImportFromEPSG(crs_polygon)
        polygon_extent.AssignSpatialReference(sr_polygon)
        expected_envelope = (-0.017784821097606172, 0.03586646107971625,
                             -0.01790423549555848, 0.054070905482337325)

        polygon_with_buffer = apply_buffer_to_polygon(polygon_extent,
                                                      buffer_3763_units,
                                                      crs_polygon,
                                                      crs_buffer)

        self.assertEqual(polygon_with_buffer.GetEnvelope(), expected_envelope)
